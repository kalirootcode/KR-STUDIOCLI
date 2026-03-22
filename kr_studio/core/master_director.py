"""
master_director.py - El Motor de Orquestación Unificado de KR-Studio

Esta clase reemplaza a DirectorEngine, DynamicDirectorEngine y SoloDirectorEngine,
unificando la lógica de ejecución de guiones en un único punto de control.

Utiliza un sistema de modos (estrategias) para manejar las variaciones
en la ejecución, como 'DUAL AI' o 'SOLO TERM'.
"""

import logging
import time
from enum import Enum, auto
from typing import Any, Callable, Optional

from kr_studio.core.tts_engine import TTSEngine
from kr_studio.core.x11_controller import X11Controller

logger = logging.getLogger(__name__)


class DirectorMode(Enum):
    """Define los modos de operación del director."""

    DUAL_AI = auto()
    SOLO_TERM = auto()


class MasterDirector:
    """
    Clase unificada para orquestar la ejecución de guiones, controlando
    terminales, audio y la sincronización de eventos.
    """

    def __init__(
        self,
        guion: list[dict[str, Any]],
        mode: DirectorMode,
        workspace_dir: str,
        typing_speed: int = 80,
        wid_a: Optional[int] = None,
        wid_b: Optional[int] = None,
        project_name: str = "default",
        progress_callback: Optional[Callable] = None,
    ):
        self.guion = guion
        self.mode = mode
        self.typing_speed_ms = typing_speed
        self.wid_a = wid_a
        self.wid_b = wid_b
        self.project_name = project_name
        self.is_running = False
        self.stop_requested = False
        self.progress_callback = progress_callback
        self.floating_ctrl = None

        logger.info(
            f"MasterDirector initialized. Mode: {self.mode.name}, WID_B: {self.wid_b}"
        )
        self.x11 = X11Controller()
        self.tts = TTSEngine(workspace_dir)

    def run(self):
        """
        Ejecuta el guion completo, escena por escena.
        """
        self.is_running = True
        self.stop_requested = False
        logger.info(f"Iniciando ejecución del guion con {len(self.guion)} escenas.")

        for i, escena in enumerate(self.guion):
            if self.stop_requested:
                logger.info("Ejecución detenida por el usuario.")
                break

            logger.info(
                f"--- Ejecutando Escena {i + 1}/{len(self.guion)}: {escena.get('tipo')} ---"
            )
            if self.progress_callback:
                self.progress_callback(i + 1, len(self.guion))

            self._execute_scene(escena)

        self.is_running = False
        logger.info("Ejecución del guion completada.")

    def stop(self):
        """Solicita detener la ejecución del guion."""
        self.stop_requested = True

    def _execute_scene(self, escena: dict):
        """
        Ejecuta una escena individual basándose en su tipo y el modo actual.
        """
        scene_type = escena.get("tipo")
        if not scene_type:
            logger.warning(f"Escena sin tipo definido, omitiendo: {escena}")
            return

        # Lógica de audio (común a muchas escenas)
        voz = escena.get("voz")
        if voz:
            # En modo manual, no generamos TTS, solo calculamos el tiempo
            palabras = len(voz.split())
            duracion_audio = max(2.0, palabras / 2.5)  # 150 ppm = 2.5 pps

            # Loguear las instrucciones para que el usuario las lea
            if hasattr(self, "floating_ctrl") and self.floating_ctrl:
                self.floating_ctrl.add_log(f"🎙 {voz}", tag="info")
        else:
            duracion_audio = 0

        # Mapeo de tipos de escena a manejadores
        handlers = {
            "narracion": self._handle_narracion,
            "ejecucion": self._handle_ejecucion,
            "pausa": self._handle_pausa,
            "menu": self._handle_menu,
            "enter": self._handle_enter,
            "leer": self._handle_leer,
            "esperar": self._handle_esperar,
        }

        handler = handlers.get(scene_type)
        if handler:
            handler(escena, duracion_audio)
        else:
            logger.warning(f"Tipo de escena '{scene_type}' no reconocido. Omitiendo.")

    # --------------------------------------------------------------------
    # MANEJADORES DE ESCENAS (Scene Handlers)
    # --------------------------------------------------------------------

    def _handle_narracion(self, escena: dict, duracion_audio: float):
        """Maneja escenas de tipo 'narracion'."""
        if duracion_audio > 0:
            if self.floating_ctrl:
                # Espera automática del tiempo calculado, pero permite pulsar Continuar para omitir
                self.floating_ctrl.wait_for_continue(
                    step_msg=f"⏳ Narrando ({int(duracion_audio)}s)...",
                    duration_seconds=duracion_audio,
                )
            else:
                time.sleep(duracion_audio)

    def _handle_ejecucion(self, escena: dict, duracion_audio: float):
        """Maneja escenas de tipo 'ejecucion'."""
        if self.mode == DirectorMode.DUAL_AI:
            target_wid = self.wid_b
            comando = escena.get("comando_real")
        elif self.mode == DirectorMode.SOLO_TERM:
            target_wid = self.wid_b  # En modo SOLO, todo ocurre en la terminal B
            comando = escena.get("comando_real") or escena.get("comando_visual")
        else:
            logger.warning(
                "Modo de ejecución no configurado para la escena 'ejecucion'."
            )
            return

        if not target_wid or not comando:
            logger.error(
                f"Falta 'target_wid' o 'comando' en la escena de ejecución: {escena}"
            )
            return

        # --- PAUSA MANUAL PARA EL USUARIO ---
        if self.floating_ctrl:
            self.floating_ctrl.wait_for_continue(
                step_msg=f"⌨️ Ejecutar comando: {comando[:30]}..."
            )
            if self.stop_requested:
                return

        logger.info(f"Executing command: '{comando}' on WID: {target_wid}")

        self.x11.focus_window(str(target_wid))  # Asegurar que la ventana esté visible
        time.sleep(0.2)
        self.x11.type_text(str(target_wid), comando, speed_pct=self.typing_speed_ms)
        self.x11.send_key(str(target_wid), "Return")

        # En modo manual paso a paso, no hace falta dormir el tiempo de audio
        # después del comando porque el usuario ya lo controló con Continuar.

    def _handle_pausa(self, escena: dict, duracion_audio: float):
        """Maneja escenas de tipo 'pausa'."""
        espera = float(escena.get("espera", 1.0))
        if self.floating_ctrl:
            self.floating_ctrl.wait_for_continue(
                step_msg=f"⏳ Pausa ({espera}s)...", duration_seconds=espera
            )
        else:
            time.sleep(espera)

    def _handle_menu(self, escena: dict, duracion_audio: float):
        """Maneja escenas de tipo 'menu' (solo para DUAL_AI)."""
        if self.mode != DirectorMode.DUAL_AI:
            logger.debug("Omitiendo escena 'menu' en modo SOLO_TERM.")
            return

        if not self.wid_a:
            logger.error("Se requiere WID de Terminal A para la escena 'menu'.")
            return

        self.x11.focus_window(str(self.wid_a))
        time.sleep(0.2)
        if "tecla" in escena:
            self.x11.send_key(str(self.wid_a), escena["tecla"])
        elif "texto" in escena:
            self.x11.type_text(
                str(self.wid_a), escena["texto"], speed_pct=self.typing_speed_ms
            )

        time.sleep(max(0, duracion_audio))

    def _handle_enter(self, escena: dict, duracion_audio: float):
        """Maneja escenas de tipo 'enter'."""
        terminal = escena.get("terminal", "A").upper()
        target_wid = self.wid_a if terminal == "A" else self.wid_b

        if not target_wid:
            logger.error(f"WID para la terminal '{terminal}' no disponible.")
            return

        self.x11.focus_window(str(target_wid))
        time.sleep(0.2)
        self.x11.send_key(str(target_wid), "Return")
        time.sleep(max(0, duracion_audio))

    def _handle_leer(self, escena: dict, duracion_audio: float):
        """Maneja escenas de tipo 'leer' (marcador de posición)."""
        # En esta refactorización, 'leer' no tiene una acción directa,
        # pero es importante para la lógica del guion.
        logger.info("Escena 'leer' encontrada. Esperando finalización de audio.")
        time.sleep(duracion_audio)

    def _handle_esperar(self, escena: dict, duracion_audio: float):
        """Maneja escenas de tipo 'esperar'."""
        # Esta es una pausa manual que el usuario debe continuar
        logger.info(
            "Pausa manual. Esperando la intervención del usuario para continuar..."
        )
        # En una implementación completa, esto se conectaría a un evento de la UI.
        # Por ahora, simplemente logueamos y continuamos.
        time.sleep(duracion_audio)
