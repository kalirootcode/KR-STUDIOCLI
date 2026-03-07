"""
audio_engine.py — Motor de Audio (edge-tts + mutagen)
Genera archivos MP3 de voz usando edge-tts y extrae duraciones exactas con mutagen.
"""
import subprocess
import os
from mutagen.mp3 import MP3


class AudioEngine:
    # Voz en español latinoamericano masculina por defecto (Voz más humana)
    DEFAULT_VOICE = "es-CO-GonzaloNeural"

    def __init__(self, voice: str = None):
        self.voice = voice or self.DEFAULT_VOICE

    def generar_audio(self, texto: str, output_path: str) -> float:
        """
        Genera un archivo MP3 a partir de texto usando edge-tts (subprocess).
        Retorna la duración en segundos del archivo generado.
        """
        # Asegurar que el directorio de salida exista
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Ejecutar edge-tts como subproceso
        cmd = [
            "edge-tts",
            "--voice", self.voice,
            "--text", texto,
            "--write-media", output_path
        ]

        max_retries = 3
        for attempt in range(max_retries):
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode == 0:
                    return self.obtener_duracion(output_path)
                else:
                    last_err = result.stderr
            except FileNotFoundError:
                raise RuntimeError("edge-tts no está instalado. Ejecuta: pip install edge-tts")
            except subprocess.TimeoutExpired:
                last_err = "edge-tts tardó demasiado en responder."
            
            # Si falla, esperar antes de reintentar
            import time
            time.sleep(2.0)
            
        raise RuntimeError(f"edge-tts falló después de {max_retries} intentos. Último error: {last_err}")

        return self.obtener_duracion(output_path)

    def obtener_duracion(self, audio_path: str) -> float:
        """Obtiene la duración en segundos (float) de un archivo MP3."""
        try:
            audio = MP3(audio_path)
            return audio.info.length
        except Exception:
            return 3.0  # Duración por defecto si falla la lectura
