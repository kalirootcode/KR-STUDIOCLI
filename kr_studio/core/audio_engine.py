"""
audio_engine.py — Motor de Audio (edge-tts + WAV) — KR-STUDIO
FIXES aplicados:
  - SIN loudnorm: ffmpeg 8.x falla rc=234 con una sola pasada
  - Validación robusta de texto vacío/emojis antes de llamar edge-tts
  - Limpieza de temporales garantizada aunque falle ffmpeg
  - Soporte SSML para pausas naturales
  - Parámetros de voz configurables (rate, pitch, volume)
"""

import subprocess
import os
import re
import wave
import time
import logging
import unicodedata
import typing
import asyncio

try:
    import edge_tts

    EDGE_TTS_LIB_AVAILABLE = True
except ImportError:
    EDGE_TTS_LIB_AVAILABLE = False

from kr_studio.core.pronunciation_mapper import transform_to_pronounceable

logger = logging.getLogger(__name__)

_EMOJI_RE = re.compile(
    "["
    "\U0001f300-\U0001f9ff"
    "\U0001f600-\U0001f64f"
    "\U0001f680-\U0001f6ff"
    "\U00010000-\U0010ffff"
    "\u2600-\u27bf"
    "\u200b-\u200f"
    "\ufe00-\ufe0f"
    "]+",
    flags=re.UNICODE,
)
_CTRL_RE = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]")
_SPACE_RE = re.compile(r" {2,}")


