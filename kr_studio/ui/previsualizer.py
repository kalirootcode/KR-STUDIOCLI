"""
previsualizer.py — Motor de reproducción VLC para Timeline Multipista
Módulo independiente: maneja toda la lógica de VLC, sincronización de audio,
playback, scrubbing, y visualización de clips en el previsualizador.

NO depende directamente de MainWindow; recibe callbacks y widgets por inyección.
"""
import time as time_module
import traceback


class Previsualizer:
    """
    Motor de reproducción VLC que sincroniza clips de video/imagen/audio
    con el TimelineEngine y muestra el resultado en un frame de Tkinter.

    Parámetros de constructor:
        tl_engine:    Instancia de TimelineEngine (acceso a clips y duración)
        video_frame:  tk.Frame donde se embebe el reproductor VLC (XID en Linux)
        root:         Widget CTk raíz para programar .after() callbacks
        callbacks:    Dict con funciones de callback de la UI:
            - on_timecode(text: str)  → Actualiza label de timecode
            - on_slider(value: float) → Actualiza slider 0-1000
            - on_play_state(playing: bool) → Actualiza botón Play/Pause
            - on_draw_timeline()      → Redibuja el timeline visual
            - on_chat(role, msg)      → Escribe mensaje en el chat del editor
    """

    def __init__(self, tl_engine, video_frame, root, callbacks: dict):
        self.tl_engine = tl_engine
        self.video_frame = video_frame
        self.root = root
        self.cb = callbacks

        # ── Estado interno VLC ──
        self._vlc_instance = None
        self._vlc_player = None
        self._vlc_audio_a1 = None
        self._vlc_audio_a2 = None
        self._vlc_current_video_path = None
        self._a1_current_path = None
        self._a2_current_path = None

        # ── Estado de reproducción ──
        self._playing = False
        self._playhead_pos = 0.0
        self._last_poll_time = None
        self._video_muted = False
        self._volume = 80

        # ── Placeholder (imagen de "sin medios") ──
        self._preview_placeholder = None

    # ══════════════════════════════════════════
    # PROPIEDADES PÚBLICAS
    # ══════════════════════════════════════════

    @property
    def playhead_pos(self) -> float:
        return self._playhead_pos

    @playhead_pos.setter
    def playhead_pos(self, value: float):
        self._playhead_pos = max(0.0, value)

    @property
    def is_playing(self) -> bool:
        return self._playing

    @property
    def current_video_path(self) -> str:
        return self._vlc_current_video_path

    # ══════════════════════════════════════════
    # INICIALIZACIÓN VLC
    # ══════════════════════════════════════════

    def _init_vlc(self) -> bool:
        """Inicializa la instancia VLC si no existe."""
        if self._vlc_instance is None:
            try:
                import vlc
                self._vlc_instance = vlc.Instance('--no-xlib', '--quiet')
                self._vlc_player = self._vlc_instance.media_player_new()
                return True
            except Exception as e:
                self._chat(f"⚠ Error inicializando VLC: {e}")
                return False
        return True

    def _embed_player(self):
        """Embebe el reproductor VLC en el frame de Tkinter usando el XID de X11."""
        if self._vlc_player is None:
            return
        self.video_frame.update_idletasks()
        wid = self.video_frame.winfo_id()
        if wid:
            self._vlc_player.set_xwindow(wid)

    def _chat(self, msg: str):
        """Envía un mensaje al chat del editor (si el callback existe)."""
        cb = self.cb.get("on_chat")
        if cb:
            cb("Editor", msg)

    # ══════════════════════════════════════════
    # CARGA DE MEDIOS
    # ══════════════════════════════════════════

    def load_video(self, path: str):
        """Carga un video/imagen en el reproductor VLC principal."""
        if not self._init_vlc():
            return
        try:
            media = self._vlc_instance.media_new(path)
            self._vlc_player.set_media(media)
            self._embed_player()
            self._vlc_player.audio_set_volume(self._volume)
            self._vlc_current_video_path = path
            # Borrar placeholder si existe
            if self._preview_placeholder:
                self._preview_placeholder.place_forget()
                self._preview_placeholder = None
        except Exception as e:
            self._chat(f"⚠ Error cargando video: {e}")

    # ══════════════════════════════════════════
    # ACTUALIZACIÓN DE UI
    # ══════════════════════════════════════════

    def _update_ui_from_playhead(self):
        """Actualiza el timecode y slider basándose en la posición del playhead."""
        pos = self._playhead_pos
        h = int(pos // 3600)
        m = int((pos % 3600) // 60)
        s = int(pos % 60)
        ms = int((pos % 1) * 1000)

        tc_cb = self.cb.get("on_timecode")
        if tc_cb:
            tc_cb(f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}")

        total_dur = max(self.tl_engine.total_duration, 1)
        sl_cb = self.cb.get("on_slider")
        if sl_cb:
            sl_cb(pos / total_dur * 1000)
            
        ph_cb = self.cb.get("on_playhead")
        if ph_cb:
            ph_cb(pos)

    def _notify_play_state(self):
        """Notifica a la UI si estamos Playing o Paused."""
        cb = self.cb.get("on_play_state")
        if cb:
            cb(self._playing)

    def _draw_timeline(self):
        """Solicita redibujado del timeline visual."""
        cb = self.cb.get("on_draw_timeline")
        if cb:
            cb()

    # ══════════════════════════════════════════
    # SHOW PREVIEW FRAME (seek VLC al clip correcto)
    # ══════════════════════════════════════════

    def show_frame_at(self, time_pos: float):
        """Mueve VLC al frame correcto según el clip de video dominante (V3->V2->V1)."""
        if self._vlc_player is None or not self._init_vlc():
            return
        try:
            import vlc
            result = self.tl_engine.get_top_video_clip_at(time_pos)
            if result:
                source_path, source_time, clip = result
                target_ms = int(source_time * 1000)
                is_img = source_path.lower().endswith(('.png', '.jpg', '.jpeg'))

                if self._vlc_current_video_path != source_path:
                    # Cambio de fuente → cargar nuevo medio
                    media = self._vlc_instance.media_new(source_path)
                    self._vlc_player.set_media(media)
                    self._embed_player()
                    self._vlc_current_video_path = source_path
                    self._vlc_player.play()
                    if not self._playing:
                        if not is_img:
                            self.root.after(50, lambda: self._vlc_player.set_time(max(0, target_ms)))
                        self.root.after(200, lambda: self._vlc_player.pause())
                    else:
                        if not is_img:
                            self.root.after(50, lambda: self._vlc_player.set_time(max(0, target_ms)))
                else:
                    # Mismo archivo, solo seek si es video
                    if not is_img:
                        self._vlc_player.set_time(max(0, target_ms))
            else:
                # Gap total — pausar VLC
                if self._vlc_player.get_state() == vlc.State.Playing:
                    self._vlc_player.pause()
        except Exception as e:
            traceback.print_exc()
            print(f"[Previsualizer] Error en show_frame_at: {e}")

    # ══════════════════════════════════════════
    # CONTROLES DE REPRODUCCIÓN
    # ══════════════════════════════════════════

    def play_pause(self):
        """Alterna reproducción timeline-driven."""
        if self._vlc_player is None and not self._init_vlc():
            return
        import vlc

        if self._playing:
            # ── PAUSAR ──
            self._playing = False
            self._vlc_player.pause()
            # Pausar audio players
            for player in [self._vlc_audio_a1, self._vlc_audio_a2]:
                if player:
                    try:
                        if player.get_state() == vlc.State.Playing:
                            player.pause()
                    except Exception:
                        pass
            self._notify_play_state()
        else:
            # ── PLAY ──
            self._playing = True
            self._notify_play_state()

            # Solo llamar play() si hay media cargada
            state = self._vlc_player.get_state()
            has_media = self._vlc_player.get_media() is not None

            if has_media and state in (vlc.State.NothingSpecial, vlc.State.Stopped, vlc.State.Ended):
                self._vlc_player.play()
                self._embed_player()
            elif state == vlc.State.Paused:
                self._vlc_player.pause()  # Resume (toggle)

            # Posicionar en el clip actual
            self.root.after(100, lambda: self.show_frame_at(self._playhead_pos))

            # Sincronizar audio
            self._sync_audio(self._playhead_pos, force_start=True)

            # Iniciar el loop de polling
            self._last_poll_time = None
            self._poll_position()

    def stop(self):
        """Detiene completamente la reproducción."""
        self._playing = False
        self._last_poll_time = None
        if self._vlc_player:
            self._vlc_player.stop()
        for player in [self._vlc_audio_a1, self._vlc_audio_a2]:
            if player:
                try:
                    player.stop()
                except Exception:
                    pass
        self._a1_current_path = None
        self._a2_current_path = None
        self._playhead_pos = 0.0
        self._notify_play_state()
        self._update_ui_from_playhead()
        self._draw_timeline()

    def goto_start(self):
        """Salta al inicio del timeline."""
        self._playhead_pos = 0.0
        self.show_frame_at(0.0)
        self._update_ui_from_playhead()
        self._draw_timeline()

    def goto_end(self):
        """Salta al final del timeline."""
        total = max(0, self.tl_engine.total_duration - 0.5)
        self._playhead_pos = total
        self.show_frame_at(total)
        self._update_ui_from_playhead()
        self._draw_timeline()

    # ══════════════════════════════════════════
    # SCRUBBING Y VOLUMEN
    # ══════════════════════════════════════════

    def scrub(self, slider_value: float):
        """Callback del slider de scrubbing (0-1000)."""
        total_dur = max(self.tl_engine.total_duration, 1)
        self._playhead_pos = (slider_value / 1000.0) * total_dur
        self._update_ui_from_playhead()
        self._draw_timeline()
        self.show_frame_at(self._playhead_pos)

    def set_volume(self, vol: int):
        """Ajusta el volumen global."""
        self._volume = vol
        if self._vlc_player and not self._video_muted:
            self._vlc_player.audio_set_volume(vol)
        if self._vlc_audio_a1:
            self._vlc_audio_a1.audio_set_volume(vol)
        if self._vlc_audio_a2:
            self._vlc_audio_a2.audio_set_volume(max(30, vol // 2))

    def toggle_video_mute(self) -> bool:
        """Silencia o reactiva el audio del video. Retorna el nuevo estado."""
        self._video_muted = not self._video_muted
        if self._vlc_player:
            if self._video_muted:
                self._vlc_player.audio_set_volume(0)
            else:
                self._vlc_player.audio_set_volume(self._volume)
        return self._video_muted

    # ══════════════════════════════════════════
    # LOOP PRINCIPAL DE POLLING (Timeline-driven)
    # ══════════════════════════════════════════

    def _poll_position(self):
        """Loop principal: avanza el playhead por el timeline y maneja gaps/splits."""
        if not self._playing or self._vlc_player is None:
            return

        import vlc

        now = time_module.time()
        if self._last_poll_time is None:
            dt = 0.0
        else:
            dt = now - self._last_poll_time
        self._last_poll_time = now

        # Avanzar playhead
        self._playhead_pos += dt

        # ¿Pasamos del final del timeline?
        if self._playhead_pos >= self.tl_engine.total_duration:
            self._playing = False
            self._vlc_player.pause()
            
            # Pausar las pistas de audio también (muy importante para clips recortados largos)
            for player in [self._vlc_audio_a1, self._vlc_audio_a2]:
                if player:
                    try:
                        if player.get_state() == vlc.State.Playing:
                            player.pause()
                    except Exception:
                        pass
                        
            self._playhead_pos = self.tl_engine.total_duration
            self._notify_play_state()
            self._update_ui_from_playhead()
            self._draw_timeline()
            return

        # ¿Hay clips de video bajo el playhead?
        result = self.tl_engine.get_top_video_clip_at(self._playhead_pos)
        if result:
            source_path, source_time, clip = result
            target_ms = int(source_time * 1000)
            is_img = source_path.lower().endswith(('.png', '.jpg', '.jpeg'))

            if self._vlc_current_video_path != source_path:
                # Switch dinámico de fuente
                media = self._vlc_instance.media_new(source_path)
                self._vlc_player.set_media(media)
                self._embed_player()
                self._vlc_current_video_path = source_path
                self._vlc_player.play()
                if not is_img:
                    self.root.after(50, lambda: self._vlc_player.set_time(max(0, target_ms)))
            else:
                # Asegurar que VLC esté playing
                state = self._vlc_player.get_state()
                if state != vlc.State.Playing and state != vlc.State.Opening:
                    if state == vlc.State.Ended and not is_img:
                        media = self._vlc_instance.media_new(source_path)
                        self._vlc_player.set_media(media)
                    self._vlc_player.play()
                    self._embed_player()

                # Sincronización continua solo para video
                if not is_img:
                    current_ms = self._vlc_player.get_time() or 0
                    if abs(current_ms - target_ms) > 300:
                        self._vlc_player.set_time(max(0, target_ms))
        else:
            # GAP total → pausar VLC y saltar al siguiente clip
            state = self._vlc_player.get_state()
            if state == vlc.State.Playing:
                self._vlc_player.pause()

            next_start = self.tl_engine.get_next_video_clip_start(self._playhead_pos)
            if next_start > 0:
                self._playhead_pos = next_start
                result2 = self.tl_engine.get_top_video_clip_at(next_start)
                if result2:
                    if self._vlc_current_video_path != result2[0]:
                        media = self._vlc_instance.media_new(result2[0])
                        self._vlc_player.set_media(media)
                        self._vlc_current_video_path = result2[0]
                    self._vlc_player.play()
                    self._embed_player()
                    is_img_next = result2[0].lower().endswith(('.png', '.jpg', '.jpeg'))
                    if not is_img_next:
                        self.root.after(50, lambda: self._vlc_player.set_time(int(result2[1] * 1000)))

        self._update_ui_from_playhead()
        self._draw_timeline()

        # Sincronizar pistas de audio A1/A2
        self._sync_audio(self._playhead_pos)

        self.root.after(50, self._poll_position)  # 20 FPS de polling

    # ══════════════════════════════════════════
    # SINCRONIZACIÓN DE AUDIO (A1 TTS, A2 Música)
    # ══════════════════════════════════════════

    def _get_or_create_audio_player(self, track: str):
        """Crea u obtiene un MediaPlayer para la pista de audio."""
        if not self._init_vlc():
            return None
        if track == "A1":
            if self._vlc_audio_a1 is None:
                self._vlc_audio_a1 = self._vlc_instance.media_player_new()
            return self._vlc_audio_a1
        elif track == "A2":
            if self._vlc_audio_a2 is None:
                self._vlc_audio_a2 = self._vlc_instance.media_player_new()
            return self._vlc_audio_a2
        return None

    def _sync_audio(self, timeline_pos: float, force_start: bool = False):
        """Sincroniza los reproductores A1/A2 con la posición del timeline."""
        import vlc

        for track_id, path_attr in [("A1", "_a1_current_path"), ("A2", "_a2_current_path")]:
            result = self.tl_engine.get_source_time_at(track_id, timeline_pos)
            player = self._get_or_create_audio_player(track_id)
            if not player:
                continue

            if result:
                source_path, source_time, clip = result
                if clip.muted:
                    if player.get_state() == vlc.State.Playing:
                        player.pause()
                    continue

                current_loaded = getattr(self, path_attr)

                if current_loaded != source_path or force_start:
                    media = self._vlc_instance.media_new(source_path)
                    player.set_media(media)
                    player.play()
                    setattr(self, path_attr, source_path)
                    a_vol = max(30, self._volume // 2) if track_id == "A2" else self._volume
                    player.audio_set_volume(a_vol)
                    self.root.after(80, lambda p=player, t=source_time: p.set_time(int(t * 1000)))
                else:
                    state = player.get_state()
                    if state != vlc.State.Playing:
                        player.play()
                    cur_ms = player.get_time() or 0
                    target_ms = int(source_time * 1000)
                    if abs(cur_ms - target_ms) > 500:
                        player.set_time(max(0, target_ms))
            else:
                if player.get_state() == vlc.State.Playing:
                    player.pause()
                setattr(self, path_attr, None)

    # ══════════════════════════════════════════
    # LIMPIEZA
    # ══════════════════════════════════════════

    def destroy(self):
        """Libera todos los recursos VLC."""
        self._playing = False
        for player in [self._vlc_player, self._vlc_audio_a1, self._vlc_audio_a2]:
            if player:
                try:
                    player.stop()
                    player.release()
                except Exception:
                    pass
        if self._vlc_instance:
            try:
                self._vlc_instance.release()
            except Exception:
                pass
        self._vlc_instance = None
        self._vlc_player = None
        self._vlc_audio_a1 = None
        self._vlc_audio_a2 = None
