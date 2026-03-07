"""
video_engine.py — Ensamblaje y renderizado de video final (moviepy + ffmpeg)
Combina clips de video/imagen/audio del timeline en un archivo MP4 final.

Estrategia de renderizado (anti-hang):
  1. Compositar video con moviepy → MP4 sin audio (rápido, sin deadlocks)
  2. Compositar audio por separado → WAV
  3. Muxear video + audio con ffmpeg subprocess (confiable, sin pipes colgados)
"""
import os
import subprocess
import threading
import traceback
import time as time_module
import sys
import re

class TqdmCapture:
    """Captura el stderr de tqdm para extraer el porcentaje de progreso."""
    def __init__(self, callback):
        self.callback = callback
        self.original_stderr = sys.stderr
        self.buffer = ""
        self.pct_regex = re.compile(r"(\d+)%\|")

    def write(self, text):
        self.buffer += text
        if '\r' in text or '\n' in text:
            lines = self.buffer.split('\r')
            last_line = lines[-1] if lines[-1] else (lines[-2] if len(lines) > 1 else "")
            match = self.pct_regex.search(last_line)
            if match and self.callback:
                pct = int(match.group(1))
                # Escalar para que sea 15% -> 80% del proceso total
                scaled_pct = 15 + (pct / 100.0) * 65
                # Mandar None como msg para que la UI actualice la barra pero NO llene la consola de logs
                self.callback(scaled_pct, None)
            self.buffer = ""
        self.original_stderr.write(text)

    def flush(self):
        self.original_stderr.flush()

    def __enter__(self):
        sys.stderr = self
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stderr = self.original_stderr

