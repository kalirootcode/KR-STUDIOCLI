"""
obs_controller.py — Controlador de OBS Studio via WebSocket v5
Permite cambiar escenas y controlar grabaciones programáticamente.
Requiere: pip install obs-websocket-py
Requiere: OBS Studio con WebSocket habilitado (Tools > WebSocket Server Settings)
"""
import time
import logging

logger = logging.getLogger(__name__)


class OBSController:
    """Controlador de OBS via obs-websocket-py (WebSocket v5)."""

    def __init__(self, host="localhost", port=4455, password=""):
        self.host = host
        self.port = port
        self.password = password
        self.ws = None
        self.connected = False
        self._obs_requests = None

    def connect(self) -> bool:
        """Intenta conectarse a OBS WebSocket. Retorna True si se conectó."""
        try:
            from obswebsocket import obsws, requests as obs_requests
            self._obs_requests = obs_requests

            logger.info(f"Conectando a OBS en {self.host}:{self.port} (password: {'***' if self.password else 'sin password'})...")

            self.ws = obsws(self.host, self.port, self.password)
            self.ws.connect()
            self.connected = True

            # Verificar conexión listando escenas
            scenes = self._get_scene_names()
            logger.info(f"✅ OBS conectado. Escenas disponibles: {scenes}")
            return True

        except ImportError:
            logger.warning("obs-websocket-py no instalado. pip install obs-websocket-py")
            self.connected = False
            return False

        except Exception as e:
            logger.warning(f"No se pudo conectar a OBS: {e}")
            self.connected = False
            return False

    def disconnect(self):
        """Cierra la conexión con OBS."""
        if self.ws and self.connected:
            try:
                self.ws.disconnect()
            except Exception:
                pass
            self.connected = False

    def _get_scene_names(self) -> list:
        """Obtiene la lista de nombres de escenas disponibles."""
        if not self.connected or not self._obs_requests:
            return []
        try:
            response = self.ws.call(self._obs_requests.GetSceneList())
            scenes = response.getScenes()
            return [s.get("sceneName", "") for s in scenes]
        except Exception as e:
            logger.warning(f"Error al obtener escenas: {e}")
            return []

    def switch_scene(self, scene_name: str) -> bool:
        """Cambia la escena activa en OBS."""
        if not self.connected:
            logger.warning(f"switch_scene('{scene_name}'): No conectado a OBS")
            return False
        try:
            self.ws.call(self._obs_requests.SetCurrentProgramScene(
                sceneName=scene_name
            ))
            logger.info(f"🎬 Escena cambiada a: {scene_name}")
            time.sleep(0.3)
            return True
        except Exception as e:
            logger.warning(f"Error al cambiar escena a '{scene_name}': {e}")
            # Listar escenas disponibles para debug
            available = self._get_scene_names()
            logger.warning(f"Escenas disponibles: {available}")
            return False

    def start_recording(self) -> bool:
        """Inicia la grabación en OBS."""
        if not self.connected:
            return False
        try:
            self.ws.call(self._obs_requests.StartRecord())
            logger.info("🔴 Grabación iniciada")
            return True
        except Exception as e:
            logger.warning(f"Error al iniciar grabación: {e}")
            return False

    def stop_recording(self) -> bool:
        """Detiene la grabación en OBS."""
        if not self.connected:
            return False
        try:
            self.ws.call(self._obs_requests.StopRecord())
            logger.info("⏹ Grabación detenida")
            return True
        except Exception as e:
            logger.warning(f"Error al detener grabación: {e}")
            return False
