"""
base.py - Define la interfaz para los proveedores de TTS.
"""
from abc import ABC, abstractmethod

class TTSProvider(ABC):
    """
    Clase base abstracta para todos los proveedores de Text-to-Speech.
    Define la interfaz que cada proveedor debe implementar.
    """
    @property
    @abstractmethod
    def name(self) -> str:
        """Retorna el nombre del proveedor de TTS."""
        raise NotImplementedError

    @abstractmethod
    def get_voices(self) -> list[str]:
        """Retorna una lista de voces disponibles para este proveedor."""
        raise NotImplementedError

    @abstractmethod
    def synthesize(self, text: str, output_path: str, voice: str) -> bool:
        """
        Sintetiza el texto dado en un archivo de audio.

        Args:
            text (str): El texto a convertir en audio.
            output_path (str): La ruta donde se guardará el archivo de audio.
            voice (str): El identificador de la voz a utilizar.

        Returns:
            bool: True si la síntesis fue exitosa, False en caso contrario.
        """
        raise NotImplementedError
