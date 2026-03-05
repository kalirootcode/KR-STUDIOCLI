"""
tts_engine.py — Motor TTS unificado para KR-STUDIO
Genera audio con edge-tts y reproduce con mpv.
Usado por DynamicDirector y SoloDirector.
"""
import subprocess
import os
import time
import logging

from kr_studio.core.audio_engine import AudioEngine

logger = logging.getLogger(__name__)


class TTSEngine:
    """Motor TTS con generación y reproducción en vivo."""

    def __init__(self, workspace_dir: str, subdir: str = "audio_tts"):
        self.audio_engine = AudioEngine()
        self.audio_dir = os.path.join(workspace_dir, subdir)
        os.makedirs(self.audio_dir, exist_ok=True)
        self._counter = 0
        self._current_proc = None  # proceso mpv actual

    def speak(self, text: str) -> float:
        """
        Genera TTS y reproduce audio en background.
        Retorna la duración del audio en segundos.
        No bloquea — el audio se reproduce mientras el código continúa.
        """
        if not text or not text.strip():
            return 0.0

        self._counter += 1
        audio_path = os.path.join(self.audio_dir, f"tts_{self._counter}.mp3")

        try:
            duracion = self.audio_engine.generar_audio(text, audio_path)

            # Detener audio anterior si aún suena
            self.stop_current()

            # Reproducir en background
            self._current_proc = subprocess.Popen(
                ['mpv', '--no-video', '--really-quiet', audio_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            logger.info(f"🔊 TTS ({duracion:.1f}s): {text[:50]}...")
            return duracion

        except Exception as e:
            logger.warning(f"TTS error: {e}")
            return 2.0

    def speak_and_wait(self, text: str):
        """Genera TTS, reproduce y espera a que termine."""
        dur = self.speak(text)
        time.sleep(max(dur, 1.5))

    def play_audio(self, path: str):
        """Reproduce un archivo de audio previamente generado de forma síncrona."""
        if not os.path.exists(path):
            return
        self.stop_current()
        subprocess.run(['mpv', '--no-video', '--really-quiet', path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def play_audio_bg(self, path: str):
        """Reproduce un archivo de audio previamente generado en background."""
        if not os.path.exists(path):
            return
        self.stop_current()
        self._current_proc = subprocess.Popen(
            ['mpv', '--no-video', '--really-quiet', path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    def stop_current(self):
        """Detiene el audio que se está reproduciendo."""
        if self._current_proc and self._current_proc.poll() is None:
            try:
                self._current_proc.terminate()
                self._current_proc.wait(timeout=2)
            except Exception:
                pass
            self._current_proc = None

    def cleanup(self):
        """Limpia archivos temporales de audio."""
        self.stop_current()
        try:
            for f in os.listdir(self.audio_dir):
                if f.startswith("tts_") and f.endswith(".mp3"):
                    os.remove(os.path.join(self.audio_dir, f))
        except Exception:
            pass
