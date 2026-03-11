"""
director.py — Módulo Director / Titiritero (Phase 3)
Orquesta la ejecución del video con DOBLE terminal + OBS:
  Terminal A → kr-clidn (dashboard, ya con venv activado)
  Terminal B → ejecución de comandos reales (limpios)
  OBS → cambia escenas automáticamente
  Widget flotante → pausa paso a paso + mini log
  NEW: Lee respuestas del terminal con xdotool + xclip
"""
import threading
import subprocess
import time
import os
import hashlib
from kr_studio.core.audio_engine import AudioEngine
from kr_studio.core.obs_controller import OBSController


class DirectorEngine:
    def __init__(self, main_app, json_data: list, workspace_dir: str):
        self.app = main_app
        self.json_data = json_data
        self.workspace_dir = workspace_dir
        self.audio_engine = AudioEngine()
        self.is_running = False

        # Dual terminal WIDs
        self.wid_a = None  # Terminal A (kr-clidn)
        self.wid_b = None  # Terminal B (ejecución)

        self.typing_delay = 80  # ms entre teclas
        self.obs = OBSController()
        self.floating_ctrl = None  # Widget flotante

        from kr_studio.core.x11_controller import X11Controller
        self.x11 = X11Controller()

        # Almacén de respuestas leídas del terminal
        self.last_terminal_read = ""

        # Timestamps para sincronización con video_engine
        self.timestamps = {}
        self._start_wall = 0.0
        self.on_timestamps_ready = None  # callback(timestamps_dict)

    def start(self):
        self.is_running = True
        threading.Thread(target=self._run_sequence, daemon=True).start()

    def stop(self):
        self.is_running = False

    # ─────────────────────────────────────────────
    # UTILIDADES X11
    # ─────────────────────────────────────────────

    def _find_all_konsole_wids(self) -> list:
        return self.x11.find_konsole_wids()

    def _resize_window(self, wid: str, width=450, height=800):
        self.x11.resize_window(wid, width, height)

    def _focus_window(self, wid: str):
        self.x11.focus_window(wid)

    def _type_text(self, wid: str, text: str, delay_ms: int = None):
        speed = getattr(self.app, 'typing_speed_pct', 80) if hasattr(self, 'app') else 80
        self.x11.type_text(wid, text, speed, delay_ms)

    def _send_key(self, wid: str, key: str):
        self.x11.send_key(wid, key)

    def _log(self, sender: str, message: str):
        try:
            self.app.after(0, self.app.append_chat, sender, message)
        except Exception:
            print(f"[{sender}] {message}")

    def _flog(self, message: str, tag: str = "info"):
        """Log al widget flotante."""
        if self.floating_ctrl:
            self.floating_ctrl.add_log(message, tag)

    # ─────────────────────────────────────────────
    # LEER TERMINAL (desde archivos de log)
    # ─────────────────────────────────────────────

    def _read_terminal(self, wid: str) -> str:
        """Lee el terminal desde archivo de log — NUNCA interrumpe kr-clidn."""
        from kr_studio.core.dynamic_director import LOG_TERMINAL_A, LOG_TERMINAL_B, read_log_file

        # Determinar qué log leer según el WID
        if wid == self.wid_a:
            return read_log_file(LOG_TERMINAL_A, 40)
        else:
            return read_log_file(LOG_TERMINAL_B, 30)

    # ─────────────────────────────────────────────
    # KR-CLIDN BOOT SEQUENCE (Terminal A)
    # Terminal ya tiene venv activado desde el startup
    # ─────────────────────────────────────────────

    def _boot_krcli_terminal_a(self):
        self._log("Director", "🚀 Verificando Terminal A...")
        self._flog("Verificando estado Terminal A...", "info")
        
        # Leer el log actual para ver si kr-clidn ya está activo
        from kr_studio.core.dynamic_director import read_log_file, LOG_TERMINAL_A
        current_log = read_log_file(LOG_TERMINAL_A, 20)
        
        # Si el dashboard ya está visible (detectar por texto del menú)
        keywords_dashboard = ["CONSOLA AI", "WEB H4CK3R", "HERRAMIENTAS", "DOMINION"]
        already_running = any(kw in current_log for kw in keywords_dashboard)
        
        if already_running:
            self._log("Director", "✅ KR-CLIDN ya está activo")
            self._flog("KR-CLIDN ya activo ✅", "ok")
            return
        
        # Si no está corriendo, hacer el boot completo
        self._focus_window(self.wid_a)
        self._type_text(self.wid_a, f"script -q -f {LOG_TERMINAL_A}", delay_ms=30)
        self._send_key(self.wid_a, "Return")
        time.sleep(0.8)
        self._type_text(self.wid_a, "clear", delay_ms=30)
        self._send_key(self.wid_a, "Return")
        time.sleep(0.3)
        self._type_text(self.wid_a, "source venv/bin/activate", delay_ms=30)
        self._send_key(self.wid_a, "Return")
        time.sleep(1.0)
        self._type_text(self.wid_a, "kr-clidn", delay_ms=80)
        self._send_key(self.wid_a, "Return")
        
        # Esperar hasta 15s a que aparezca el dashboard
        self._flog("Esperando dashboard (auto-detect)...", "wait")
        max_wait = 30  # 15s total (30 x 0.5s)
        for attempt in range(max_wait):
            if not self.is_running:
                return
            time.sleep(0.5)
            log_content = read_log_file(LOG_TERMINAL_A, 30)
            if any(kw in log_content for kw in keywords_dashboard):
                self._log("Director", "✅ KR-CLIDN Dashboard detectado automáticamente")
                self._flog("Dashboard detectado ✅", "ok")
                return
        
        # Si no se detectó, pedir confirmación manual
        self._log("Director", "⏸ No se detectó dashboard. Confirma manualmente.")
        if self.floating_ctrl:
            self.floating_ctrl.wait_for_continue("Confirma: ¿Dashboard KR-CLIDN visible?")

    # ─────────────────────────────────────────────
    # SECUENCIA PRINCIPAL (DUAL TERMINAL + OBS)
    # ─────────────────────────────────────────────

    def _run_sequence(self):
        self._log("Director", "🎬 Iniciando secuencia DUAL TERMINAL...")
        self._flog("Iniciando secuencia...", "ok")
        self._start_wall = time.monotonic()

        # ── PASO 1: Detectar o lanzar 2 Konsoles ──
        if self.wid_a and self.wid_b:
            self._log("Director", f"Terminal A: {self.wid_a} | Terminal B: {self.wid_b}")
        else:
            self._flog("Lanzando 2 Konsoles...", "info")
            for i in range(2):
                try:
                    subprocess.Popen(['konsole'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    time.sleep(1.5)
                except FileNotFoundError:
                    self._log("Error", "❌ Konsole no está instalado.")
                    self.is_running = False
                    return

            time.sleep(2.0)
            wids = self._find_all_konsole_wids()
            if len(wids) < 2:
                self._log("Error", f"❌ Se necesitan 2 Konsoles, encontradas: {len(wids)}")
                self.is_running = False
                return
            self.wid_a = wids[-2]
            self.wid_b = wids[-1]

        # ── PASO 2: Redimensionar ──
        self._resize_window(self.wid_a, 450, 800)
        self._resize_window(self.wid_b, 450, 800)
        self._flog("Terminales a 450x800", "ok")
        time.sleep(0.5)

        # ── PASO 3: Conectar a OBS ──
        obs_ok = self.obs.connect()
        if obs_ok:
            scenes = self.obs._get_scene_names()
            self._log("Director", f"🔴 OBS conectado — Escenas: {scenes}")
            self._flog(f"OBS OK — Escenas: {scenes}", "ok")

            if "Terminal-A" not in scenes or "Terminal-B" not in scenes:
                self._log("Director", "⚠ FALTAN escenas 'Terminal-A' y/o 'Terminal-B' en OBS!")
                self._flog("⚠ Crear escenas Terminal-A y Terminal-B", "error")

            self.obs.start_recording()
            time.sleep(1.0)
            self.obs.switch_scene("Terminal-A")
            self._flog("Grabación OBS iniciada", "ok")
        else:
            self._log("Director", "⚠ OBS no disponible — Modo manual")
            self._flog("OBS no disponible", "wait")

        # ── PASO 4: Limpiar Terminal B ──
        self._focus_window(self.wid_b)
        self._type_text(self.wid_b, "clear", delay_ms=20)
        self._send_key(self.wid_b, "Return")
        time.sleep(0.3)

        # ── PASO 5: Boot KR-CLIDN en Terminal A ──
        self._boot_krcli_terminal_a()

        # ── PASO 6: Ejecutar escenas del guion ──
        total = len(self.json_data)
        
        i = 0
        while i < total and self.is_running:
            escena = self.json_data[i]
            
            if self.floating_ctrl:
                self.floating_ctrl.set_scene_info(i + 1, total)
                
            # Verificar salto pendiente
            jump_to = self.floating_ctrl.consume_jump() if self.floating_ctrl else -1
            if jump_to >= 0:
                i = jump_to
                continue
                
            # Verificar skip
            if self.floating_ctrl and self.floating_ctrl.consume_skip():
                i += 1
                continue

            tipo = escena.get("tipo", "")
            step_num = i + 1
            self._log("Director", f"▶ Escena {step_num}/{total} — {tipo.upper()}")

            # Progreso en widget flotante
            if self.floating_ctrl:
                self.floating_ctrl.set_progress(step_num, total)
                self.floating_ctrl.add_log(f"Escena {step_num}/{total}: {tipo.upper()}", "step")

            # Timestamp tracking
            elapsed = time.monotonic() - self._start_wall

            voz_text = escena.get("voz", "")
            text_hash = hashlib.md5(voz_text.encode('utf-8')).hexdigest()[:8] if voz_text else "nohash"

            # Duración del audio
            # Utilizar WorkspaceManager si está disponible y hay sesión activa
            try:
                wm = getattr(self.app, 'workspace_manager', None)
                session = wm.get_active_session() if wm else None
            except:
                session = None

            if session:
                audio_path = os.path.join(session["audio_dir"], f"audio_{i}_{text_hash}.wav")
            else:
                audio_path = os.path.join(self.workspace_dir, f"audio_{i}_{text_hash}.wav")

            if not os.path.exists(audio_path) and voz_text:
                try:
                    self.audio_engine.generar_audio(voz_text, audio_path)
                except Exception:
                    pass
            if os.path.exists(audio_path):
                duracion = self.audio_engine.obtener_duracion(audio_path)
            else:
                # Fallback solo si falló la generación
                duracion = max(1.5, len(voz_text.split()) / 2.5)

            if tipo == "narracion":
                self.timestamps[f"scene_{i}_audio"] = elapsed
                # Solo espera la duración del audio (kr-clidn activo en Terminal A)
                if obs_ok:
                    self.obs.switch_scene("Terminal-A")
                time.sleep(max(0.5, duracion))
                self._flog(f"  Voz: {escena.get('voz', '')[:40]}", "info")

            elif tipo == "ejecucion":
                self.timestamps[f"scene_{i}_command"] = elapsed
                if obs_ok:
                    self.obs.switch_scene("Terminal-B")
                comando_real = escena.get("comando_real", "")
                if comando_real:
                    self._type_text(self.wid_b, comando_real, delay_ms=escena.get("typing_delay"))
                    time.sleep(max(0.5, duracion))
                    self._send_key(self.wid_b, "Return")
                    time.sleep(1.5)
                self._flog(f"  Ejecutado: {comando_real[:40]}", "ok")

            elif tipo == "menu":
                self.timestamps[f"scene_{i}_menu"] = elapsed
                if obs_ok:
                    self.obs.switch_scene("Terminal-A")
                tecla = escena.get("tecla", "")
                texto = escena.get("texto", "")
                espera = float(escena.get("espera", 2.0))
                self.floating_ctrl.add_log(f"Esperando selección menú...", "wait")
                
                if tecla:
                    self._focus_window(self.wid_a)
                    self._type_text(self.wid_a, tecla, delay_ms=150)
                    time.sleep(0.3)
                    self._send_key(self.wid_a, "Return")
                    time.sleep(max(espera, 1.5))
                    
                    # Verificar que la tecla tuvo efecto leyendo el log
                    from kr_studio.core.dynamic_director import read_log_file, LOG_TERMINAL_A
                    log_after = read_log_file(LOG_TERMINAL_A, 15)
                    
                    # Si presionamos "1" y esperamos ver "Consola AI" en el log
                    expected_map = {
                        "1": ["Consola AI", "CONSOLA", "Chat"],
                        "N": ["Nuevo", "Chat", "Nombre"],
                        "n": ["Nuevo", "Chat", "Nombre"],
                    }
                    expected = expected_map.get(tecla, [])
                    if expected and not any(e in log_after for e in expected):
                        self._flog(f"⚠ Tecla '{tecla}' posiblemente no tuvo efecto", "wait")
                        # Reintentar una vez
                        time.sleep(1.0)
                        self._type_text(self.wid_a, tecla, delay_ms=150)
                        self._send_key(self.wid_a, "Return")
                        time.sleep(espera)
                    
                    self._flog(f"Menú: tecla '{tecla}' enviada", "info")
                
                elif texto:
                    self._focus_window(self.wid_a)
                    # Limpiar línea actual antes de escribir (por si hay texto residual)
                    self._send_key(self.wid_a, "ctrl+u")
                    time.sleep(0.2)
                    self._type_text(self.wid_a, texto, delay_ms=escena.get("typing_delay", 80))
                    time.sleep(max(0.5, duracion))
                    self._send_key(self.wid_a, "Return")
                    time.sleep(espera)
                    self._flog(f"Texto enviado: {texto[:35]}", "info")

            elif tipo == "enter":
                terminal = escena.get("terminal", "A")
                wid = self.wid_a if terminal == "A" else self.wid_b
                espera = escena.get("espera", 2.0)
                if obs_ok:
                    scene = "Terminal-A" if terminal == "A" else "Terminal-B"
                    self.obs.switch_scene(scene)
                self._send_key(wid, "Return")
                time.sleep(espera)
                self._flog(f"  Enter Terminal {terminal}", "info")

            elif tipo == "pausa":
                self.timestamps[f"scene_{idx}_pause"] = elapsed
                espera = escena.get("espera", 3.0)
                time.sleep(espera)
                self._flog(f"  Pausa {espera}s", "info")

            elif tipo == "leer":
                # ── LEER → Captura el contenido del terminal ──
                terminal = escena.get("terminal", "A")
                wid = self.wid_a if terminal == "A" else self.wid_b
                espera = escena.get("espera", 2.0)
                time.sleep(espera)  # Esperar a que la respuesta termine

                output = self._read_terminal(wid)
                # Guardar las últimas 30 líneas para contexto
                lines = output.split('\n')
                last_lines = '\n'.join(lines[-30:]) if len(lines) > 30 else output
                self.last_terminal_read = last_lines
                self._log("Director", f"📖 Terminal {terminal} leída ({len(lines)} líneas)")
                self._flog(f"  Leído: {len(lines)} líneas de Terminal {terminal}", "ok")

            elif tipo == "esperar":
                espera = float(escena.get("duracion", 2.0))
                time.sleep(espera)
                self._flog(f"  Pausa: {espera}s", "wait")

            else:
                self._log("Director", f"⚠ Tipo desconocido: {tipo}")
                time.sleep(1.0)

            if self.is_running and self.floating_ctrl and tipo != "esperar":
                if tipo == "narracion":
                    self.floating_ctrl.wait_for_continue(
                        f"Narración {step_num}",
                        duration_seconds=duracion + 0.3
                    )
                else:
                    self.floating_ctrl.wait_for_continue(f"Paso {step_num}/{total} listo")
                    
            # Verificar retry
            if self.floating_ctrl and self.floating_ctrl.consume_retry():
                self.floating_ctrl.add_log(f"↺ Reintentando escena {i+1}", "wait")
                continue
                
            i += 1

        # ── PASO 7: Finalizar ──
        if obs_ok:
            time.sleep(2.0)
            self.obs.stop_recording()
            self.obs.disconnect()
            self._log("Director", "🔴 Grabación detenida.")

        self.is_running = False
        self._log("Director", "✅ Secuencia DUAL finalizada. ¡Video listo!")
        if self.floating_ctrl:
            self.floating_ctrl.notify_finished()
