"""
master_director.py - El Motor de Orquestación Unificado de KR-Studio

Esta clase reemplaza a DirectorEngine, DynamicDirectorEngine y SoloDirectorEngine,
unificando la lógica de ejecución de guiones en un único punto de control.

Utiliza un sistema de modos (estrategias) para manejar las variaciones
en la ejecución, como 'DUAL AI' o 'SOLO TERM'.
"""

import logging
import os
import subprocess
import time
from enum import Enum, auto
from typing import Any, Callable, Optional

from kr_studio.core.audio_engine import AudioEngine  # type: ignore
from kr_studio.core.x11_controller import X11Controller  # type: ignore

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
        wid_a: int | None = None,
        wid_b: int | None = None,
        project_name: str = "default",
        aspect_ratio: str = "16:9 (YouTube)",
        obs_password: str = "",
        auto_record: bool = False,
        terminals_preconfigured: bool = False,
    ):
        """
        Inicializa el MasterDirector.
        """
        self.guion = guion
        self.mode = mode
        self.typing_speed_ms = typing_speed
        self.typing_delay = typing_speed  # Alias para compatibilidad legacy
        self.wid_a = wid_a
        self.wid_b = wid_b
        self.project_name = project_name
        self.aspect_ratio = aspect_ratio
        self.obs_password = obs_password
        self.auto_record = auto_record
        self.terminals_preconfigured = terminals_preconfigured
        self.is_running = False
        self.stop_requested = False
        self.floating_ctrl = None  # Para control granular de la UI flotante
        self.on_finished: Optional[Callable] = None  # Callback al finalizar run()
        self.use_wrapper = False  # Para boot_terminal_b con venv

        self.workspace_dir = workspace_dir
        self.x11 = X11Controller()
        self.audio = AudioEngine()

        from kr_studio.core.obs_controller import OBSController  # type: ignore

        self.obs = OBSController()
        self._obs_connected = False
        self._obs_recording = False

    # ====================================================================
    # PUNTO DE ENTRADA UNIFICADO
    # ====================================================================

    def setup_and_run(self):
        """
        Punto de entrada unificado:
        1. Llama a setup_terminals() para abrir/redimensionar según aspect_ratio
        2. Conecta OBS si auto_record=True
        3. Llama a run() para ejecutar el guion
        4. Llama a teardown() al finalizar
        """
        try:
            self.setup_terminals()

            # Conectar y grabar OBS si se solicitó
            if self.auto_record and self.obs_password:
                self.obs.password = self.obs_password
                if self.obs.connect():
                    self._obs_connected = True
                    logger.info("OBS conectado correctamente.")
                    if self.obs.start_recording():
                        self._obs_recording = True
                        logger.info("OBS grabación iniciada.")
                    else:
                        logger.warning("No se pudo iniciar grabación OBS.")
                else:
                    logger.warning("No se pudo conectar a OBS.")

            self.run()
        finally:
            self.teardown()

    # ====================================================================
    # SETUP DE TERMINALES
    # ====================================================================

    def setup_terminals(self):
        """
        Configura las Konsoles según aspect_ratio.

        Si terminals_preconfigured=True, las terminales ya fueron configuradas
        por _startup_konsole_thread (main_window) — NO aplicar resize de nuevo.
        """
        if self.terminals_preconfigured:
            logger.info("Terminales ya preconfiguradas, saltando setup_terminals().")
            return

        is_vertical = "9:16" in self.aspect_ratio

        if is_vertical:
            # Modo 9:16: solo Terminal B con resize exacto
            if self.wid_b:
                self._resize_terminal_chars(self.wid_b, rows=40, cols=60)  # type: ignore[arg-type]
                # Reforzar tamaño 2 veces más porque Konsole tiende a resetear
                time.sleep(1.5)
                self._resize_terminal_chars(self.wid_b, rows=40, cols=60)  # type: ignore[arg-type]
                time.sleep(1.5)
                self._resize_terminal_chars(self.wid_b, rows=40, cols=60)  # type: ignore[arg-type]
        else:
            # Modo 16:9: dividir pantalla 50/50
            try:
                result = subprocess.run(
                    ["xdotool", "getdisplaygeometry"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                parts = result.stdout.strip().split()
                screen_w = int(parts[0])
                screen_h = int(parts[1])
            except Exception:
                screen_w, screen_h = 1920, 1080

            half_w = screen_w // 2
            term_h = screen_h - 40  # Margen para barra de tareas

            # Terminal A: mitad izquierda
            if self.wid_a and self.wid_a != self.wid_b:
                hex_a = hex(int(self.wid_a))  # type: ignore[arg-type]
                subprocess.run(
                    ["wmctrl", "-i", "-r", hex_a, "-e", f"0,0,0,{half_w},{term_h}"],
                    capture_output=True,
                    timeout=5,
                )

            # Terminal B: mitad derecha
            if self.wid_b:
                hex_b = hex(int(self.wid_b))  # type: ignore[arg-type]
                subprocess.run(
                    [
                        "wmctrl",
                        "-i",
                        "-r",
                        hex_b,
                        "-e",
                        f"0,{half_w},0,{half_w},{term_h}",
                    ],
                    capture_output=True,
                    timeout=5,
                )

    def _resize_terminal_chars(self, wid: str, rows: int = 40, cols: int = 60):
        """Envía resize -s ROWS COLS dentro de la terminal vía xdotool."""
        try:
            subprocess.run(
                [
                    "xdotool",
                    "type",
                    "--window",
                    str(wid),
                    "--delay",
                    "15",
                    f"resize -s {rows} {cols}",
                ],
                capture_output=True,
                timeout=5,
            )
            subprocess.run(
                ["xdotool", "key", "--window", str(wid), "Return"],
                capture_output=True,
                timeout=5,
            )
            time.sleep(0.5)
            subprocess.run(
                ["xdotool", "type", "--window", str(wid), "--delay", "15", "clear"],
                capture_output=True,
                timeout=5,
            )
            subprocess.run(
                ["xdotool", "key", "--window", str(wid), "Return"],
                capture_output=True,
                timeout=5,
            )
        except Exception as e:
            logger.warning(f"_resize_terminal_chars falló: {e}")

    def boot_terminal_a(self):
        """
        Solo para DUAL AI. Arranca kr-clidn en Terminal A.
        Secuencia EXACTA (en orden, con delays):
          1. script -q -f /tmp/kr_terminal_a.log → Enter → sleep 0.8s
          2. clear → Enter → sleep 0.3s
          3. source venv/bin/activate → Enter → sleep 1.0s
          4. kr-clidn → Enter → sleep 5.0s
          5. Si floating_ctrl: wait_for_continue("KR-CLIDN cargando...")
        """
        if not self.wid_a:
            logger.warning("boot_terminal_a: wid_a no definido.")
            return

        wid = str(self.wid_a)

        self._xdotool_type_enter(wid, "script -q -f /tmp/kr_terminal_a.log")
        time.sleep(0.8)

        self._xdotool_type_enter(wid, "clear")
        time.sleep(0.3)

        self._xdotool_type_enter(wid, "source venv/bin/activate")
        time.sleep(1.0)

        self._xdotool_type_enter(wid, "kr-clidn")
        time.sleep(5.0)

        if self.floating_ctrl:
            self.floating_ctrl.wait_for_continue("KR-CLIDN cargando...")  # type: ignore

    def boot_terminal_b(self):
        """
        Para ambos modos. Inicia logging en Terminal B.
        Secuencia:
          1. script -q -f /tmp/kr_terminal_b.log → Enter → sleep 0.5s
          2. clear → Enter → sleep 0.3s
          Si DUAL AI y use_wrapper=True:
            3. source venv/bin/activate → Enter → sleep 0.5s
        """
        if not self.wid_b:
            logger.warning("boot_terminal_b: wid_b no definido.")
            return

        wid = str(self.wid_b)

        self._xdotool_type_enter(wid, "script -q -f /tmp/kr_terminal_b.log")
        time.sleep(0.5)

        self._xdotool_type_enter(wid, "clear")
        time.sleep(0.3)

        if self.mode == DirectorMode.DUAL_AI and self.use_wrapper:
            self._xdotool_type_enter(wid, "source venv/bin/activate")
            time.sleep(0.5)

    def _xdotool_type_enter(self, wid: str, text: str):
        """Helper: escribe texto en una ventana y presiona Enter."""
        try:
            subprocess.run(
                ["xdotool", "type", "--window", wid, "--delay", "15", text],
                capture_output=True,
                timeout=30,
            )
            subprocess.run(
                ["xdotool", "key", "--window", wid, "Return"],
                capture_output=True,
                timeout=5,
            )
        except Exception as e:
            logger.warning(f"_xdotool_type_enter falló: {e}")

    # ====================================================================
    # TEARDOWN
    # ====================================================================

    def teardown(self):
        """
        Limpieza al finalizar la secuencia.
        - Si OBS conectado y grabando: stop_recording() + disconnect()
        - Si floating_ctrl: notify_finished()
        - is_running = False
        """
        if self._obs_recording:
            try:
                self.obs.stop_recording()
                logger.info("OBS grabación detenida.")
            except Exception as e:
                logger.warning(f"Error deteniendo grabación OBS: {e}")
            self._obs_recording = False

        if self._obs_connected:
            try:
                self.obs.disconnect()
                logger.info("OBS desconectado.")
            except Exception as e:
                logger.warning(f"Error desconectando OBS: {e}")
            self._obs_connected = False

        if self.floating_ctrl:
            try:
                self.floating_ctrl.notify_finished()  # type: ignore
            except AttributeError:
                # fallback si no tiene notify_finished
                try:
                    self.floating_ctrl._set_idle()  # type: ignore
                except Exception:
                    pass
            except Exception:
                pass

        self.is_running = False

    # ====================================================================
    # EJECUCIÓN PRINCIPAL
    # ====================================================================

    def run(self):
        """
        Ejecuta todo el guion escena por escena de forma secuencial.
        """
        self.is_running = True
        self.stop_requested = False
        logger.info(f"MasterDirector iniciado en modo {self.mode.name}")

        try:
            total_scenes = len(self.guion)
            for i, escena in enumerate(self.guion):
                if self.stop_requested:
                    logger.info("Detención del director solicitada.")
                    break

                # Update UI Progress before running the scene
                if self.floating_ctrl:
                    self.floating_ctrl.set_scene_info(i + 1, total_scenes)  # type: ignore

                self._run_scene(escena, i + 1, total_scenes)
        except Exception as e:
            logger.error(f"Error durante la ejecución del director: {e}", exc_info=True)
        finally:
            self.is_running = False
            logger.info("MasterDirector finalizado.")
            if self.on_finished:
                try:
                    self.on_finished()  # type: ignore[misc]
                except Exception:
                    pass

    def stop(self):
        """Solicita la detención de la ejecución."""
        self.stop_requested = True

    def _run_scene(self, escena: dict, current_idx: int, total_scenes: int):
        """Ejecuta una escena individual basándose en su tipo y el modo actual."""
        scene_type = escena.get("tipo")
        if not scene_type:
            logger.warning(f"Escena sin tipo definido, omitiendo: {escena}")
            return

        # Actualizar mini-log
        if self.floating_ctrl:
            tipo_upper = str(scene_type).upper()
            comando = escena.get("comando_real") or escena.get("comando_visual") or ""
            desc = str(comando)[:30] + "..." if len(comando) > 30 else comando  # type: ignore
            msg = f"[{current_idx}/{total_scenes}] {tipo_upper} {desc}"
            self.floating_ctrl.add_log(msg, "step")  # type: ignore

        # Lógica de audio (común a muchas escenas)
        voz = escena.get("voz")
        duracion_audio = 0
        if voz:
            import hashlib

            text_hash = str(hashlib.md5(voz.strip().encode("utf-8")).hexdigest())[:8]  # type: ignore
            safe_name = (
                "".join([c if c.isalnum() else "_" for c in self.project_name])
                or "default"
            )
            audio_dir = os.path.join(
                self.workspace_dir, "projects", safe_name, "audio_live"
            )
            os.makedirs(audio_dir, exist_ok=True)
            audio_path = os.path.join(audio_dir, f"audio_{text_hash}.wav")

            if os.path.exists(audio_path):
                duracion_audio = self.audio.obtener_duracion(audio_path)
                if duracion_audio > 0:
                    subprocess.Popen(
                        ["mpv", "--no-video", "--really-quiet", audio_path],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
            else:
                logger.debug(
                    f"Audio no encontrado para escena: {audio_path}. Generalo manualmente con el botón TTS."
                )

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
            # ── Flujo diferenciado por tipo de escena ──
            # NARRACIÓN: Auto-reproduce el audio, espera su duración y continúa solo.
            #            No necesita aprobación manual. Nada se muestra en la terminal.
            # EJECUCIÓN/OTROS: Espera a que el usuario presione CONTINUAR para ejecutar.
            if scene_type == "narracion":
                # Auto-continuar: la narración es solo voz, no toca la terminal.
                # wait_for_continue con duration_seconds SE ENCARGA de la espera.
                # NO volver a esperar en el handler (evitar doble-wait).
                if self.floating_ctrl and duracion_audio > 0:
                    self.floating_ctrl.wait_for_continue(  # type: ignore[union-attr]
                        step_msg=f"🔊 Narración ({duracion_audio:.1f}s)...",
                        duration_seconds=duracion_audio,
                    )
                    # El handler NO debe esperar de nuevo
                    handler(escena, 0)  # type: ignore  # Pasar 0 para evitar doble-sleep
                elif self.floating_ctrl:
                    # Sin audio: calcular pausa por palabras dentro del handler
                    handler(escena, 0)  # type: ignore
                else:
                    # Sin floating_ctrl, el handler gestiona la pausa
                    handler(escena, duracion_audio)  # type: ignore
            elif scene_type == "pausa":
                # Pausas son automáticas, no requieren interacción
                handler(escena, duracion_audio)  # type: ignore
            else:
                # EJECUCIÓN, MENU, ENTER, LEER, ESPERAR:
                # Requieren que el usuario presione CONTINUAR
                if self.floating_ctrl:
                    self.floating_ctrl.wait_for_continue(  # type: ignore[union-attr]
                        step_msg=f"▶ Listo para: {scene_type.upper()}"
                    )

                    if self.stop_requested:
                        return

                handler(escena, duracion_audio)  # type: ignore
        else:
            logger.warning(f"Tipo de escena '{scene_type}' no reconocido. Omitiendo.")

    # --------------------------------------------------------------------
    # MANEJADORES DE ESCENAS (Scene Handlers)
    # --------------------------------------------------------------------

    def _handle_narracion(self, escena: dict, duracion_audio: float):
        """Maneja escenas de tipo 'narracion'."""
        voz = escena.get("voz", "")

        # Switch de escena OBS según modo
        if self._obs_connected:
            try:
                scene_name = (
                    "Terminal-A" if self.mode == DirectorMode.DUAL_AI else "Terminal-B"
                )
                self.obs.switch_scene(scene_name)
            except Exception as e:
                logger.warning(f"Error cambiando escena OBS: {e}")

        if duracion_audio > 0:
            # Esperar a que termine el audio
            time.sleep(duracion_audio)
        elif voz:
            # Si no hay WAV pre-generado: calcular pausa por palabras
            palabras = len(voz.split())
            pausa_calculada = max(1.5, palabras / 2.5)
            time.sleep(pausa_calculada)

    def _handle_ejecucion(self, escena: dict, duracion_audio: float):
        """Maneja escenas de tipo 'ejecucion'."""
        target_wid = self.wid_b

        # Leer comando con fallback: comando_visual → comando_real → comando
        comando = (
            escena.get("comando_visual")
            or escena.get("comando_real")
            or escena.get("comando")
        )

        logger.info(f"EJECUCION: wid_b={target_wid}, comando='{comando}'")

        if not target_wid or not comando:
            logger.error(
                f"Falta 'target_wid' o 'comando' en la escena de ejecución: {escena}"
            )
            return

        # Switch a escena Terminal-B en OBS antes de ejecutar
        if self._obs_connected:
            try:
                self.obs.switch_scene("Terminal-B")
            except Exception:
                pass

        self.x11.focus_window(target_wid)
        time.sleep(0.3)
        logger.info(f"Escribiendo comando en terminal B...")
        self.x11.type_text(target_wid, comando, delay_ms=self.typing_speed_ms)

        # Calcular delay basado en longitud del comando (aprox 50ms por carácter)
        tipo_delay = max(0.5, len(comando) * 0.05)
        time.sleep(tipo_delay)

        # Re-focar antes de enviar Enter para asegurar que la ventana tiene el foco
        self.x11.focus_window(target_wid)
        time.sleep(0.1)

        logger.info(f"Enviando Enter...")
        self.x11.send_key(target_wid, "Return")

        # Esperar a que el comando termine monitoreando el log
        self._wait_for_command_done(max_wait=25)

        # Adicionalmente esperar la duración del audio si lo hay
        if duracion_audio > 0:
            time.sleep(duracion_audio)

    def _handle_pausa(self, escena: dict, duracion_audio: float):
        """Maneja escenas de tipo 'pausa'."""
        espera = float(escena.get("espera", 1.0))
        time.sleep(espera)

    def _handle_menu(self, escena: dict, duracion_audio: float):
        """Maneja escenas de tipo 'menu' (Terminal A en DUAL, Terminal B en SOLO)."""
        target_wid = self.wid_a if self.mode == DirectorMode.DUAL_AI else self.wid_b

        if not target_wid:
            logger.error("Se requiere WID de Terminal para la escena 'menu'.")
            return

        if self.mode == DirectorMode.DUAL_AI and self._obs_connected:
            try:
                self.obs.switch_scene("Terminal-A")
            except Exception:
                pass

        self.x11.focus_window(target_wid)
        time.sleep(0.2)
        if "tecla" in escena:
            self.x11.send_key(target_wid, escena["tecla"])
        elif "texto" in escena:
            self.x11.type_text(
                target_wid, escena["texto"], delay_ms=self.typing_speed_ms
            )

        espera = float(escena.get("espera", 0))
        if espera > 0:
            time.sleep(espera)

    def _handle_enter(self, escena: dict, duracion_audio: float):
        """Maneja escenas de tipo 'enter'."""
        terminal = escena.get("terminal", "A").upper()
        if self.mode == DirectorMode.SOLO_TERM:
            target_wid = self.wid_b
        else:
            target_wid = self.wid_a if terminal == "A" else self.wid_b

        if not target_wid:
            logger.error(f"WID para la terminal '{terminal}' no disponible.")
            return

        self.x11.focus_window(target_wid)
        time.sleep(0.2)
        self.x11.send_key(target_wid, "Return")

        espera = float(escena.get("espera", 0))
        if espera > 0:
            time.sleep(espera)

    def _handle_leer(self, escena: dict, duracion_audio: float):
        """Maneja escenas de tipo 'leer' (marcador de posición o lectura en Terminal A/B)."""
        logger.info("Escena 'leer' encontrada.")
        espera = float(escena.get("espera", 0))
        if espera > 0:
            time.sleep(espera)

    def _handle_esperar(self, escena: dict, duracion_audio: float):
        """Maneja escenas de tipo 'esperar'."""
        logger.info(
            "Pausa manual. Esperando la intervención del usuario para continuar..."
        )
        time.sleep(duracion_audio)

    # --------------------------------------------------------------------
    # UTILIDADES
    # --------------------------------------------------------------------

    def _wait_for_command_done(self, max_wait: int = 25):
        """
        Monitorea /tmp/kr_terminal_b.log cada 0.5s.
        Retorna cuando lleva 1.5s sin cambiar (el comando terminó).
        """
        log_path = "/tmp/kr_terminal_b.log"
        if not os.path.exists(log_path):
            time.sleep(2.0)
            return

        last_size: int = -1
        stable_time: float = 0.0
        elapsed: float = 0.0

        while elapsed < max_wait:
            if self.stop_requested:
                return

            try:
                current_size = os.path.getsize(log_path)
            except OSError:
                time.sleep(0.5)
                elapsed += 0.5
                continue

            if current_size == last_size:
                stable_time += 0.5  # type: ignore[operator]
                if stable_time >= 1.5:
                    return
            else:
                stable_time = 0.0
                last_size = current_size

            time.sleep(0.5)
            elapsed += 0.5
