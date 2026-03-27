"""
action_handler.py - Controlador Central de Acciones para KR-Studio

Esta clase centraliza toda la lógica de negocio que se dispara desde la
interfaz de usuario (MainWindow). Actúa como un intermediario entre la UI
y los motores del núcleo (AIEngine, MasterDirector, etc.), promoviendo
una arquitectura de software más limpia y desacoplada.
"""

import json
import logging
import threading
from typing import TYPE_CHECKING

from kr_studio.core.master_director import MasterDirector, DirectorMode  # type: ignore
from kr_studio.core.ai_engine import AIEngine  # type: ignore
from kr_studio.core.task_manager import TaskManager, TaskType  # type: ignore

# Para evitar importaciones circulares, usamos TYPE_CHECKING
if TYPE_CHECKING:
    from kr_studio.ui.main_window import MainWindow  # type: ignore
    from kr_studio.core.vector_memory import VectorMemory  # type: ignore

logger = logging.getLogger(__name__)


class ActionHandler:
    """Maneja la lógica de todas las acciones iniciadas por el usuario en la UI."""

    def __init__(self, main_window: "MainWindow"):
        """
        Inicializa el ActionHandler.

        Args:
            main_window (MainWindow): La instancia de la ventana principal de la UI.
        """
        self.ui = main_window
        self._active_director: MasterDirector | None = None

    @property
    def ai(self) -> AIEngine:
        return self.ui.ai

    @property
    def vector_memories(self) -> dict[str, "VectorMemory"]:
        return self.ui.vector_memories

    @property
    def task_manager(self) -> TaskManager:
        return self.ui.task_manager

    def send_chat_message(self):
        """
        Inicia el proceso de generación de un guion a partir de un prompt del usuario.
        """
        user_text = self.ui.chat_entry.get().strip()
        if not user_text:
            return

        self.ui.append_chat("Tú", user_text)
        self.ui.chat_entry.delete(0, "end")
        self.ui.chat_entry.configure(state="disabled")
        self.ui.chat_btn.configure(state="disabled")
        self.ui.start_processing_animation()

        # Usar el TaskManager para ejecutar la lógica de la IA en segundo plano
        self.task_manager.submit_task(
            self._process_chat_thread, TaskType.AI_GENERATION, user_text
        )

    def _process_chat_thread(self, prompt: str):
        """
        Lógica de procesamiento del chat que se ejecuta en segundo plano.
        """
        try:
            # Obtener el tipo de contenido
            content_type = None
            if hasattr(self.ui, "configuration_panel") and hasattr(
                self.ui.configuration_panel, "content_combo"
            ):
                content_type_val = self.ui.configuration_panel.content_combo.get()
                content_type = (
                    None if content_type_val == "Por defecto" else content_type_val
                )
            else:
                # Fallback to the old way (if we haven't moved the configuration panel yet)
                content_type = self.ui.content_combo.get()
                content_type = None if content_type == "Por defecto" else content_type

            # Obtener el objetivo
            target_ip = ""
            if hasattr(self.ui, "configuration_panel") and hasattr(
                self.ui.configuration_panel, "target_combo"
            ):
                target_ip = self.ui.configuration_panel.target_combo.get()
            else:
                target_ip = self.ui.target_combo.get()

            # Obtener el modo seleccionado (DUAL AI o SOLO TERM)
            modo = "DUAL_AI"
            if hasattr(self.ui, "pre_mode_var") and self.ui.pre_mode_var:
                modo = self.ui.pre_mode_var.get()

            is_solo = modo == "SOLO TERM"
            modo_param = "SOLO_TERM" if is_solo else "DUAL_AI"

            # Obtener el formato seleccionado (9:16 o 16:9)
            formato = "9:16"
            if hasattr(self.ui, "format_combo"):
                formato_sel = self.ui.format_combo.get()
                formato = "9:16" if "9:16" in formato_sel else "16:9"
            elif hasattr(self.ui, "orchestrator_format_var"):
                formato_sel = self.ui.orchestrator_format_var.get()
                formato = "9:16" if "9:16" in formato_sel else "16:9"

            # Obtener duración y velocidad
            duration_min = 5
            typing_speed = 80
            if hasattr(self.ui, "configuration_panel"):
                if hasattr(self.ui.configuration_panel, "video_duration_min"):
                    duration_min = self.ui.configuration_panel.video_duration_min
                if hasattr(self.ui.configuration_panel, "typing_speed_pct"):
                    typing_speed = self.ui.configuration_panel.typing_speed_pct
            else:
                if hasattr(self.ui, "video_duration_min"):
                    duration_min = self.ui.video_duration_min
                if hasattr(self.ui, "typing_speed_pct"):
                    typing_speed = self.ui.typing_speed_pct

            # Obtener modo de contenido de tercero (ahora es String, no Boolean)
            third_party_content = "Desactivado"
            if hasattr(self.ui, "configuration_panel") and hasattr(
                self.ui.configuration_panel, "third_party_content_var"
            ):
                third_party_content = (
                    self.ui.configuration_panel.third_party_content_var.get()
                )
            else:
                if (
                    hasattr(self.ui, "third_party_content_var")
                    and self.ui.third_party_content_var
                ):
                    third_party_content = self.ui.third_party_content_var.get()

            # Inyectar la memoria correcta según el modo
            if content_type:
                self.ai.memory = self.vector_memories.get("marketing", self.ai.memory)
            else:
                self.ai.memory = self.vector_memories.get(
                    "guion_director", self.ai.memory
                )

            # --- Generar el proyecto ---
            final_prompt, response_text = self.ai.generar_proyecto(
                tendencia=prompt,
                objetivo_legal=target_ip,
                content_type=content_type,
                modo=modo_param,
                formato=formato,
                duration_min=duration_min,
                typing_speed=typing_speed,
                third_party_content=third_party_content,
                # Pasar la función de actualización del inspector de contexto
                context_inspector_callback=self.ui._brain_update_context_inspector,
            )

            # --- Actualizar Inspector de Contexto ---
            if hasattr(self.ui, "_brain_update_context_inspector"):
                self.ui.after(0, self.ui._brain_update_context_inspector, final_prompt)

            json_data = self.ai.extraer_json(response_text)

            if json_data:
                # --- Guardar en Memoria a Largo Plazo ---
                doc_id = f"guion_{prompt[:20].replace(' ', '_')}_{str(hash(response_text))[:6]}"
                memory_to_save_in = self.vector_memories.get(
                    "marketing" if content_type else "guion_director"
                )
                if memory_to_save_in:
                    # Guardar en un hilo para no bloquear
                    threading.Thread(
                        target=memory_to_save_in.add_document,
                        args=(
                            f"Prompt: {prompt}\n\nGuion:\n{json.dumps(json_data, indent=2)}",
                            doc_id,
                        ),
                        daemon=True,
                    ).start()

                msg = f"✅ Guion generado ({content_type or 'defecto'}) — {len(json_data)} escenas. Revisa el editor de JSON."
                self.ui.after(0, self.ui.append_chat, "DOMINION", msg)

                # Actualizar el editor de la UI desde el hilo principal
                def update_editor():
                    json_str = json.dumps(json_data, indent=4, ensure_ascii=False)
                    # Buscar el editor correcto
                    editor = None
                    # Primero intentar con los atributos directos
                    if hasattr(self.ui, "editor"):
                        editor = self.ui.editor
                    if hasattr(self.ui, "editor_b"):
                        if (
                            self.ui.pre_mode_var
                            and self.ui.pre_mode_var.get() == "SOLO TERM"
                        ):
                            editor = self.ui.editor_b
                    # Actualizar el editor
                    if editor:
                        editor.configure(state="normal")
                        editor.delete("1.0", "end")
                        editor.insert("end", json_str)
                        editor.configure(state="disabled")
                        print(f"DEBUG: Editor actualizado con {len(json_data)} escenas")
                    else:
                        print("DEBUG: No se encontró editor para actualizar")
                    # Auto guardar
                    self.ui.auto_save_project(json_data)
                    self.ui.generate_seo_metadata(prompt, json_data)

                self.ui.after(0, update_editor)
            else:
                self.ui.after(0, self.ui.append_chat, "DOMINION", response_text)

        except Exception as e:
            logger.error(f"Error en _process_chat_thread: {e}", exc_info=True)
            self.ui.after(0, self.ui.append_chat, "Error", f"❌ {str(e)}")
        finally:
            # Reactivar la UI desde el hilo principal
            def finalize_ui():
                self.ui.stop_processing_animation()
                if self.ui.chat_entry:
                    self.ui.chat_entry.configure(state="normal")
                if self.ui.chat_btn:
                    self.ui.chat_btn.configure(state="normal")

            self.ui.after(0, finalize_ui)

    def stop_director(self):
        """Detiene la ejecución del director delegando a main_window.stop_director()."""
        self.ui.stop_director()