class VideoEngine:
    """Motor de renderizado de video multipista con moviepy + ffmpeg."""

    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.exports_dir = os.path.join(output_dir, "exports")
        os.makedirs(self.exports_dir, exist_ok=True)

    def render_timeline(
        self,
        clips_data: list,
        total_duration: float,
        output_path: str = None,
        resolution: str = "1080p",
        preset: str = "medium",
        progress_callback=None
    ) -> str:
        """
        Renderiza el video final a partir de los clips del TimelineEngine.
        Usa un pipeline de 2 pasos para evitar deadlocks de moviepy:
          Paso 1: Generar video-only MP4
          Paso 2: Generar audio WAV y muxear con ffmpeg
        """
        if output_path is None:
            ts = time_module.strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(self.exports_dir, f"VIRAL_REEL_{ts}.mp4")

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Archivos temporales
        video_only_path = output_path.replace('.mp4', '_VIDEO_ONLY.mp4')
        audio_only_path = output_path.replace('.mp4', '_AUDIO_MIX.wav')

        # Overshadow print locally to pipe all terminal logs to the UI console
        import builtins
        _orig_print = builtins.print
        def print(*args, **kwargs):
            msg = " ".join(str(a) for a in args)
            _orig_print(*args, **kwargs)
            if progress_callback:
                progress_callback(None, msg)

        print(f"\n{'='*60}")
        print(f"🎬 EXPORT: Iniciando render multipista (2-pass)")
        print(f"   Clips totales: {len(clips_data)}")
        print(f"   Duración total: {total_duration:.1f}s")
        print(f"   Resolución: {resolution}")
        print(f"   Output: {output_path}")
        print(f"{'='*60}\n")

        open_clips = []

        try:
            from moviepy import (
                VideoFileClip, ImageClip, AudioFileClip,
                CompositeVideoClip, CompositeAudioClip, ColorClip
            )

            if progress_callback:
                progress_callback(2, "Preparando recursos...")

            # ── Resolución ──
            target_w, target_h = 1080, 1920  # Default: 9:16 vertical para Reels
            bitrate = "8000k"

            if "1920x1080" in resolution or "16:9" in resolution:
                target_w, target_h = 1920, 1080
            elif "1080x1920" in resolution or "9:16" in resolution:
                target_w, target_h = 1080, 1920
            elif "4K" in resolution:
                target_w, target_h = 3840, 2160
                bitrate = "25000k"
            elif "720p" in resolution:
                target_w, target_h = 1280, 720
                bitrate = "5000k"

            target_res = (target_w, target_h)

            # Fondo negro base
            base = ColorClip(size=target_res, color=(0, 0, 0), duration=total_duration)
            video_layers = [base]
            audio_layers = []

            # Separar por tipo/pista
            v_clips = [c for c in clips_data if c.track.startswith("V")]
            a_clips = [c for c in clips_data if c.track.startswith("A")]

            v_tracks_order = {"V1": 0, "V2": 1, "V3": 2}
            v_clips.sort(key=lambda x: (v_tracks_order.get(x.track, 0), x.start))

            print(f"  📹 Video clips: {len(v_clips)}")
            print(f"  🔊 Audio clips: {len(a_clips)}")
            print(f"  📐 Resolución: {target_w}x{target_h}")

            if progress_callback:
                progress_callback(5, f"Compositing {len(v_clips)} clips de video...")

            # ══════════════════════════════════════
            # PASO 1: Procesar clips de video
            # ══════════════════════════════════════
            for idx, tc in enumerate(v_clips):
                is_image = tc.source_path.lower().endswith(
                    ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'))
                clip_dur = tc.end - tc.start

                print(f"  [{idx+1}/{len(v_clips)}] {tc.track}: {tc.label}")
                print(f"      Start: {tc.start:.1f}s → {tc.end:.1f}s (dur: {clip_dur:.1f}s)")

                if not os.path.exists(tc.source_path):
                    print(f"      ⚠ ARCHIVO NO ENCONTRADO")
                    continue

                try:
                    if is_image:
                        c = ImageClip(tc.source_path).with_duration(clip_dur)
                    else:
                        full_clip = VideoFileClip(tc.source_path)
                        open_clips.append(full_clip)

                        real_dur = full_clip.duration
                        src_start = min(tc.source_start, max(0, real_dur - 0.1))
                        src_end = min(src_start + clip_dur, real_dur)
                        c = full_clip.subclipped(src_start, src_end)

                        # Extraer audio nativo del video
                        if not tc.muted and c.audio is not None:
                            a_clip = c.audio.with_start(tc.start)
                            audio_layers.append(a_clip)

                    # Redimensionar con fit (cover/center crop para aspect ratio diferente)
                    c = self._resize_clip(c, target_res)
                    c = c.with_start(tc.start).with_position("center")
                    video_layers.append(c)
                    print(f"      ✅ OK")

                except Exception as e:
                    print(f"      ❌ Error: {e}")
                    traceback.print_exc()

            # ══════════════════════════════════════
            # PASO 2: Procesar clips de audio (A1/A2)
            # ══════════════════════════════════════
            for idx, tc in enumerate(a_clips):
                if tc.muted:
                    continue
                if not os.path.exists(tc.source_path):
                    continue

                try:
                    c = AudioFileClip(tc.source_path)
                    open_clips.append(c)

                    clip_dur = tc.end - tc.start
                    real_dur = c.duration
                    src_start = min(tc.source_start, max(0, real_dur - 0.1))
                    src_end = min(src_start + clip_dur, real_dur)

                    c = c.subclipped(src_start, src_end)
                    c = c.with_start(tc.start)

                    if tc.track == "A2":
                        c = c.with_volume_scaled(0.15)

                    audio_layers.append(c)
                    print(f"  🔊 {tc.track}: {tc.label} ({clip_dur:.1f}s)")
                except Exception as e:
                    print(f"  ❌ Audio error: {e}")

            if len(video_layers) <= 1:
                print("  ⚠ No hay clips de video válidos")
                if progress_callback:
                    progress_callback(0, "Error: No hay clips válidos")
                return ""

            # ══════════════════════════════════════
            # PASO 3: Escribir VIDEO sin audio (rápido, sin deadlocks)
            # ══════════════════════════════════════
            if progress_callback:
                progress_callback(15, "Generando pista de video...")

            ffmpeg_preset = "ultrafast"
            if "slow" in preset.lower():
                ffmpeg_preset = "slow"
            elif "medium" in preset.lower():
                ffmpeg_preset = "medium"

            final_video = CompositeVideoClip(video_layers, size=target_res)
            final_video = final_video.with_duration(total_duration)

            print(f"\n  🎞️ Escribiendo video-only → {video_only_path}")
            print(f"     Preset: {ffmpeg_preset} | Bitrate: {bitrate} | FPS: 30")

            # Monitorear progreso capturando stderr
            if progress_callback:
                progress_callback(15, "Iniciando renderización de frames (x264)...")

            with TqdmCapture(progress_callback) if progress_callback else open(os.devnull, 'w'):
                final_video.write_videofile(
                    video_only_path,
                    codec="libx264",
                    bitrate=bitrate,
                    fps=30,
                    preset=ffmpeg_preset,
                    threads=os.cpu_count() or 4,
                    audio=False,     # ← SIN AUDIO (evita deadlocks)
                    logger="bar",    # ← Imprime barra tqdm, TqdmCapture la intercepta
                )

            print(f"  ✅ Video escrito")
            final_video.close()

            # ══════════════════════════════════════
            # PASO 4: Escribir AUDIO por separado (si hay pistas de audio)
            # ══════════════════════════════════════
            has_audio = bool(audio_layers)

            if has_audio:
                if progress_callback:
                    progress_callback(80, "Generando pista de audio...")

                print(f"  🔊 Escribiendo audio ({len(audio_layers)} pistas) → {audio_only_path}")

                final_audio = CompositeAudioClip(audio_layers)
                final_audio = final_audio.with_duration(total_duration)
                final_audio.write_audiofile(audio_only_path, fps=44100, logger=None)
                final_audio.close()
                print(f"  ✅ Audio escrito")

            # ══════════════════════════════════════
            # PASO 5: Muxear con FFMPEG (confiable, sin cuelgues)
            # ══════════════════════════════════════
            if progress_callback:
                progress_callback(90, "Muxeando video + audio...")

            if has_audio:
                print(f"  🔗 Muxeando → {output_path}")
                cmd = [
                    "ffmpeg", "-y",
                    "-i", video_only_path,
                    "-i", audio_only_path,
                    "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k",
                    "-shortest",
                    output_path
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                if result.returncode != 0:
                    print(f"  ⚠ ffmpeg stderr: {result.stderr[:500]}")
                    # Fallback: usar el video sin audio
                    os.rename(video_only_path, output_path)
                    print(f"  ⚠ Usando video sin audio como fallback")
            else:
                # Sin audio, solo renombrar
                os.rename(video_only_path, output_path)

            # ── Limpieza de temporales ──
            for tmp in [video_only_path, audio_only_path]:
                try:
                    if os.path.exists(tmp):
                        os.remove(tmp)
                except Exception:
                    pass

            for c in open_clips:
                try:
                    c.close()
                except Exception:
                    pass

            # ── Resultado ──
            if progress_callback:
                progress_callback(100, "¡Renderizado Completo!")

            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path) / (1024 * 1024)
                print(f"\n  ✅ VIDEO EXPORTADO: {output_path} ({file_size:.1f} MB)")
                return output_path
            else:
                print(f"\n  ❌ No se creó el archivo de salida")
                return ""

        except Exception as e:
            print(f"\n  ❌ ERROR FATAL: {e}")
            traceback.print_exc()
            if progress_callback:
                progress_callback(0, f"Error: {e}")
            return ""

        finally:
            for c in open_clips:
                try:
                    c.close()
                except Exception:
                    pass
            # Limpieza de temporales en caso de error
            for tmp in [video_only_path, audio_only_path]:
                try:
                    if os.path.exists(tmp):
                        os.remove(tmp)
                except Exception:
                    pass

    def _resize_clip(self, clip, target_res):
        """Redimensiona un clip al tamaño target, centrando si el aspect ratio difiere."""
        tw, th = target_res
        cw, ch = clip.w, clip.h

        if (cw, ch) == (tw, th):
            return clip

        # Escalar para cubrir (cover fit) y luego recortar al centro
        scale_w = tw / cw
        scale_h = th / ch
        scale = max(scale_w, scale_h)

        new_w = int(cw * scale)
        new_h = int(ch * scale)

        clip = clip.resized(new_size=(new_w, new_h))

        # Recortar al centro si sobra
        if new_w > tw or new_h > th:
            x_center = new_w // 2
            y_center = new_h // 2
            x1 = x_center - tw // 2
            y1 = y_center - th // 2
            clip = clip.cropped(x1=x1, y1=y1, width=tw, height=th)

        return clip
