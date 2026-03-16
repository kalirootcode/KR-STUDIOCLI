"""
edge_tts_provider.py - Proveedor de TTS que utiliza Microsoft Edge TTS.
"""
import edge_tts
import asyncio
import logging
from .base import TTSProvider

logger = logging.getLogger(__name__)

class EdgeTTSProvider(TTSProvider):
    """
    Proveedor de TTS que utiliza la biblioteca edge-tts de Microsoft.
    """
    @property
    def name(self) -> str:
        return "EdgeTTS"

    def get_voices(self) -> list[str]:
        """Retorna una lista de voces en español para Edge TTS."""
        # Esta es una lista curada, se podría obtener dinámicamente
        return [
            "es-MX-GerardoNeural",
            "es-ES-AlvaroNeural",
            "es-AR-ElenaNeural",
            "es-CO-SalomeNeural",
            "es-US-AlonsoNeural"
        ]

    def synthesize(self, text: str, output_path: str, voice: str | None = None) -> bool:
        """Sintetiza audio usando Edge-TTS."""
        if not text.strip():
            logger.debug("EdgeTTSProvider: texto vacío, omitiendo síntesis.")
            return False
        
        # Usar voz por defecto si no se especifica una
        active_voice = voice or self.get_voices()[0]

        try:
            async def _main():
                comunicador = edge_tts.Communicate(text, active_voice)
                await comunicador.save(output_path)
            
            # asyncio.run() es una forma simple de ejecutar la corutina
            asyncio.run(_main())
            logger.debug(f"Audio sintetizado con éxito en '{output_path}' usando {active_voice}.")
            return True
        except Exception as e:
            logger.error(f"Error al sintetizar con EdgeTTS: {e}", exc_info=True)
            return False
