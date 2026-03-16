"""
audio_engine.py — Motor de Audio (edge-tts + WAV) — KR-STUDIO
FIXES aplicados:
  - SIN --ssml: causaba "one of the arguments -t/--text required" en algunos entornos
  - SIN loudnorm: ffmpeg 8.x falla rc=234 con una sola pasada
  - Validación robusta de texto vacío/emojis antes de llamar edge-tts
  - Limpieza de temporales garantizada aunque falle ffmpeg
"""
import subprocess
import os
import re
import wave
import time
import logging
import unicodedata
import typing

logger = logging.getLogger(__name__)

_EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001F9FF"
    "\U0001F600-\U0001F64F"
    "\U0001F680-\U0001F6FF"
    "\U00010000-\U0010FFFF"
    "\u2600-\u27BF"
    "\u200B-\u200F"
    "\uFE00-\uFE0F"
    "]+",
    flags=re.UNICODE,
)
_CTRL_RE  = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]")
_SPACE_RE = re.compile(r" {2,}")


class AudioEngine:

    DEFAULT_VOICE = "es-CO-GonzaloNeural"

    VOICE_OPTIONS = {
        "Gonzalo (Colombia)": "es-CO-GonzaloNeural",
        "Alvaro (Espana)":    "es-ES-AlvaroNeural",
        "Andres (Mexico)":    "es-MX-JorgeNeural",
        "Tomas (Argentina)":  "es-AR-TomasNeural",
    }

    def __init__(self, voice: typing.Optional[str] = None):
        self.voice = voice or self.DEFAULT_VOICE

    def _limpiar(self, texto: str) -> str:
        if not isinstance(texto, str):
            return ""
        texto = unicodedata.normalize("NFC", texto)
        texto = _EMOJI_RE.sub(" ", texto)
        texto = _CTRL_RE.sub(" ", texto)
        texto = _SPACE_RE.sub(" ", texto).strip()
        if sum(1 for c in texto if c.isalpha()) < 2:
            return ""
        return texto

    def generar_audio(self, texto: str, output_path: str) -> float:
        """
        Genera WAV a partir de texto.
        - USA siempre --text (nunca --ssml, que falla en algunos entornos)
        - SIN loudnorm (incompatible con ffmpeg 8.x en una pasada)
        - Retorna 0.0 si el texto no es pronunciable (sin lanzar excepcion)
        """
        texto = self._limpiar(texto)
        if not texto:
            logger.debug("generar_audio: texto vacio, omitiendo.")
            return 0.0

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        tmp_mp3 = output_path.rsplit(".", 1)[0] + "_tmp.mp3"

        cmd_tts = [
            "edge-tts",
            "--voice", self.voice,
            "--rate",  "+0%",
            "--text",  texto,
            "--write-media", tmp_mp3,
        ]

        MAX_REINTENTOS = 3
        ultimo_error = ""

        for intento in range(1, MAX_REINTENTOS + 1):
            try:
                res = subprocess.run(cmd_tts, capture_output=True, text=True, timeout=45)
                if res.returncode == 0 and os.path.exists(tmp_mp3):
                    break
                ultimo_error = (res.stderr or res.stdout or "").strip()
                logger.warning(f"edge-tts intento {intento}: rc={res.returncode} {ultimo_error[:80]}")  # type: ignore
            except FileNotFoundError:
                raise RuntimeError("edge-tts no instalado. Activa el venv: pip install edge-tts")
            except subprocess.TimeoutExpired:
                ultimo_error = "Timeout 45s"
            if intento < MAX_REINTENTOS:
                time.sleep(2.0 * intento)
        else:
            self._rm(tmp_mp3)
            raise RuntimeError(f"edge-tts fallo tras {MAX_REINTENTOS} intentos: {ultimo_error}")

        cmd_ffmpeg = [
            "ffmpeg", "-y", "-i", tmp_mp3,
            "-ar", "48000", "-ac", "1",
            "-sample_fmt", "s16", "-acodec", "pcm_s16le",
            output_path,
        ]

        try:
            conv = subprocess.run(cmd_ffmpeg, capture_output=True, text=True, timeout=60)
            if conv.returncode != 0:
                raise RuntimeError(f"ffmpeg fallo (rc={conv.returncode}): {conv.stderr[:300]}")  # type: ignore
        finally:
            self._rm(tmp_mp3)

        return self.obtener_duracion(output_path)

    def obtener_duracion(self, audio_path: str) -> float:
        try:
            with wave.open(audio_path, "r") as wf:
                return wf.getnframes() / float(wf.getframerate())
        except Exception:
            return 3.0

    @staticmethod
    def _rm(path: str):
        try:
            if path and os.path.exists(path):
                os.remove(path)
        except OSError:
            pass