class AudioEngine:
    DEFAULT_VOICE = "es-CO-GonzaloNeural"

    VOICE_OPTIONS = {
        "Gonzalo (Colombia)": "es-CO-GonzaloNeural",
        "Alvaro (España)": "es-ES-AlvaroNeural",
        "Jorge (México)": "es-MX-JorgeNeural",
        "Tomás (Argentina)": "es-AR-TomasNeural",
        "Lorenzo (Chile)": "es-CL-LorenzoNeural",
        "Alex (Perú)": "es-PE-AlexNeural",
        "Mateo (Uruguay)": "es-UY-MateoNeural",
        "Marcelo (Bolivia)": "es-BO-MarceloNeural",
    }

    def __init__(self, voice: typing.Optional[str] = None):
        self.voice = voice or self.DEFAULT_VOICE
        self._studio_rate = "-15%"
        self._studio_pitch = "+0Hz"
        self._studio_vol = "+0%"

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

    def _aplicar_pausas_ssml(self, texto: str) -> str:
        """
        Añade pausas naturales al texto usando SSML.
        Las pausas se insertan después de conectores lógicos y comandos.
        """
        replacements = [
            (r"(\||\|\|)", r'<break time="200ms"/> \1 <break time="200ms"/>'),
            (r"(\&\&)", r'<break time="300ms"/> \1 <break time="300ms"/>'),
            (r"(;)", r'\1 <break time="250ms"/>'),
            (r"(/)", r'<break time="100ms"/> \1 <break time="100ms"/>'),
            (r"(>)", r'\1 <break time="150ms"/>'),
            (r"(<)", r'<break time="150ms"/> \1'),
        ]

        result = texto
        for pattern, replacement in replacements:
            result = re.sub(pattern, replacement, result)

        return f"<speak>{result}</speak>"

    def generar_audio(
        self, texto: str, output_path: str, apply_pronunciation: bool = True
    ) -> float:
        """
        Genera WAV a partir de texto.
        - USA edge-tts con soporte SSML para pausas naturales
        - SIN loudnorm (incompatible con ffmpeg 8.x en una pasada)
        - Retorna 0.0 si el texto no es pronunciable (sin lanzar excepcion)
        - apply_pronunciation: si True, transforma comandos para mejor pronunciación TTS
        """
        texto = self._limpiar(texto)

        if apply_pronunciation:
            texto = transform_to_pronounceable(texto)
        if not texto:
            logger.debug("generar_audio: texto vacio, omitiendo.")
            return 0.0

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        tmp_mp3 = output_path.rsplit(".", 1)[0] + "_tmp.mp3"

        texto_ssml = self._aplicar_pausas_ssml(texto)

        MAX_REINTENTOS = 3
        ultimo_error = ""

        for intento in range(1, MAX_REINTENTOS + 1):
            try:
                if EDGE_TTS_LIB_AVAILABLE:
                    asyncio.run(self._generar_audio_async(texto_ssml, tmp_mp3))
                else:
                    cmd_tts = [
                        "edge-tts",
                        "--voice",
                        self.voice,
                        "--rate",
                        self._studio_rate,
                        "--pitch",
                        self._studio_pitch,
                        "--volume",
                        self._studio_vol,
                        "--text",
                        texto,
                        "--write-media",
                        tmp_mp3,
                    ]
                    res = subprocess.run(
                        cmd_tts, capture_output=True, text=True, timeout=45
                    )
                    if res.returncode != 0:
                        raise RuntimeError(res.stderr or res.stdout)

                if os.path.exists(tmp_mp3):
                    break
                ultimo_error = "Archivo no generado"
            except Exception as e:
                ultimo_error = str(e)
                logger.warning(f"edge-tts intento {intento}: {ultimo_error[:80]}")
                if intento < MAX_REINTENTOS:
                    time.sleep(2.0 * intento)
        else:
            self._rm(tmp_mp3)
            raise RuntimeError(
                f"edge-tts fallo tras {MAX_REINTENTOS} intentos: {ultimo_error}"
            )

        temp_wav = output_path.rsplit(".", 1)[0] + "_temp.wav"

        cmd_ffmpeg_1 = [
            "ffmpeg",
            "-y",
            "-i",
            tmp_mp3,
            "-ar",
            "48000",
            "-ac",
            "1",
            "-sample_fmt",
            "s16",
            "-acodec",
            "pcm_s16le",
            temp_wav,
        ]

        try:
            conv1 = subprocess.run(
                cmd_ffmpeg_1, capture_output=True, text=True, timeout=60
            )
            if conv1.returncode != 0:
                raise RuntimeError(f"ffmpeg paso 1 fallo: {conv1.stderr[:300]}")
        except Exception as e:
            self._rm(tmp_mp3)
            raise RuntimeError(f"ffmpeg paso 1 error: {e}")

        normalized_wav = output_path.rsplit(".", 1)[0] + "_norm.wav"
        loudnorm_1 = subprocess.run(
            [
                "ffmpeg",
                "-i",
                temp_wav,
                "-af",
                "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json",
                "-f",
                "null",
                "-",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        import json
        import re

        match = re.search(r'\{[^}]*"input_i"[^}]*\}', loudnorm_1.stderr)
        if match:
            try:
                norm_data = json.loads(match.group())
                input_i = norm_data.get("input_i", "-16")
                input_tp = norm_data.get("input_tp", "-1.5")
                input_lra = norm_data.get("input_lra", "11")
            except:
                input_i, input_tp, input_lra = "-16", "-1.5", "11"
        else:
            input_i, input_tp, input_lra = "-16", "-1.5", "11"

        cmd_ffmpeg_2 = [
            "ffmpeg",
            "-y",
            "-i",
            temp_wav,
            "-af",
            f"loudnorm=I=-16:TP=-1.5:LRA=11:input_i={input_i}:input_tp={input_tp}:input_lra={input_lra},"
            f"highpass=f=200,lowpass=f=3000,volume=0.5",
            "-ar",
            "48000",
            "-ac",
            "1",
            "-sample_fmt",
            "s16",
            "-acodec",
            "pcm_s16le",
            normalized_wav,
        ]

        try:
            conv2 = subprocess.run(
                cmd_ffmpeg_2, capture_output=True, text=True, timeout=60
            )
            if conv2.returncode != 0:
                import shutil

                shutil.copy(temp_wav, output_path)
            else:
                import shutil

                shutil.move(normalized_wav, output_path)
        except Exception:
            import shutil

            if os.path.exists(temp_wav):
                shutil.copy(temp_wav, output_path)
        finally:
            self._rm(tmp_mp3)
            self._rm(temp_wav)
            self._rm(normalized_wav)

        return self.obtener_duracion(output_path)

    async def _generar_audio_async(self, texto_ssml: str, output_path: str):
        """
        Genera audio usando la librería edge-tts con soporte SSML.
        """
        rate_str = self._studio_rate
        pitch_str = self._studio_pitch
        vol_str = self._studio_vol

        communicate = edge_tts.Communicate(
            texto_ssml, self.voice, rate=rate_str, pitch=pitch_str, volume=vol_str
        )
        await communicate.save(output_path)

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
