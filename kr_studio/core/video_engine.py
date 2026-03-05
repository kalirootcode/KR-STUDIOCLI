"""
video_engine.py — Ensamblaje y renderizado de video final (moviepy)
Combina video crudo + audios TTS en sus tiempos exactos.
"""
import os
import logging

logger = logging.getLogger(__name__)


class VideoEngine:
    """Motor de renderizado de video con moviepy."""

    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def render(
        self,
        video_path: str,
        timestamps: dict,
        audio_dir: str,
        output_path: str = None,
        bg_music_path: str = None,
        bg_volume: float = 0.10
    ) -> str:
        """
        Renderiza el video final sincronizando audios con timestamps.

        Args:
            video_path: Ruta al video crudo (.mp4)
            timestamps: Dict con tiempos exactos {"scene_0_audio": 0.0, ...}
            audio_dir: Directorio con archivos .mp3 generados
            output_path: Ruta de salida (default: workspace/VIRAL_REEL_FINAL.mp4)
            bg_music_path: Pista de fondo opcional
            bg_volume: Volumen de fondo (0.0 - 1.0)

        Returns:
            Ruta al video final renderizado.
        """
        if output_path is None:
            output_path = os.path.join(self.output_dir, "VIRAL_REEL_FINAL.mp4")

        try:
            from moviepy import VideoFileClip, AudioFileClip, CompositeAudioClip

            logger.info(f"🎬 Cargando video: {video_path}")
            video = VideoFileClip(video_path)
            video_duration = video.duration
            logger.info(f"   Duración: {video_duration:.1f}s")

            # ── Recopilar audios y posicionarlos ──
            audio_clips = []

            # Buscar archivos de audio TTS
            audio_files = sorted([
                f for f in os.listdir(audio_dir)
                if f.endswith('.mp3')
            ])

            logger.info(f"   Audios encontrados: {len(audio_files)}")

            # Mapear timestamps de audio a clips
            audio_timestamps = sorted([
                (k, v) for k, v in timestamps.items()
                if "audio" in k.lower() or "tts" in k.lower() or "narr" in k.lower()
            ], key=lambda x: x[1])

            for idx, audio_file in enumerate(audio_files):
                audio_path_full = os.path.join(audio_dir, audio_file)

                # Determinar timestamp de inicio
                if idx < len(audio_timestamps):
                    start_time = audio_timestamps[idx][1]
                else:
                    # Si no hay timestamp, distribuir equitativamente
                    start_time = (idx / max(len(audio_files), 1)) * video_duration

                # Asegurar que no exceda la duración del video
                if start_time >= video_duration:
                    continue

                try:
                    clip = AudioFileClip(audio_path_full)
                    clip = clip.with_start(start_time)

                    # Recortar si excede el video
                    max_dur = video_duration - start_time
                    if clip.duration > max_dur:
                        clip = clip.subclipped(0, max_dur)

                    audio_clips.append(clip)
                    logger.info(f"   🔊 {audio_file} → {start_time:.1f}s")
                except Exception as e:
                    logger.warning(f"   Error cargando {audio_file}: {e}")

            # ── Música de fondo (opcional) ──
            if bg_music_path and os.path.exists(bg_music_path):
                try:
                    bg = AudioFileClip(bg_music_path)
                    # Loop si es más corta que el video
                    if bg.duration < video_duration:
                        loops = int(video_duration / bg.duration) + 1
                        bg = bg.loop(n=loops)
                    bg = bg.subclipped(0, video_duration)
                    bg = bg.with_volume_scaled(bg_volume)
                    audio_clips.insert(0, bg)
                    logger.info(f"   🎵 Fondo musical al {int(bg_volume*100)}%")
                except Exception as e:
                    logger.warning(f"   Error con música de fondo: {e}")

            # ── Componer audio final ──
            if audio_clips:
                final_audio = CompositeAudioClip(audio_clips)
                video = video.with_audio(final_audio)
                logger.info(f"   🎚️ {len(audio_clips)} pistas de audio compuestas")
            else:
                logger.warning("   ⚠ Sin audios — exportando video sin narración")

            # ── Exportar ──
            logger.info(f"🎞️ Renderizando → {output_path}")
            video.write_videofile(
                output_path,
                codec="libx264",
                audio_codec="aac",
                fps=30,
                preset="medium",
                threads=4,
                logger=None  # Silenciar tqdm de moviepy
            )

            # Cerrar clips
            video.close()
            for c in audio_clips:
                try:
                    c.close()
                except Exception:
                    pass

            file_size = os.path.getsize(output_path) / (1024 * 1024)
            logger.info(f"✅ Video final: {output_path} ({file_size:.1f} MB)")
            return output_path

        except ImportError as e:
            logger.error(f"Dependencia faltante: {e}. pip install moviepy")
            return ""
        except Exception as e:
            logger.error(f"Error renderizando: {e}")
            return ""

    def get_timestamps_from_json(self, json_data: list) -> dict:
        """
        Genera timestamps estimados a partir de un JSON de escenas.
        Útil cuando no hay timestamps reales del director.
        """
        timestamps = {}
        current_time = 0.0

        for idx, scene in enumerate(json_data):
            tipo = scene.get("tipo", "")

            if tipo == "narracion":
                timestamps[f"scene_{idx}_narration"] = current_time
                current_time += 5.0  # Estimación

            elif tipo == "ejecucion":
                timestamps[f"scene_{idx}_command"] = current_time
                current_time += scene.get("espera", 4.0) + 2.0

            elif tipo == "pausa":
                timestamps[f"scene_{idx}_pause"] = current_time
                current_time += scene.get("espera", 3.0)

            elif tipo == "menu":
                timestamps[f"scene_{idx}_menu"] = current_time
                current_time += scene.get("espera", 2.0)

        return timestamps
