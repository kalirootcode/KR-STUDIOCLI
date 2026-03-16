# kr_studio/core/tts_providers/__init__.py
from .base import TTSProvider
from .edge_tts_provider import EdgeTTSProvider

# Lista de proveedores disponibles para ser descubiertos por la UI
AVAILABLE_PROVIDERS = {
    "EdgeTTS": EdgeTTSProvider
}
