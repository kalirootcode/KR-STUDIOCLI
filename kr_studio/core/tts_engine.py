"""
tts_engine.py — Motor TTS unificado para KR-STUDIO
Genera audio con edge-tts y reproduce con mpv.
Usado por DynamicDirector y SoloDirector.
"""
import os
import re
import time
import logging
import subprocess
import unicodedata

from kr_studio.core.audio_engine import AudioEngine

logger = logging.getLogger(__name__)

# Regex para detectar si queda texto pronunciable tras limpiar
_ALPHA_RE = re.compile(r"[a-záéíóúüñA-ZÁÉÍÓÚÜÑ]")


class TTSEngine:
    """
    Motor TTS con generación y reproducción en vivo.

    Mejoras vs versión anterior:
    - Validación y limpieza de texto antes de llamar a AudioEngine.
    - Supresión silenciosa (sin excepción) de texto no pronunciable.
    - Gestión de proceso mpv más robusta (kill si terminate falla).
    - speak() nunca lanza excepción al llamador — siempre retorna float.
    - Método speak_blocking() espera el fin real del proceso mpv.
    """

    def __init__(self, workspace_dir: str, subdir: str = "audio_tts"):
        self.audio_engine  = AudioEngine()
        self.audio_dir     = os.path.join(workspace_dir, subdir)
        os.makedirs(self.audio_dir, exist_ok=True)
        self._counter      = 0
        self._current_proc = None

    # ─────────────────────────────────────────
    #  Validación interna
    # ─────────────────────────────────────────

    @staticmethod
    def _texto_valido(texto) -> bool:
        """
        Retorna True solo si `texto` contiene al menos 2 letras tras
        eliminar emojis, espacios y caracteres no imprimibles.
        Nunca lanza excepción.
        """
        if not isinstance(texto, str) or not texto.strip():
            return False
        # Normalizar y quitar no-imprimibles / emojis básicos
        try:
            texto_n = unicodedata.normalize("NFC", texto)
        except Exception:
            texto_n = texto
        limpio = re.sub(r"[^\w\s]", "", texto_n, flags=re.UNICODE)
        return len(_ALPHA_RE.findall(limpio)) >= 2

    # ─────────────────────────────────────────
    #  API pública
    # ─────────────────────────────────────────

    def speak(self, text: str) -> float:
        """
        Genera TTS y reproduce en background.
        - Nunca lanza excepción: errores se loguean como WARNING.
        - Retorna 0.0 si el texto no es pronunciable.
        - Retorna 2.0 si ocurre un error inesperado (fallback seguro).
        """
        if not self._texto_valido(text):
            logger.debug(f"speak: texto omitido (no pronunciable): {repr(text[:60])}")
            return 0.0

        self._counter += 1
        audio_path = os.path.join(self.audio_dir, f"tts_{self._counter}.wav")

        try:
            duracion = self.audio_engine.generar_audio(text, audio_path)

            if duracion <= 0.0 or not os.path.exists(audio_path):
                return 0.0

            self.stop_current()
            self._current_proc = subprocess.Popen(
                ["mpv", "--no-video", "--really-quiet", audio_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            logger.info(f"🔊 TTS ({duracion:.1f}s): {text[:60]}")
            return duracion

        except RuntimeError as e:
            # Error irrecuperable de edge-tts / ffmpeg — logueamos y seguimos
            logger.warning(f"TTS RuntimeError: {e}")
            return 2.0
        except Exception as e:
            logger.warning(f"TTS error inesperado: {type(e).__name__}: {e}")
            return 2.0

    def speak_and_wait(self, text: str):
        """
        Genera TTS, reproduce y espera al menos la duración del audio.
        Usa poll() sobre el proceso mpv para esperar de forma precisa.
        """
        dur = self.speak(text)
        if dur <= 0.0:
            return
        # Esperar que mpv termine, con un límite seguro de dur + 3s
        deadline = time.time() + dur + 3.0
        while self._current_proc and time.time() < deadline:
            if self._current_proc.poll() is not None:
                break
            time.sleep(0.1)
        # Garantía mínima
        time.sleep(max(0, dur - (time.time() - (deadline - dur - 3.0))))

    def speak_blocking(self, text: str) -> float:
        """
        Genera TTS y bloquea hasta que mpv termina completamente.
        Útil cuando necesitas sincronización exacta (ej: subtítulos).
        """
        dur = self.speak(text)
        if dur > 0.0 and self._current_proc:
            try:
                self._current_proc.wait(timeout=dur + 10.0)
            except subprocess.TimeoutExpired:
                logger.warning("speak_blocking: mpv tardó demasiado, forzando stop.")
                self.stop_current()
        return dur

    def play_audio(self, path: str):
        """Reproduce un WAV de forma síncrona (bloquea hasta el final)."""
        if not os.path.exists(path):
            logger.debug(f"play_audio: archivo no existe: {path}")
            return
        self.stop_current()
        subprocess.run(
            ["mpv", "--no-video", "--really-quiet", path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def play_audio_bg(self, path: str):
        """Reproduce un WAV en background (no bloquea)."""
        if not os.path.exists(path):
            logger.debug(f"play_audio_bg: archivo no existe: {path}")
            return
        self.stop_current()
        self._current_proc = subprocess.Popen(
            ["mpv", "--no-video", "--really-quiet", path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def stop_current(self):
        """
        Detiene el audio en reproducción.
        Intenta terminate(); si no responde en 2s, hace kill().
        """
        proc = self._current_proc
        if proc is None or proc.poll() is not None:
            self._current_proc = None
            return
        try:
            proc.terminate()
            proc.wait(timeout=2.0)
        except subprocess.TimeoutExpired:
            logger.debug("stop_current: terminate no respondió, haciendo kill().")
            try:
                proc.kill()
                proc.wait(timeout=1.0)
            except Exception:
                pass
        except Exception:
            pass
        finally:
            self._current_proc = None

    def cleanup(self):
        """Detiene audio y elimina WAVs temporales de la sesión."""
        self.stop_current()
        try:
            for fname in os.listdir(self.audio_dir):
                if fname.startswith("tts_") and fname.endswith(".wav"):
                    try:
                        os.remove(os.path.join(self.audio_dir, fname))
                    except OSError:
                        pass
        except Exception as e:
            logger.debug(f"cleanup: error al listar audio_dir: {e}")

    # ─────────────────────────────────────────
    #  Propiedades de conveniencia
    # ─────────────────────────────────────────

    @property
    def voice(self) -> str:
        return self.audio_engine.voice

    @voice.setter
    def voice(self, value: str):
        self.audio_engine.voice = value
