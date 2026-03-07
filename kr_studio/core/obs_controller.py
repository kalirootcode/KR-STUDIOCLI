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

    def get_current_scene(self) -> str:
        """Obtiene el nombre de la escena activa."""
        if not self.connected:
            return ""
        try:
            response = self.ws.call(self._obs_requests.GetCurrentProgramScene())
            return response.datain.get("currentProgramSceneName", "")
        except Exception:
            return ""

    def setup_dual_scenes(self, wid_a: str, wid_b: str) -> dict:
        """
        Configura OBS con escenas para captura de terminales.
        Crea las escenas si no existen y añade window capture sources.
        Retorna un dict con el resultado.
        """
        result = {"ok": False, "scenes": [], "errors": []}

        if not self.connected:
            result["errors"].append("No conectado a OBS")
            return result

        existing = self._get_scene_names()
        result["scenes"] = existing

        scenes_to_create = ["Terminal-B"]
        if wid_a:
            scenes_to_create.append("Terminal-A")

        # Crear escenas si no existen
        for scene_name in scenes_to_create:
            if scene_name not in existing:
                try:
                    self.ws.call(self._obs_requests.CreateScene(
                        sceneName=scene_name
                    ))
                    logger.info(f"✅ Escena '{scene_name}' creada")
                    result["scenes"].append(scene_name)
                except Exception as e:
                    result["errors"].append(f"Error creando '{scene_name}': {e}")

        # Intentar agregar Window Capture a cada escena
        captures = []
        if wid_a:
            captures.append(("Terminal-A", "Captura-TermA", wid_a))
        if wid_b:
            captures.append(("Terminal-B", "Captura-TermB", wid_b))

        for scene_name, source_name, wid in captures:
            try:
                # Verificar si ya tiene fuentes
                resp = self.ws.call(self._obs_requests.GetSceneItemList(
                    sceneName=scene_name
                ))
                items = resp.datain.get("sceneItems", [])
                if len(items) > 0:
                    logger.info(f"  '{scene_name}' ya tiene {len(items)} fuentes")
                    continue

                # Crear fuente de captura de ventana
                self.ws.call(self._obs_requests.CreateInput(
                    sceneName=scene_name,
                    inputName=source_name,
                    inputKind="xcomposite_input",
                    inputSettings={
                        "capture_window": "",
                        "capture_window_use_regex": False
                    }
                ))
                logger.info(f"✅ Fuente '{source_name}' agregada a '{scene_name}'")
            except Exception as e:
                msg = f"Fuente en '{scene_name}': {e}"
                logger.warning(msg)
                result["errors"].append(msg)

        if wid_a:
            result["ok"] = "Terminal-A" in result["scenes"] and "Terminal-B" in result["scenes"]
        else:
            result["ok"] = "Terminal-B" in result["scenes"]
        return result
