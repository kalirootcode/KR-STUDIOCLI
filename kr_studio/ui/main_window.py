"""
main_window.py — Interfaz Principal Profesional de KR-STUDIO
Panel dividido: Chat AI DOMINION (izquierda) + Editor JSON Pro (derecha)
Con sistema de proyectos, slider de velocidad, y UI elegante.
"""

import customtkinter as ctk  # type: ignore
import json
import threading
import os
import re
import time
import hashlib
import subprocess
import tkinter as tk
from tkinter import filedialog
import typing
from typing import cast  # type: ignore

from kr_studio.core.ai_engine import AIEngine  # type: ignore
from kr_studio.core.audio_engine import AudioEngine  # type: ignore
from kr_studio.core.workspace_manager import WorkspaceManager  # type: ignore
from kr_studio.core.task_manager import TaskManager  # type: ignore
from kr_studio.core.action_handler import ActionHandler  # type: ignore
from kr_studio.ui.floating_control import FloatingControl  # type: ignore
from kr_studio.core.video_templates import (
    get_template_list,
    get_presenter_list,
    get_audience_list,
)  # type: ignore
from kr_studio.ui.components.chat_panel import ChatPanel  # type: ignore
from kr_studio.ui.components.editor_panel import EditorPanel  # type: ignore
from kr_studio.ui.components.configuration_panel import ConfigurationPanel  # type: ignore
from kr_studio.ui.theme import COLORS, get_module_color  # type: ignore
from kr_studio.core.master_director import MasterDirector, DirectorMode  # type: ignore
from kr_studio.core.vector_memory import VectorMemory
from kr_studio.core.video_templates import (
    get_template_list,
    get_presenter_list,
    get_audience_list,
)  # type: ignore


class MainWindow(ctk.CTkFrame):  # type: ignore
    def _show_configuration_panel(self):
        """Muestra la ventana emergente de configuración global."""
        if hasattr(self, "config_window") and self.config_window:
            self.config_window.deiconify()
            self.config_window.lift()
            self.config_window.focus_force()

    def _build_configuration_panel(self):
        """Construye el panel de configuración centralizada en una ventana flotante."""
        self.config_window = ctk.CTkToplevel(self)
        self.config_window.title("⚙️ Configuración Global")
        self.config_window.geometry("500x750")
        self.config_window.withdraw()  # Ocultar al inicio
        self.config_window.protocol("WM_DELETE_WINDOW", self.config_window.withdraw)

        self.config_window.grid_rowconfigure(0, weight=1)
        self.config_window.grid_columnconfigure(0, weight=1)

        panel = ctk.CTkScrollableFrame(
            self.config_window,
            fg_color=COLORS["bg_panel"],
            corner_radius=12,
            border_width=1,
            border_color=COLORS["border"],
        )
        panel.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # ── Header ──
        header = ctk.CTkFrame(
            panel, fg_color=COLORS["header_bg"], height=42, corner_radius=0
        )
        header.pack(fill="x", pady=(0, 6))
        header.pack_propagate(False)

        ctk.CTkLabel(header, text="⚙️", font=("Arial", 18)).pack(
            side="left", padx=(12, 4)
        )
        ctk.CTkLabel(
            header,
            text="CONFIGURACIÓN CENTRALIZADA",
            font=("JetBrains Mono", 14, "bold"),
            text_color=COLORS["accent_cyan"],
        ).pack(side="left")

        # Botón de restablecer
        reset_btn = ctk.CTkButton(
            header,
            text="🔄 Restablecer",
            width=100,
            height=28,
            font=("JetBrains Mono", 10),
            fg_color="#1a1b2e",
            hover_color="#252640",
            command=self._reset_configuration_to_defaults,
        )
        reset_btn.pack(side="right", padx=(12, 4), pady=6)

        # Contenido principal
        controls = ctk.CTkFrame(panel, fg_color="transparent")
        controls.pack(fill="both", expand=True, padx=4, pady=4)

        # Configuración de video
        self._build_video_config_section(controls)

        # Parámetros de ejecución
        self._build_execution_params_section(controls)

        # Selección de objetivo
        self._build_target_section(controls)

        # Formato y Opciones
        self._build_format_options_section(controls)

        # Notas y Contenido
        self._build_notes_content_section(controls)

        # Botones de acción
        self._build_configuration_action_buttons(panel)

    def _reset_configuration_to_defaults(self):
        """Restablece todos los valores a sus valores predeterminados."""
        self._video_type_var.set("Tutorial Profundo")
        self._presenter_style_var.set("Experto Técnico")
        self._audience_var.set("Intermedio (1-3 años)")
        self.typing_speed_pct = 80
        self.video_duration_min = 5
        self.use_wrapper_var.set(False)
        self.third_party_content_var.set("Desactivado")
        self.target_combo_var.set("scanme.nmap.org")
        self.format_combo_var.set("9:16 (Vertical)")
        if hasattr(self, "_on_configuration_changed"):
            self._on_configuration_changed()

    def _build_video_config_section(self, parent):
        """Construye la sección de configuración de video."""
        section_header = ctk.CTkFrame(
            parent, fg_color="#1a1b2e", height=28, corner_radius=0
        )
        section_header.pack(fill="x", pady=(10, 10))
        section_header.pack_propagate(False)

        ctk.CTkLabel(
            section_header,
            text="🎬 CONFIGURACIÓN DE VIDEO",
            font=("JetBrains Mono", 11, "bold"),
            text_color=COLORS["accent_cyan"],
        ).pack(side="left", padx=10, pady=4)

        # Tipo de video
        video_type_row = ctk.CTkFrame(parent, fg_color="transparent")
        video_type_row.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(
            video_type_row,
            text="Tipo de Video:",
            font=("JetBrains Mono", 10, "bold"),
            text_color=COLORS["text_dim"],
        ).pack(side="left")

        templates = get_template_list()
        template_labels = [f"{t['icono']} {t['nombre']}" for t in templates]
        self._video_type_var = ctk.StringVar(
            value=template_labels[1] if len(template_labels) > 1 else template_labels[0]
        )
        self.video_type_menu = ctk.CTkOptionMenu(
            video_type_row,
            variable=self._video_type_var,
            values=template_labels,
            width=200,
            font=("JetBrains Mono", 10),
            fg_color="#1a1b2e",
            button_color=COLORS["accent_cyan"],
        )
        self.video_type_menu.pack(side="left", padx=10)

        # Estilo de presentador
        presenter_row = ctk.CTkFrame(parent, fg_color="transparent")
        presenter_row.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(
            presenter_row,
            text="Estilo Presentador:",
            font=("JetBrains Mono", 10, "bold"),
            text_color=COLORS["text_dim"],
        ).pack(side="left")

        presenters = get_presenter_list()
        presenter_labels = [p["nombre"] for p in presenters]
        self._presenter_style_var = ctk.StringVar(
            value=presenter_labels[0] if presenter_labels else ""
        )
        self.presenter_style_menu = ctk.CTkOptionMenu(
            presenter_row,
            variable=self._presenter_style_var,
            values=presenter_labels,
            width=200,
            font=("JetBrains Mono", 10),
            fg_color="#1a1b2e",
            button_color="#FF8F00",
        )
        self.presenter_style_menu.pack(side="left", padx=10)

        # Nivel de audiencia
        audience_row = ctk.CTkFrame(parent, fg_color="transparent")
        audience_row.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(
            audience_row,
            text="Nivel de Audiencia:",
            font=("JetBrains Mono", 10, "bold"),
            text_color=COLORS["text_dim"],
        ).pack(side="left")

        audiences = get_audience_list()
        audience_labels = [a["nombre"] for a in audiences]
        self._audience_var = ctk.StringVar(
            value=audience_labels[1] if len(audience_labels) > 1 else audience_labels[0]
        )
        self.audience_menu = ctk.CTkOptionMenu(
            audience_row,
            variable=self._audience_var,
            values=audience_labels,
            width=200,
            font=("JetBrains Mono", 10),
            fg_color="#1a1b2e",
            button_color="#ff3333",
        )
        self.audience_menu.pack(side="left", padx=10)

    def _build_execution_params_section(self, parent):
        """Construye la sección de parámetros de ejecución."""
        section_header = ctk.CTkFrame(
            parent, fg_color="#1a1b2e", height=28, corner_radius=0
        )
        section_header.pack(fill="x", pady=(10, 10))
        section_header.pack_propagate(False)

        ctk.CTkLabel(
            section_header,
            text="⚙️ PARÁMETROS DE EJECUCIÓN",
            font=("JetBrains Mono", 11, "bold"),
            text_color=COLORS["accent_cyan"],
        ).pack(side="left", padx=10, pady=4)

        # Modo de ejecución
        mode_row = ctk.CTkFrame(parent, fg_color="transparent")
        mode_row.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(
            mode_row,
            text="Modo de Ejecución:",
            font=("JetBrains Mono", 10, "bold"),
            text_color=COLORS["text_dim"],
        ).pack(side="left")

        # Use pre_mode_var if it exists (from chat panel), otherwise create new
        if hasattr(self, "pre_mode_var") and self.pre_mode_var:
            self.mode_var = self.pre_mode_var
        else:
            self.mode_var = ctk.StringVar(value="DUAL AI")

        self.mode_selector = ctk.CTkOptionMenu(
            mode_row,
            variable=self.mode_var,
            values=["DUAL AI", "SOLO TERM"],
            width=140,
            font=("JetBrains Mono", 10),
            fg_color="#1a1b2e",
            button_color=COLORS["accent_cyan"],
        )
        self.mode_selector.pack(side="left", padx=10)

        # Velocidad de tipeo
        speed_row = ctk.CTkFrame(parent, fg_color="transparent")
        speed_row.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(
            speed_row,
            text="Velocidad de Tipeo:",
            font=("JetBrains Mono", 10, "bold"),
            text_color=COLORS["text_dim"],
        ).pack(side="left")

        self.speed_slider = ctk.CTkSlider(
            speed_row,
            from_=50,
            to=200,
            number_of_steps=15,
            width=140,
            fg_color=COLORS["border"],
            progress_color=COLORS["accent_cyan"],
            button_color=COLORS["accent_cyan"],
            command=self._on_speed_change,
        )
        self.speed_slider.set(80)
        self.speed_slider.pack(side="left", padx=10)

        self.speed_label = ctk.CTkLabel(
            speed_row,
            text="80%",
            font=("JetBrains Mono", 10, "bold"),
            text_color=COLORS["accent_cyan"],
        )
        self.speed_label.pack(side="left")

        # Duración del video
        dur_row = ctk.CTkFrame(parent, fg_color="transparent")
        dur_row.pack(fill="x", padx=10, pady=(10, 5))

        ctk.CTkLabel(
            dur_row,
            text="Duración Video:",
            font=("JetBrains Mono", 10, "bold"),
            text_color=COLORS["text_dim"],
        ).pack(side="left")

        self.duration_slider = ctk.CTkSlider(
            dur_row,
            from_=1,
            to=30,
            number_of_steps=29,
            width=140,
            fg_color=COLORS["border"],
            progress_color="#FF8F00",
            button_color="#FF8F00",
            command=self._on_duration_change,
        )
        self.duration_slider.set(5)
        self.duration_slider.pack(side="left", padx=10)

        self.duration_label = ctk.CTkLabel(
            dur_row,
            text="5 min",
            font=("JetBrains Mono", 10, "bold"),
            text_color="#FF8F00",
        )
        self.duration_label.pack(side="left")

        # Wrapper KR-CLI
        self.wrapper_check = ctk.CTkCheckBox(
            parent,
            text="🔲 KR-CLI Wrapper (Terminal B)",
            variable=self.use_wrapper_var,
            font=("JetBrains Mono", 10),
            text_color=COLORS["text_dim"],
            fg_color=COLORS["accent_red"],
            hover_color="#9c27b0",
            checkbox_width=18,
            checkbox_height=18,
        )
        self.wrapper_check.pack(anchor="w", padx=10, pady=(10, 5))

        # Contenido de Tercero (Dropdown)
        third_party_label = ctk.CTkLabel(
            parent,
            text="🎬 Contenido de Tercero:",
            font=("JetBrains Mono", 10),
            text_color=COLORS["text_dim"],
        )
        third_party_label.pack(anchor="w", padx=10, pady=(5, 2))

        self.third_party_menu = ctk.CTkOptionMenu(
            parent,
            variable=self.third_party_content_var,
            values=[
                "Desactivado",
                "Contenido Mixto (Videos + Terminal)",
                "Contenido Puro (Terminal)",
            ],
            width=200,
            font=("JetBrains Mono", 10),
            fg_color="#1a1b2e",
            button_color=COLORS["accent_yellow"],
        )
        self.third_party_menu.pack(anchor="w", padx=10, pady=(0, 5))

    def _build_target_section(self, parent):
        """Construye la sección de objetivo y target."""
        section_header = ctk.CTkFrame(
            parent, fg_color="#1a1b2e", height=28, corner_radius=0
        )
        section_header.pack(fill="x", pady=(10, 10))
        section_header.pack_propagate(False)

        ctk.CTkLabel(
            section_header,
            text="🎯 OBJETIVO Y TARGET",
            font=("JetBrains Mono", 11, "bold"),
            text_color=COLORS["accent_cyan"],
        ).pack(side="left", padx=10, pady=4)

        # Selector de IP/Target
        target_row = ctk.CTkFrame(parent, fg_color="transparent")
        target_row.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(
            target_row,
            text="IP/Target:",
            font=("JetBrains Mono", 10, "bold"),
            text_color=COLORS["text_dim"],
        ).pack(side="left")

        self.target_combo_var = ctk.StringVar(value="scanme.nmap.org")
        self.target_combo = ctk.CTkComboBox(
            target_row,
            variable=self.target_combo_var,
            width=200,
            height=28,
            values=[
                "scanme.nmap.org",
                "testphp.vulnweb.com",
                "httpbin.org",
                "badssl.com",
                "rest.vulnweb.com",
                "IP Personalizada",
            ],
            font=("JetBrains Mono", 11),
            fg_color=COLORS["bg_dark"],
            border_color=COLORS["border"],
            dropdown_fg_color=COLORS["bg_dark"],
        )
        self.target_combo.pack(side="left", padx=10)

    def _build_format_options_section(self, parent):
        """Construye la sección de formato y opciones."""
        section_header = ctk.CTkFrame(
            parent, fg_color="#1a1b2e", height=28, corner_radius=0
        )
        section_header.pack(fill="x", pady=(10, 10))
        section_header.pack_propagate(False)

        ctk.CTkLabel(
            section_header,
            text="📐 FORMATO Y OPCIONES",
            font=("JetBrains Mono", 11, "bold"),
            text_color=COLORS["accent_cyan"],
        ).pack(side="left", padx=10, pady=4)

        # Formato de video
        format_row = ctk.CTkFrame(parent, fg_color="transparent")
        format_row.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(
            format_row,
            text="Formato de Video:",
            font=("JetBrains Mono", 10, "bold"),
            text_color=COLORS["text_dim"],
        ).pack(side="left")

        self.format_combo_var = ctk.StringVar(value="9:16 (Vertical)")
        self.format_combo = ctk.CTkOptionMenu(
            format_row,
            variable=self.format_combo_var,
            values=["9:16 (Vertical)", "16:9 (Horizontal)"],
            width=200,
            font=("JetBrains Mono", 11),
            fg_color=COLORS["border"],
            button_color=COLORS["accent_red"],
            button_hover_color="#9c27b0",
        )
        self.format_combo.pack(side="left", padx=10)

    def _build_notes_content_section(self, parent):
        """Construye la sección de notas y contenido."""
        section_header = ctk.CTkFrame(
            parent, fg_color="#1a1b2e", height=28, corner_radius=0
        )
        section_header.pack(fill="x", pady=(10, 10))
        section_header.pack_propagate(False)

        ctk.CTkLabel(
            section_header,
            text="📝 NOTAS Y CONTENIDO",
            font=("JetBrains Mono", 11, "bold"),
            text_color=COLORS["accent_cyan"],
        ).pack(side="left", padx=10, pady=4)

        # Tipo de contenido
        content_row = ctk.CTkFrame(parent, fg_color="transparent")
        content_row.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(
            content_row,
            text="Tipo de Contenido:",
            font=("JetBrains Mono", 10, "bold"),
            text_color=COLORS["text_dim"],
        ).pack(side="left")

        content_types = ["Por defecto"] + [t["key"] for t in get_template_list()]
        self.content_combo = ctk.CTkOptionMenu(
            content_row,
            values=content_types,
            width=200,
            font=("JetBrains Mono", 11),
            fg_color=COLORS["border"],
            button_color=COLORS["accent_yellow"],
            button_hover_color="#e6b800",
        )
        self.content_combo.set("Por defecto")
        self.content_combo.pack(side="left", padx=10)

        # Notas adicionales
        notes_row = ctk.CTkFrame(parent, fg_color="transparent")
        notes_row.pack(fill="x", padx=10, pady=(10, 5))

        ctk.CTkLabel(
            notes_row,
            text="Notas para la IA:",
            font=("JetBrains Mono", 9),
            text_color="#555577",
        ).pack(side="left")

        self._extra_notes_text = ctk.CTkTextbox(
            notes_row,
            height=60,
            font=("JetBrains Mono", 10),
            fg_color="#080810",
            border_color=COLORS["border"],
            border_width=1,
        )
        self._extra_notes_text.pack(side="left", fill="x", expand=True, padx=10)
        self._extra_notes_text.bind("<FocusOut>", lambda e: self._save_extra_notes())

    def _save_extra_notes(self):
        """Guarda las notas adicionales."""
        if hasattr(self, "_extra_notes_text"):
            self._extra_notes = self._extra_notes_text.get("1.0", "end-1c")
        if hasattr(self, "_on_configuration_changed"):
            self._on_configuration_changed()

    def _build_configuration_action_buttons(self, parent):
        """Construye los botones de acción del panel de configuración."""
        button_frame = ctk.CTkFrame(parent, fg_color="transparent")
        button_frame.pack(fill="x", padx=10, pady=10)

        # Botón guardar configuración
        save_config_btn = ctk.CTkButton(
            button_frame,
            text="💾 Guardar Configuración",
            command=self._save_configuration,
            font=("JetBrains Mono", 11, "bold"),
            height=35,
            fg_color="#1a1b2e",
            hover_color="#252640",
            border_width=1,
            border_color=COLORS["accent_cyan"],
        )
        save_config_btn.pack(side="left", expand=True, fill="x", padx=(0, 5))

        # Botón aplicar configuración
        apply_btn = ctk.CTkButton(
            button_frame,
            text="✅ Aplicar Configuración",
            command=self._apply_configuration,
            font=("JetBrains Mono", 11, "bold"),
            height=35,
            fg_color=COLORS["accent_cyan"],
            hover_color="#00ACC1",
            text_color="#000000",
        )
        apply_btn.pack(side="right", expand=True, fill="x", padx=(5, 0))

    def _save_configuration(self):
        """Guarda la configuración actual en un archivo."""
        config_data = {
            "video_type": getattr(self, "_video_type_var", ctk.StringVar()).get(),
            "presenter_style": getattr(
                self, "_presenter_style_var", ctk.StringVar()
            ).get(),
            "audience": getattr(self, "_audience_var", ctk.StringVar()).get(),
            "typing_speed_pct": getattr(self, "typing_speed_pct", 80),
            "video_duration_min": getattr(self, "video_duration_min", 5),
            "use_wrapper": getattr(self, "use_wrapper_var", ctk.BooleanVar()).get(),
            "third_party_content": getattr(
                self, "third_party_content_var", ctk.StringVar(value="Desactivado")
            ).get(),
            "target": getattr(self, "target_combo_var", ctk.StringVar()).get(),
            "format": getattr(self, "format_combo_var", ctk.StringVar()).get(),
            "content_type": getattr(self, "content_combo", None).get()
            if hasattr(self, "content_combo") and self.content_combo
            else "Por defecto",
            "extra_notes": getattr(self, "_extra_notes", ""),
        }
        try:
            config_path = os.path.join(self.workspace_dir, "configuration.json")
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            self.append_chat("Sistema", "✅ Configuración guardada")
        except Exception as e:
            self.append_chat("Error", f"❌ Error al guardar configuración: {str(e)}")

    def _load_saved_configuration(self):
        """Carga la configuración guardada desde archivo."""
        try:
            config_path = os.path.join(self.workspace_dir, "configuration.json")
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
                if hasattr(self, "_video_type_var") and "video_type" in config_data:
                    self._video_type_var.set(config_data["video_type"])
                if (
                    hasattr(self, "_presenter_style_var")
                    and "presenter_style" in config_data
                ):
                    self._presenter_style_var.set(config_data["presenter_style"])
                if hasattr(self, "_audience_var") and "audience" in config_data:
                    self._audience_var.set(config_data["audience"])
                if "typing_speed_pct" in config_data and hasattr(self, "speed_slider"):
                    self.typing_speed_pct = config_data["typing_speed_pct"]
                    self.speed_slider.set(self.typing_speed_pct)
                    self.speed_label.configure(text=f"{self.typing_speed_pct}%")
                if "video_duration_min" in config_data and hasattr(
                    self, "duration_slider"
                ):
                    self.video_duration_min = config_data["video_duration_min"]
                    self.duration_slider.set(self.video_duration_min)
                    self.duration_label.configure(text=f"{self.video_duration_min} min")
                if hasattr(self, "use_wrapper_var") and "use_wrapper" in config_data:
                    self.use_wrapper_var.set(config_data["use_wrapper"])
                if (
                    hasattr(self, "third_party_content_var")
                    and "third_party_content" in config_data
                ):
                    value = config_data["third_party_content"]
                    if value in [
                        "Desactivado",
                        "Contenido Mixto (Videos + Terminal)",
                        "Contenido Puro (Terminal)",
                    ]:
                        self.third_party_content_var.set(value)
        except Exception as e:
            print(f"Advertencia: No se pudo cargar configuración guardada: {e}")

    def _apply_configuration(self):
        """Aplica la configuración actual a la instancia principal de la aplicación."""
        self._load_saved_configuration()
        if hasattr(self, "_on_configuration_changed"):
            self._on_configuration_changed()
        self.append_chat("Sistema", "✅ Configuración aplicada")

    def get_current_configuration(self):
        """Retorna la configuración actual como diccionario."""
        return {
            "video_type": getattr(self, "_video_type_var", ctk.StringVar()).get(),
            "presenter_style": getattr(
                self, "_presenter_style_var", ctk.StringVar()
            ).get(),
            "audience": getattr(self, "_audience_var", ctk.StringVar()).get(),
            "typing_speed_pct": getattr(self, "typing_speed_pct", 80),
            "video_duration_min": getattr(self, "video_duration_min", 5),
            "use_wrapper": getattr(self, "use_wrapper_var", ctk.BooleanVar()).get(),
            "third_party_content": getattr(
                self, "third_party_content_var", ctk.StringVar(value="Desactivado")
            ).get(),
            "target": getattr(self, "target_combo_var", ctk.StringVar()).get(),
            "format": getattr(self, "format_combo_var", ctk.StringVar()).get(),
            "content_type": getattr(self, "content_combo", None).get()
            if hasattr(self, "content_combo") and self.content_combo
            else "Por defecto",
            "extra_notes": getattr(self, "_extra_notes", ""),
        }

    def __init__(self, master_app):
        print("DEBUG: MainWindow.__init__ start", flush=True)
        super().__init__(master_app, fg_color=COLORS["bg_dark"])  # type: ignore
        print("DEBUG: After super().__init__", flush=True)
        self.master_app = master_app
        print("DEBUG: After setting master_app", flush=True)
        self.pack(fill="both", expand=True)
        print("DEBUG: After pack", flush=True)

        self._base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self._env_path = os.path.join(os.path.dirname(self._base_dir), ".env")
        print("DEBUG: _base_dir and _env_path set", flush=True)

        # Inicializar los motores y gestores principales
        self.task_manager = TaskManager()
        print("DEBUG: TaskManager created", flush=True)

        # Inicializar la Súper Memoria de la IA - Director Maestro
        self.vector_memories = {}
        compartments = [
            "conocimiento",  # Conocimiento general del nicho
            "marketing",  # Estrategias de marketing y viralidad
            "plantillas",  # Templates de contenido
            "generado",  # Contenido generado (se auto-guarda)
            "cursos",  # Contenido para cursos (Hotmart, Udemy)
            "series",  # Series de videos/posts
        ]
        for comp in compartments:
            self.vector_memories[comp] = VectorMemory(
                db_path="kr_studio_memory", compartments=[comp]
            )
        saved_key = self._load_env_key()
        self.ai = AIEngine(saved_key, vector_memories=self.vector_memories)
        print("DEBUG: AIEngine created", flush=True)
        self.action_handler = ActionHandler(self)
        print("DEBUG: ActionHandler created", flush=True)
        self.workspace_dir = os.path.join(self._base_dir, "workspace")
        self.projects_dir = os.path.join(self._base_dir, "projects")
        print("DEBUG: workspace and projects dirs set", flush=True)
        os.makedirs(self.workspace_dir, exist_ok=True)
        os.makedirs(self.projects_dir, exist_ok=True)
        print("DEBUG: dirs created", flush=True)

        # Cargar preferencias guardadas
        self.typing_speed_pct = 70
        self.video_duration_min = 5
        print("DEBUG: About to load UI preferences", flush=True)
        self._load_ui_preferences()
        print("DEBUG: UI preferences loaded", flush=True)

        # Variables de estado
        self.wid_a: typing.Optional[int] = None
        self.wid_b: typing.Optional[int] = None
        self._anim_id = None
        self._floating_ctrl: typing.Optional[FloatingControl] = None
        self._create_floating_control()
        self._active_director: typing.Optional[MasterDirector] = None
        print("DEBUG: Misc variables initialized", flush=True)

        # Configuración variables (will be initialized in _build_configuration_panel)
        self._video_type_var: typing.Any = None
        self._presenter_style_var: typing.Any = None
        self._audience_var: typing.Any = None
        self.typing_speed_pct: int = 80  # default, will be overridden by UI
        self.video_duration_min: int = 5  # default, will be overridden by UI
        self.use_wrapper_var: typing.Any = None
        self.third_party_content_var: typing.Any = None
        self.target_combo_var: typing.Any = None
        self.format_combo_var: typing.Any = None
        self.content_combo: typing.Any = None
        self._extra_notes: str = ""
        self._extra_notes_text: typing.Any = None
        # Callback for configuration changes
        self._on_configuration_changed = lambda: None
        # Auto-save related
        self._auto_save_after_id: typing.Optional[str] = None
        self._auto_save_delay_ms = 2000  # 2 seconds

        # Orquestadores
        from kr_studio.core.series_orchestrator import SeriesOrchestrator  # type: ignore
        from kr_studio.core.course_engine import CourseOrchestrator  # type: ignore

        self.series_orchestrator = SeriesOrchestrator(self.ai, self.workspace_dir)  # type: ignore
        self.course_orchestrator = CourseOrchestrator(self.ai, self.workspace_dir)  # type: ignore

        # Estado adicional
        self.timestamps: typing.Dict[str, typing.Any] = {}
        self._raw_video_path: typing.Optional[str] = None
        self.pre_mode_var: typing.Optional[ctk.StringVar] = (
            None  # Se crea en _build_chat_panel
        )
        # use_wrapper_var se crea en _build_editor_panel, pero ya tenemos una variable arriba (se sobrescribirá)

        # ─── LAYOUT: API Bar + Tabview ───
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Cargar API Key anticipadamente para evitar "flashing"
        saved_key = self._load_env_key()
        is_api_valid = False

        self._build_api_bar()

        if saved_key:
            try:
                self.ai = AIEngine(saved_key)
                self.api_entry.insert(0, saved_key)
                is_api_valid = True
                # Si es válida, la ocultamos de inmediato
                self._api_bar.grid_forget()
            except Exception:
                is_api_valid = False

        print("DEBUG: API bar built", flush=True)

        # ── CTkTabview ──
        self.tabview = ctk.CTkTabview(
            self,
            fg_color=COLORS["bg_dark"],
            segmented_button_fg_color=COLORS["bg_panel"],
            segmented_button_selected_color="#0D47A1",  # Azul oscuro elegante
            segmented_button_selected_hover_color="#1565C0",
            segmented_button_unselected_color="#1a1b2e",  # Fondo panel oscuro
            segmented_button_unselected_hover_color="#252640",
            text_color="#ffffff",  # Blanco para que siempre se vea bien
            corner_radius=8,
        )
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=6, pady=(0, 6))
        print("DEBUG: Tabview created", flush=True)

        self.tab1 = self.tabview.add("🎬 Guion y Director")
        self.tab2 = self.tabview.add("🎬 Orquestador de Series")
        self.tab3 = self.tabview.add("🎙 Estudio TTS")
        self.tab4 = self.tabview.add("🚀 Marketing Studio")
        self.tab_brain = self.tabview.add("🧠 Cerebro de la IA")
        self.tab6 = self.tabview.add("🧠 Opencode")
        print("DEBUG: Tabs added", flush=True)

        # Tab 1 layout
        self.tab1.grid_columnconfigure(0, weight=3)  # Panel izquierdo (Chat)
        self.tab1.grid_columnconfigure(
            1, weight=5
        )  # Panel central (Editor) = mucho más ancho
        self.tab1.grid_columnconfigure(
            2, weight=2
        )  # Panel derecho (Config) = más angosto
        self.tab1.grid_rowconfigure(0, weight=1)

        self._build_chat_panel()
        self._build_editor_panel()

        # Tab 2 layout
        self._build_postprod_tab()

        # Tab 3 — Estudio TTS
        self.tab3.grid_rowconfigure(1, weight=1)
        self.tab3.grid_columnconfigure(0, weight=1)
        self.tab3.grid_columnconfigure(1, weight=2)
        self._build_tts_studio()

        # Tab 4 — Marketing Studio
        self.tab4.grid_rowconfigure(0, weight=1)
        # El grid de 3 columnas se configura dentro de _build_marketing_studio

        self._build_marketing_studio()

        # Tab Cerebro de la IA
        self._build_brain_tab()

        # Opencode tab layout
        self.tab6.grid_rowconfigure(0, weight=1)
        self.tab6.grid_columnconfigure(0, weight=1)
        self._build_opencode_tab()

        # Configuración Global (Ventana emergente)
        self._build_configuration_panel()

        # Botón de engranaje global en la esquina superior derecha
        self.btn_open_config = ctk.CTkButton(
            self,
            text="⚙️",
            width=36,
            height=36,
            corner_radius=8,
            fg_color=COLORS["bg_panel"],
            hover_color=COLORS["gray_medium"],
            text_color="#ffffff",
            font=("Arial", 18),
            command=self._show_configuration_panel,
        )
        self.btn_open_config.place(relx=1.0, rely=0.0, x=-20, y=10, anchor="ne")

        # ─── POSICIONAR VENTANA ───

    def _build_brain_tab(self):
        """
        Construye la pestaña 'Cerebro de la IA' con 3 paneles:
        1. Gestor de Memoria (Izquierda)
        2. Chat de Conocimiento (Centro)
        3. Inspector de Contexto (Derecha)
        """
        # Configurar el grid principal de la pestaña
        self.tab_brain.grid_columnconfigure(0, weight=2)  # Gestor de Memoria
        self.tab_brain.grid_columnconfigure(1, weight=3)  # Chat
        self.tab_brain.grid_columnconfigure(2, weight=2)  # Inspector
        self.tab_brain.grid_rowconfigure(0, weight=1)

        # ════════════════════════════════════════
        # PANEL IZQUIERDO — Gestor de Memoria
        # ════════════════════════════════════════
        memory_panel = ctk.CTkFrame(
            self.tab_brain,
            fg_color=COLORS["bg_panel"],
            corner_radius=10,
            border_width=1,
            border_color=COLORS["border"],
        )
        memory_panel.grid(row=0, column=0, sticky="nsew", padx=(8, 4), pady=8)
        memory_panel.grid_rowconfigure(2, weight=1)
        memory_panel.grid_columnconfigure(0, weight=1)

        # Header
        memory_header = ctk.CTkFrame(
            memory_panel, fg_color=COLORS["header_bg"], height=40
        )
        memory_header.grid(row=0, column=0, sticky="ew")
        ctk.CTkLabel(
            memory_header,
            text="🗄️ GESTOR DE MEMORIA",
            font=("JetBrains Mono", 12, "bold"),
            text_color="#1E88E5",
        ).pack(side="left", padx=12)

        # Controles de gestión
        memory_controls_frame = ctk.CTkFrame(memory_panel, fg_color="transparent")
        memory_controls_frame.grid(row=1, column=0, sticky="ew", padx=8, pady=8)
        memory_controls_frame.grid_columnconfigure(0, weight=1)
        memory_controls_frame.grid_columnconfigure(1, weight=1)

        # Selector de Compartimentos - ocupa toda la fila
        self.brain_compartment_selector = ctk.CTkComboBox(
            memory_controls_frame,
            values=list(self.vector_memories.keys()),
            height=28,
            font=("JetBrains Mono", 10),
            fg_color="#1a1b2e",
            command=self._brain_update_memory_viewer,
        )
        self.brain_compartment_selector.grid(
            row=0, column=0, columnspan=2, sticky="ew", pady=(0, 6)
        )

        # Fila de acciones principales
        self.brain_load_btn = ctk.CTkButton(
            memory_controls_frame,
            text="📂 Cargar Archivo",
            command=self._brain_load_file_to_memory,
        )
        self.brain_load_btn.grid(row=1, column=0, sticky="ew", padx=(0, 3))

        self.brain_batch_load_btn = ctk.CTkButton(
            memory_controls_frame,
            text="🗂 Batch Cargar",
            command=self._brain_batch_load_to_memory,
        )
        self.brain_batch_load_btn.grid(row=1, column=1, sticky="ew", padx=(3, 0))

        self.brain_clear_btn = ctk.CTkButton(
            memory_controls_frame,
            text="💥 Limpiar",
            fg_color="#D32F2F",
            hover_color="#C62828",
            command=self._brain_clear_compartment,
        )
        self.brain_clear_btn.grid(
            row=2, column=0, columnspan=2, sticky="ew", pady=(6, 0)
        )

        # Eliminar por ID
        del_frame = ctk.CTkFrame(memory_controls_frame, fg_color="transparent")
        del_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        self.brain_delete_docid = ctk.CTkEntry(
            del_frame,
            font=("JetBrains Mono", 11),
            placeholder_text="Doc ID a eliminar...",
        )
        self.brain_delete_docid.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.brain_delete_btn = ctk.CTkButton(
            del_frame,
            text="🗑 Eliminar Doc",
            width=120,
            command=self._brain_delete_document,
        )
        self.brain_delete_btn.pack(side="left")

        # Visor de Documentos
        self.brain_memory_viewer = ctk.CTkTextbox(
            memory_panel,
            font=("JetBrains Mono", 10),
            wrap="word",
            fg_color=COLORS["bg_editor"],
            border_width=0,
        )
        self.brain_memory_viewer.grid(
            row=2, column=0, sticky="nsew", padx=8, pady=(0, 8)
        )

        # Carga inicial de documentos
        self.after(1000, lambda: self._brain_update_memory_viewer(None))

        # ════════════════════════════════════════
        # PANEL CENTRAL — Chat de Conocimiento
        # ════════════════════════════════════════
        chat_panel = ctk.CTkFrame(
            self.tab_brain,
            fg_color=COLORS["bg_panel"],
            corner_radius=10,
            border_width=1,
            border_color=COLORS["border"],
        )
        chat_panel.grid(row=0, column=1, sticky="nsew", padx=4, pady=8)
        chat_panel.grid_rowconfigure(1, weight=1)
        chat_panel.grid_columnconfigure(0, weight=1)

        # Header
        chat_header = ctk.CTkFrame(chat_panel, fg_color=COLORS["header_bg"], height=40)
        chat_header.grid(row=0, column=0, sticky="ew")
        ctk.CTkLabel(
            chat_header,
            text="💬 CHAT DE CONOCIMIENTO",
            font=("JetBrains Mono", 12, "bold"),
            text_color="#D81B60",
        ).pack(side="left", padx=12)

        # Historial de chat
        self.brain_chat_history = ctk.CTkTextbox(
            chat_panel,
            font=("JetBrains Mono", 10),
            wrap="word",
            fg_color=COLORS["bg_editor"],
            border_width=0,
        )
        self.brain_chat_history.grid(row=1, column=0, sticky="nsew", padx=8, pady=8)
        self.brain_chat_history.insert(
            "1.0", "Pregúntale a la IA sobre lo que ha aprendido..."
        )

        # Entrada de chat
        chat_input_frame = ctk.CTkFrame(chat_panel, fg_color="transparent")
        chat_input_frame.grid(row=2, column=0, sticky="ew", padx=8, pady=(0, 8))
        chat_input_frame.grid_columnconfigure(0, weight=1)
        self.brain_chat_entry = ctk.CTkEntry(
            chat_input_frame,
            placeholder_text="Escribe tu pregunta sobre el conocimiento de la IA...",
            font=("JetBrains Mono", 11),
        )
        self.brain_chat_entry.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        self.brain_chat_entry.bind("<Return>", self._brain_on_send_chat)

        self.brain_chat_send_btn = ctk.CTkButton(
            chat_input_frame,
            text="Enviar",
            width=80,
            command=self._brain_on_send_chat,
        )
        self.brain_chat_send_btn.grid(row=0, column=1)

        # ════════════════════════════════════════
        # PANEL DERECHO — Inspector de Contexto
        # ════════════════════════════════════════
        inspector_panel = ctk.CTkFrame(
            self.tab_brain,
            fg_color=COLORS["bg_panel"],
            corner_radius=10,
            border_width=1,
            border_color=COLORS["border"],
        )
        inspector_panel.grid(row=0, column=2, sticky="nsew", padx=(4, 8), pady=8)
        inspector_panel.grid_rowconfigure(1, weight=1)
        inspector_panel.grid_columnconfigure(0, weight=1)

        # Header
        inspector_header = ctk.CTkFrame(
            inspector_panel, fg_color=COLORS["header_bg"], height=40
        )
        inspector_header.grid(row=0, column=0, sticky="ew")
        ctk.CTkLabel(
            inspector_header,
            text="🔍 INSPECTOR DE CONTEXTO",
            font=("JetBrains Mono", 12, "bold"),
            text_color="#FFB300",
        ).pack(side="left", padx=12)

        # Visor de contexto
        self.brain_context_viewer = ctk.CTkTextbox(
            inspector_panel,
            font=("JetBrains Mono", 9),
            wrap="word",
            fg_color=COLORS["bg_editor"],
            border_width=0,
        )
        self.brain_context_viewer.grid(row=1, column=0, sticky="nsew", padx=8, pady=8)
        self.brain_context_viewer.insert(
            "1.0",
            "Aquí se mostrará el contexto en tiempo real antes de cada generación...",
        )

        # ─── POSICIONAR VENTANA ───

        # ─── POSICIONAR VENTANA ───

        # Maximizar ventana según OS sin forzar geometrías contradictorias
        try:
            self.master_app.state("zoomed")  # Windows / algunos Linux
        except Exception:
            try:
                self.master_app.attributes("-zoomed", True)  # Alternativa Linux X11
            except Exception:
                # Fallback solo si los métodos nativos fallan
                sw = self.master_app.winfo_screenwidth()
                sh = self.master_app.winfo_screenheight()
                self.master_app.geometry(f"{sw}x{sh}+0+0")

        # Forzamos actualización visual una sola vez al final del layout
        self.master_app.update_idletasks()

        # Auto-cargar API Key desde .env
        if hasattr(self, "api_entry") and getattr(self, "api_entry").get():
            # La API key ya se cargó y configuró al principio de __init__
            self.append_chat(
                "Sistema",
                "Bienvenido a KR-STUDIO 🎬\nAPI Key cargada desde .env — DOMINION listo.",
            )
        else:
            self.append_chat(
                "Sistema",
                "Bienvenido a KR-STUDIO 🎬\nIDE de Producción de Videos — DOMINION Edition\nIngresa tu API Key para comenzar.",
            )

        # Deferimos el lanzamiento de Konsole a la interaccion del usuario.

    def _create_floating_control(self):
        """Crea el mini control flotante."""
        self._floating_ctrl = FloatingControl(self)

    # ═══════════════════════════════════════════════
    # CONSTRUCCIÓN DE PANELES
    # ═══════════════════════════════════════════════

    def _build_api_bar(self):
        """Barra superior de API Key (se oculta tras guardar)."""
        self._api_bar = ctk.CTkFrame(
            self, fg_color=COLORS["header_bg"], height=50, corner_radius=0
        )
        self._api_bar.grid(row=0, column=0, columnspan=2, sticky="ew")
        self._api_bar.grid_propagate(False)

        lbl = ctk.CTkLabel(
            self._api_bar,
            text="🔑 API KEY",
            font=("JetBrains Mono", 12, "bold"),
            text_color=COLORS["accent_cyan"],
        )
        lbl.pack(side="left", padx=(15, 8))

        self.api_entry = ctk.CTkEntry(
            self._api_bar,
            width=350,
            show="*",
            placeholder_text="Gemini API Key...",
            font=("JetBrains Mono", 12),
            fg_color=COLORS["bg_dark"],
            border_color=COLORS["border"],
        )
        self.api_entry.pack(side="left", padx=5, fill="x", expand=True)

        self.api_btn = ctk.CTkButton(
            self._api_bar,
            text="Conectar",
            width=90,
            command=self.save_api_key,
            font=("JetBrains Mono", 12, "bold"),
            fg_color=COLORS["accent_cyan"],
            text_color="#000000",
            hover_color="#00b8d4",
        )
        self.api_btn.pack(side="left", padx=(5, 15))

    def _build_chat_panel(self):
        """Panel izquierdo — Chat AI DOMINION."""
        panel = ctk.CTkFrame(
            self.tab1,
            fg_color=COLORS["bg_panel"],
            corner_radius=12,
            border_width=1,
            border_color=COLORS["border"],
        )
        panel.grid(row=0, column=0, sticky="nsew", padx=(8, 4), pady=8)

        # Header estilizado
        header = ctk.CTkFrame(
            panel, fg_color=COLORS["header_bg"], height=48, corner_radius=0
        )
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(header, text="🧠", font=("Arial", 20)).pack(
            side="left", padx=(12, 4)
        )
        ctk.CTkLabel(
            header,
            text="DOMINION AI",
            font=("JetBrains Mono", 14, "bold"),
            text_color=COLORS["accent_cyan"],
        ).pack(side="left")

        # Indicador de estado
        self.status_label = ctk.CTkLabel(
            header,
            text="● EN LÍNEA",
            font=("JetBrains Mono", 10),
            text_color=COLORS["accent_green"],
        )
        self.status_label.pack(side="right", padx=12)

        # ─── METADATA SECTION ───
        meta_frame = ctk.CTkFrame(panel, fg_color="transparent")
        meta_frame.pack(fill="x", padx=6, pady=4)

        # Título
        ctk.CTkLabel(
            meta_frame,
            text="Título:",
            font=("JetBrains Mono", 10, "bold"),
            text_color=COLORS["text_dim"],
        ).grid(row=0, column=0, sticky="w", pady=2)
        self.meta_title = ctk.CTkEntry(
            meta_frame,
            font=("JetBrains Mono", 11),
            fg_color=COLORS["bg_dark"],
            border_color=COLORS["border"],
            height=28,
        )
        self.meta_title.grid(row=0, column=1, sticky="ew", padx=4, pady=2)

        # Descripción
        ctk.CTkLabel(
            meta_frame,
            text="Desc:",
            font=("JetBrains Mono", 10, "bold"),
            text_color=COLORS["text_dim"],
        ).grid(row=1, column=0, sticky="nw", pady=2)
        self.meta_desc = ctk.CTkTextbox(
            meta_frame,
            font=("JetBrains Mono", 11),
            fg_color=COLORS["bg_dark"],
            border_color=COLORS["border"],
            border_width=1,
            height=50,
        )
        self.meta_desc.grid(row=1, column=1, sticky="ew", padx=4, pady=2)

        # Hashtags
        ctk.CTkLabel(
            meta_frame,
            text="Tags:",
            font=("JetBrains Mono", 10, "bold"),
            text_color=COLORS["text_dim"],
        ).grid(row=2, column=0, sticky="w", pady=2)
        self.meta_tags = ctk.CTkEntry(
            meta_frame,
            font=("JetBrains Mono", 11),
            fg_color=COLORS["bg_dark"],
            border_color=COLORS["border"],
            height=28,
            text_color=COLORS["accent_cyan"],
        )
        self.meta_tags.grid(row=2, column=1, sticky="ew", padx=4, pady=2)

        meta_frame.grid_columnconfigure(1, weight=1)

        # Chat display - más alto para mejor visualización
        self.chat_display = ctk.CTkTextbox(
            panel,
            wrap="word",
            font=("JetBrains Mono", 12),
            fg_color=COLORS["bg_chat"],
            text_color=COLORS["text_primary"],
            state="disabled",
            border_width=0,
            height=350,
        )
        self.chat_display.pack(fill="both", expand=True, padx=6, pady=(4, 4))

        # Configurar tags de colores para mensajes
        self.chat_display._textbox.tag_config(
            "sender_system", foreground=COLORS["accent_yellow"]
        )
        self.chat_display._textbox.tag_config(
            "sender_user", foreground=COLORS["accent_cyan"]
        )
        self.chat_display._textbox.tag_config(
            "sender_ai", foreground=COLORS["accent_green"]
        )
        self.chat_display._textbox.tag_config(
            "sender_error", foreground=COLORS["accent_red"]
        )
        self.chat_display._textbox.tag_config("sender_director", foreground="#AB47BC")
        self.chat_display._textbox.tag_config("sender_osint", foreground="#FF6D00")
        self.chat_display._textbox.tag_config(
            "msg_body", foreground=COLORS["text_primary"]
        )

        # Selector de Modo Pre-Generación
        mode_frame = ctk.CTkFrame(panel, fg_color="transparent")
        mode_frame.pack(fill="x", padx=6, pady=(4, 2))

        ctk.CTkLabel(
            mode_frame,
            text="Formato:",
            font=("JetBrains Mono", 10, "bold"),
            text_color=COLORS["text_dim"],
        ).pack(side="left", padx=(4, 8))

        self.pre_mode_var = ctk.StringVar(value="DUAL AI")
        self.pre_mode_selector = ctk.CTkSegmentedButton(
            mode_frame,
            values=["DUAL AI", "SOLO TERM"],
            variable=self.pre_mode_var,
            command=self._on_mode_change,
            font=("JetBrains Mono", 10, "bold"),
            height=24,
            fg_color=COLORS["bg_dark"],
            selected_color=COLORS["accent_cyan"],
            selected_hover_color="#00b8d4",
        )
        self.pre_mode_selector.pack(side="left", fill="x", expand=True, padx=(0, 4))

        # Input
        input_frame = ctk.CTkFrame(panel, fg_color="transparent")
        input_frame.pack(fill="x", padx=6, pady=(0, 6))

        self.chat_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="Pide un guion de video...",
            font=("JetBrains Mono", 12),
            fg_color=COLORS["bg_dark"],
            border_color=COLORS["border"],
        )
        self.chat_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.chat_entry.bind(
            "<Return>", lambda e: self.action_handler.send_chat_message()
        )

        self.chat_btn = ctk.CTkButton(
            input_frame,
            text="⚡",
            width=45,
            command=self.action_handler.send_chat_message,
            font=("Arial", 18),
            fg_color=COLORS["accent_cyan"],
            text_color="#000000",
            hover_color="#00b8d4",
        )
        self.chat_btn.pack(side="right")

    def _build_editor_panel(self):
        """Panel central — Editor JSON Profesional (solo editor + tabs)."""
        panel = ctk.CTkFrame(
            self.tab1,
            fg_color=COLORS["bg_panel"],
            corner_radius=12,
            border_width=1,
            border_color=COLORS["border"],
        )
        panel.grid(row=0, column=1, sticky="nsew", padx=(4, 4), pady=8)

        # Grid: Header(0) + Editor(1) — editor se expande
        panel.grid_rowconfigure(1, weight=1)
        panel.grid_columnconfigure(0, weight=1)

        # ── Header (row 0) ──
        header = ctk.CTkFrame(
            panel, fg_color=COLORS["header_bg"], height=48, corner_radius=0
        )
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)

        ctk.CTkLabel(header, text="📝", font=("Arial", 20)).pack(
            side="left", padx=(12, 4)
        )
        ctk.CTkLabel(
            header,
            text="EDITOR DE GUION",
            font=("JetBrains Mono", 14, "bold"),
            text_color=COLORS["accent_cyan"],
        ).pack(side="left")

        # Botón Guardar (solo icono) en el header
        self.save_project_btn = ctk.CTkButton(
            header,
            text="💾",
            command=self._manual_save_project,
            font=("Arial", 18),
            width=36,
            height=36,
            fg_color="transparent",
            hover_color="#252640",
            text_color=COLORS["accent_cyan"],
        )
        self.save_project_btn.pack(side="right", padx=(0, 12))

        # ── Editor DUAL con pestañas (row 1 — SE EXPANDE) ──
        editor_tabs_frame = ctk.CTkFrame(panel, fg_color="transparent")
        editor_tabs_frame.grid(row=1, column=0, sticky="nsew", padx=8, pady=(4, 8))
        editor_tabs_frame.grid_rowconfigure(1, weight=1)
        editor_tabs_frame.grid_columnconfigure(0, weight=1)

        # Tab buttons (estilizados)
        tab_bar = ctk.CTkFrame(editor_tabs_frame, fg_color="transparent", height=32)
        tab_bar.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        tab_bar.grid_propagate(False)

        self._active_tab = "a"
        self.tab_btn_a = ctk.CTkButton(
            tab_bar,
            text="📝 Terminal A (Chat)",
            command=lambda: self._switch_editor_tab("a"),
            font=("JetBrains Mono", 11, "bold"),
            fg_color=COLORS["accent_cyan"],
            text_color="#000000",
            hover_color="#00b8d4",
            corner_radius=6,
            width=140,
            height=28,
        )
        self.tab_btn_a.pack(side="left", padx=(0, 4))

        self.tab_btn_b = ctk.CTkButton(
            tab_bar,
            text="⚡ Terminal B (Cmds)",
            command=lambda: self._switch_editor_tab("b"),
            font=("JetBrains Mono", 11, "bold"),
            fg_color="#1a1b2e",
            text_color=COLORS["text_dim"],
            hover_color="#252640",
            corner_radius=6,
            width=140,
            height=28,
        )
        self.tab_btn_b.pack(side="left", padx=4)

        # Editor container (switchable)
        editor_stack = ctk.CTkFrame(
            editor_tabs_frame,
            fg_color=COLORS["bg_editor"],
            corner_radius=8,
            border_width=1,
            border_color=COLORS["border"],
        )
        editor_stack.grid(row=1, column=0, sticky="nsew")

        # ── Editor A (Terminal A / Chat) ──
        self.editor_container_a = ctk.CTkFrame(editor_stack, fg_color="transparent")
        self.editor_container_a.pack(fill="both", expand=True, padx=4, pady=4)

        self.line_numbers = tk.Text(
            self.editor_container_a,
            width=4,
            bg="#08090a",
            fg="#3a3a5a",
            font=("JetBrains Mono", 10),
            state="disabled",
            relief="flat",
            bd=0,
            selectbackground="#08090a",
            highlightthickness=0,
            padx=6,
            pady=4,
        )
        self.line_numbers.pack(side="left", fill="y")

        self.editor = tk.Text(
            self.editor_container_a,
            bg=COLORS["bg_editor"],
            fg=COLORS["text_primary"],
            font=("JetBrains Mono", 10),
            insertbackground=COLORS["accent_cyan"],
            selectbackground="#1a2a4a",
            relief="flat",
            bd=0,
            wrap="word",
            highlightthickness=0,
            padx=8,
            pady=4,
            undo=True,
        )
        self.editor.pack(side="left", fill="both", expand=True)

        scrollbar_a = ctk.CTkScrollbar(
            self.editor_container_a, command=self.editor.yview
        )
        scrollbar_a.pack(side="right", fill="y")
        self.editor.configure(yscrollcommand=self._sync_scroll)

        # ── Editor B (Terminal B / Comandos) ──
        self.editor_container_b = ctk.CTkFrame(editor_stack, fg_color="transparent")
        # Inicialmente oculto

        self.line_numbers_b = tk.Text(
            self.editor_container_b,
            width=4,
            bg="#08090a",
            fg="#3a3a5a",
            font=("JetBrains Mono", 10),
            state="disabled",
            relief="flat",
            bd=0,
            selectbackground="#08090a",
            highlightthickness=0,
            padx=6,
            pady=4,
        )
        self.line_numbers_b.pack(side="left", fill="y")

        self.editor_b = tk.Text(
            self.editor_container_b,
            bg="#0a0d0a",
            fg="#a0ffa0",
            font=("JetBrains Mono", 10),
            insertbackground=COLORS["accent_green"],
            selectbackground="#1a3a1a",
            relief="flat",
            bd=0,
            wrap="word",
            highlightthickness=0,
            padx=8,
            pady=4,
            undo=True,
        )
        self.editor_b.pack(side="left", fill="both", expand=True)

        scrollbar_b = ctk.CTkScrollbar(
            self.editor_container_b, command=self.editor_b.yview
        )
        scrollbar_b.pack(side="right", fill="y")
        self.editor_b.configure(yscrollcommand=lambda *a: None)

        # Syntax highlighting tags para ambos editores (VSCode Dark Style)
        for ed in [self.editor, self.editor_b]:
            ed.tag_config("json_key", foreground="#9CDCFE")  # Azul claro (VSCode keys)
            ed.tag_config(
                "json_string", foreground="#CE9178"
            )  # Naranja (VSCode strings)
            ed.tag_config("json_bracket", foreground="#FFD700")  # Amarillo (brackets)
            ed.tag_config(
                "json_keyword", foreground="#C586C0"
            )  # Magenta (keywords/booleans)
            ed.tag_config("json_colon", foreground="#D4D4D4")  # Gris (puntuación)
            ed.tag_config("json_number", foreground="#B5CEA8")  # Verde olivo (numbers)

        self.editor.bind("<KeyRelease>", lambda e: self._schedule_auto_save())
        self.editor.bind("<ButtonRelease-1>", lambda e: self._update_line_numbers())

    def _build_config_panel(self):
        """Panel derecho (Columna 2) — Botones, sliders y config (Scrollable)."""
        panel = ctk.CTkScrollableFrame(
            self.tab1,
            fg_color=COLORS["bg_panel"],
            corner_radius=12,
            border_width=1,
            border_color=COLORS["border"],
        )
        panel.grid(row=0, column=2, sticky="nsew", padx=(4, 8), pady=8)

        # ── Header ──
        header = ctk.CTkFrame(
            panel, fg_color=COLORS["header_bg"], height=42, corner_radius=0
        )
        header.pack(fill="x", pady=(0, 6))
        header.pack_propagate(False)

        ctk.CTkLabel(header, text="⚙️", font=("Arial", 18)).pack(
            side="left", padx=(12, 4)
        )
        ctk.CTkLabel(
            header,
            text="CONFIGURACIÓN",
            font=("JetBrains Mono", 13, "bold"),
            text_color=COLORS["accent_red"],
        ).pack(side="left")

        # Botón OBS (movido desde la barra de API)
        self.obs_btn = ctk.CTkButton(
            panel,
            text="📺 Conectar OBS",
            command=self._connect_obs,
            font=("JetBrains Mono", 10, "bold"),
            fg_color="#6c3483",
            text_color="#ffffff",
            hover_color="#8e44ad",
            height=30,
        )
        self.obs_btn.pack(fill="x", padx=4, pady=(0, 6))

        # ── Toolbar proyectos (movido del editor) ──
        toolbar = ctk.CTkFrame(panel, fg_color=COLORS["header_bg"], height=34)
        toolbar.pack(fill="x", pady=4, padx=4)

        ctk.CTkButton(
            toolbar,
            text="💾 Guardar",
            command=self.save_project,
            font=("JetBrains Mono", 10, "bold"),
            fg_color="#1a1b2e",
            hover_color="#252640",
            border_width=1,
            border_color=COLORS["border"],
        ).pack(side="left", padx=(6, 2), fill="x", expand=True)

        ctk.CTkButton(
            toolbar,
            text="📂 Cargar",
            command=self.load_project,
            font=("JetBrains Mono", 10, "bold"),
            fg_color="#1a1b2e",
            hover_color="#252640",
            border_width=1,
            border_color=COLORS["border"],
        ).pack(side="left", padx=2, fill="x", expand=True)

        self.project_name_label = ctk.CTkLabel(
            toolbar,
            text="Sin título",
            font=("JetBrains Mono", 9),
            text_color=COLORS["text_dim"],
        )
        self.project_name_label.pack(side="right", padx=6)

        # Controles
        controls = ctk.CTkFrame(panel, fg_color="transparent")
        controls.pack(fill="both", expand=True, padx=4, pady=4)

        # Target IP selector
        ctk.CTkLabel(
            controls,
            text="🎯 IP/Target:",
            font=("JetBrains Mono", 10, "bold"),
            text_color=COLORS["text_dim"],
        ).pack(anchor="w", padx=4, pady=(2, 0))
        self.target_combo = ctk.CTkComboBox(
            controls,
            width=190,
            height=28,
            values=[
                "scanme.nmap.org",
                "testphp.vulnweb.com",
                "httpbin.org",
                "badssl.com",
                "rest.vulnweb.com",
                "IP Personalizada",
            ],
            font=("JetBrains Mono", 11),
            fg_color=COLORS["bg_dark"],
            border_color=COLORS["border"],
            dropdown_fg_color=COLORS["bg_dark"],
        )
        self.target_combo.set("scanme.nmap.org")
        self.target_combo.pack(fill="x", padx=4, pady=(2, 6))

        # Slider de velocidad
        speed_row = ctk.CTkFrame(controls, fg_color="transparent")
        speed_row.pack(fill="x", padx=4, pady=(6, 2))

        ctk.CTkLabel(
            speed_row,
            text="⌨ Velocidad:",
            font=("JetBrains Mono", 10, "bold"),
            text_color=COLORS["text_dim"],
        ).pack(side="left")

        self.speed_slider = ctk.CTkSlider(
            speed_row,
            from_=50,
            to=200,
            number_of_steps=15,
            command=self._on_speed_change,
            width=140,
            fg_color=COLORS["border"],
            progress_color=COLORS["accent_cyan"],
            button_color=COLORS["accent_cyan"],
        )
        self.speed_slider.set(80)  # Default to 80% (slower than normal)
        self.speed_slider.pack(side="left", padx=6)

        self.speed_label = ctk.CTkLabel(
            speed_row,
            text="80%",
            font=("JetBrains Mono", 10, "bold"),
            text_color=COLORS["accent_cyan"],
        )
        self.speed_label.pack(side="left")

        # Selector de formato
        format_row = ctk.CTkFrame(controls, fg_color="transparent")
        format_row.pack(fill="x", padx=4, pady=(6, 2))

        self.format_combo = ctk.CTkOptionMenu(
            format_row,
            values=["9:16 (Vertical)", "16:9 (Horizontal)"],
            font=("JetBrains Mono", 11),
            fg_color=COLORS["border"],
            button_color=COLORS["accent_red"],
            button_hover_color="#9c27b0",
            width=140,
            command=self._on_format_change,
        )
        self.format_combo.set("9:16 (Vertical)")
        self.format_combo.pack(side="left", padx=6)

        # Slider de duración de video
        dur_row = ctk.CTkFrame(controls, fg_color="transparent")
        dur_row.pack(fill="x", padx=4, pady=(6, 2))

        ctk.CTkLabel(
            dur_row,
            text="🎬 Duración:",
            font=("JetBrains Mono", 10, "bold"),
            text_color=COLORS["text_dim"],
        ).pack(side="left")

        self.duration_slider = ctk.CTkSlider(
            dur_row,
            from_=1,
            to=30,
            number_of_steps=29,
            command=self._on_duration_change,
            width=140,
            fg_color=COLORS["border"],
            progress_color="#FF8F00",
            button_color="#FF8F00",
        )
        self.duration_slider.set(5)
        self.duration_slider.pack(side="left", padx=6)

        self.duration_label = ctk.CTkLabel(
            dur_row,
            text="5 min",
            font=("JetBrains Mono", 10, "bold"),
            text_color="#FF8F00",
        )
        self.duration_label.pack(side="left")
        self.video_duration_min = 5

        # ── CONFIGURACIÓN DE VIDEO ──────────────────────────────────────
        vc_header = ctk.CTkFrame(
            controls, fg_color="#1a1b2e", height=28, corner_radius=0
        )
        vc_header.pack(fill="x", pady=(12, 0))
        ctk.CTkLabel(
            vc_header,
            text="🎬 TIPO DE VIDEO",
            font=("JetBrains Mono", 10, "bold"),
            text_color=COLORS["accent_cyan"],
        ).pack(side="left", padx=8, pady=4)

        # Tipo de video
        templates = get_template_list()
        template_labels = [f"{t['icono']} {t['nombre']}" for t in templates]
        template_keys = [t["key"] for t in templates]
        self._video_type_var = ctk.StringVar(value=template_labels[1])

        video_type_menu = ctk.CTkOptionMenu(
            controls,
            variable=self._video_type_var,
            values=template_labels,
            command=self._on_video_config_change,
            fg_color="#1a1b2e",
            button_color=COLORS["accent_cyan"],
            font=("JetBrains Mono", 10),
            height=30,
        )
        video_type_menu.pack(fill="x", padx=4, pady=(4, 2))
        self._template_keys = template_keys

        # Estilo presentador
        presenters = get_presenter_list()
        presenter_labels = [p["nombre"] for p in presenters]
        self._presenter_style_var = ctk.StringVar(value=presenter_labels[0])

        ctk.CTkOptionMenu(
            controls,
            variable=self._presenter_style_var,
            values=presenter_labels,
            command=self._on_video_config_change,
            fg_color="#1a1b2e",
            button_color="#FF8F00",
            font=("JetBrains Mono", 10),
            height=28,
        ).pack(fill="x", padx=4, pady=(0, 2))
        self._presenter_keys = [p["key"] for p in presenters]

        # Nivel de audiencia
        audiences = get_audience_list()
        audience_labels = [a["nombre"] for a in audiences]
        self._audience_var = ctk.StringVar(value=audience_labels[1])

        ctk.CTkOptionMenu(
            controls,
            variable=self._audience_var,
            values=audience_labels,
            command=self._on_video_config_change,
            fg_color="#1a1b2e",
            button_color="#ff3333",
            font=("JetBrains Mono", 10),
            height=28,
        ).pack(fill="x", padx=4, pady=(0, 2))
        self._audience_keys = [a["key"] for a in audiences]

        # Notas adicionales
        ctk.CTkLabel(
            controls,
            text="Notas para la IA:",
            font=("JetBrains Mono", 9),
            text_color="#555577",
        ).pack(anchor="w", padx=6)
        self._extra_notes_text = ctk.CTkTextbox(
            controls,
            height=50,
            font=("JetBrains Mono", 10),
            fg_color="#080810",
            border_color=COLORS["border"],
            border_width=1,
        )
        self._extra_notes_text.pack(fill="x", padx=4, pady=(0, 4))
        self._extra_notes_text.bind(
            "<FocusOut>", lambda e: self._on_video_config_change()
        )

        # Selector de tipo de contenido
        content_row = ctk.CTkFrame(controls, fg_color="transparent")
        content_row.pack(fill="x", padx=4, pady=(6, 2))

        ctk.CTkLabel(
            content_row,
            text="🧠 Memoria:",
            font=("JetBrains Mono", 10, "bold"),
            text_color=COLORS["text_dim"],
        ).pack(side="left")

        content_types = ["Por defecto"] + [t["key"] for t in get_template_list()]
        self.content_combo = ctk.CTkOptionMenu(
            content_row,
            values=content_types,
            font=("JetBrains Mono", 11),
            fg_color=COLORS["border"],
            button_color=COLORS["accent_yellow"],
            button_hover_color="#e6b800",
            width=140,
        )
        self.content_combo.set("Por defecto")
        self.content_combo.pack(side="left", padx=6)

        # Botones de acción
        btn_row = ctk.CTkFrame(controls, fg_color="transparent")
        btn_row.pack(fill="x", padx=4, pady=(15, 3))

        self.btn_tts = ctk.CTkButton(
            btn_row,
            text="🔊 TTS",
            command=self.generate_audios,
            font=("JetBrains Mono", 11, "bold"),
            fg_color="#1a1b2e",
            hover_color="#252640",
            border_width=1,
            border_color=COLORS["accent_cyan"],
            height=34,
        )
        self.btn_tts.pack(fill="x", pady=(0, 6))

        # Contenido de Tercero (Dropdown)
        self.third_party_content_var = ctk.StringVar(value="Desactivado")
        ctk.CTkLabel(
            controls,
            text="🎬 Contenido:",
            font=("JetBrains Mono", 10),
            text_color=COLORS["text_dim"],
        ).pack(anchor="w", padx=8, pady=(0, 2))

        self.third_party_menu = ctk.CTkOptionMenu(
            controls,
            variable=self.third_party_content_var,
            values=[
                "Desactivado",
                "Contenido Mixto (Videos + Terminal)",
                "Contenido Puro (Terminal)",
            ],
            width=180,
            font=("JetBrains Mono", 10),
            fg_color="#1a1b2e",
            button_color=COLORS["accent_yellow"],
        )
        self.third_party_menu.pack(anchor="w", padx=8, pady=(0, 6))

        self.use_wrapper_var = ctk.BooleanVar(value=False)
        self.wrapper_check = ctk.CTkCheckBox(
            controls,
            text="🔲 KR-CLI Wrapper (Terminal B)",
            variable=self.use_wrapper_var,
            font=("JetBrains Mono", 10),
            text_color=COLORS["text_dim"],
            fg_color=COLORS["accent_red"],
            hover_color="#9c27b0",
            checkbox_width=18,
            checkbox_height=18,
        )
        self.wrapper_check.pack(anchor="w", padx=8, pady=(0, 6))

    # ═══════════════════════════════════════════════
    # SPEED SLIDER
    # ═══════════════════════════════════════════════

    def _switch_editor_tab(self, tab: str):
        """Alterna entre Editor Terminal A y Editor Terminal B."""
        self._active_tab = tab
        if tab == "a":
            self.editor_container_b.pack_forget()
            self.editor_container_a.pack(fill="both", expand=True, padx=4, pady=4)
            self.tab_btn_a.configure(
                fg_color=COLORS["accent_cyan"], text_color="#000000"
            )
            self.tab_btn_b.configure(fg_color="#1a1b2e", text_color=COLORS["text_dim"])
        else:
            self.editor_container_a.pack_forget()
            self.editor_container_b.pack(fill="both", expand=True, padx=4, pady=4)
            self.tab_btn_b.configure(
                fg_color=COLORS["accent_green"], text_color="#000000"
            )
            self.tab_btn_a.configure(fg_color="#1a1b2e", text_color=COLORS["text_dim"])

    def _inject_json_editor_a(self, json_text: str):
        """Callback: inyecta JSON en el editor Terminal A."""
        self.editor.delete("1.0", "end")
        self.editor.insert("end", json_text)
        self._update_editor()
        self._switch_editor_tab("a")

    def _inject_json_editor_b(self, json_text: str):
        """Callback: inyecta JSON en el editor Terminal B."""
        self.editor_b.delete("1.0", "end")
        self.editor_b.insert("end", json_text)
        self._switch_editor_tab("b")

    # ═══════════════════════════════════════════════
    # TAB 2: POST-PRODUCCIÓN — EDITOR PROFESIONAL
    # ═══════════════════════════════════════════════

    # ═══════════════════════════════════════════════════════════════════════
    #  TAB 3 — ESTUDIO TTS PROFESIONAL
    # ═══════════════════════════════════════════════════════════════════════

    def _build_tts_studio(self):
        """
        Estudio TTS completo con:
        - Panel izquierdo: biblioteca de audios generados (por proyecto/capítulo)
        - Panel derecho: editor de voz con controles pro (voz, rate, pitch, volumen)
        - Generación individual y por lotes desde JSON
        - Preview, reproducción, descarga y gestión de archivos
        """
        # ── Header ──
        header = ctk.CTkFrame(
            self.tab3, fg_color=COLORS["header_bg"], height=48, corner_radius=0
        )
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=0, pady=0)
        ctk.CTkLabel(
            header,
            text="🎙  ESTUDIO TTS PROFESIONAL",
            font=("JetBrains Mono", 14, "bold"),
            text_color=COLORS["accent_cyan"],
        ).pack(side="left", padx=14, pady=10)
        ctk.CTkLabel(
            header,
            text="edge-tts  •  48kHz/16bit  •  PCM WAV",
            font=("JetBrains Mono", 10),
            text_color="#555577",
        ).pack(side="right", padx=14)

        # ════════════════════════════════════════
        # PANEL IZQUIERDO — Biblioteca de audios
        # ════════════════════════════════════════
        lib_frame = ctk.CTkFrame(
            self.tab3,
            fg_color=COLORS["bg_panel"],
            corner_radius=10,
            border_width=1,
            border_color=COLORS["border"],
        )
        lib_frame.grid(row=1, column=0, sticky="nsew", padx=(8, 4), pady=(8, 8))
        lib_frame.grid_rowconfigure(2, weight=1)
        lib_frame.grid_columnconfigure(0, weight=1)

        lh = ctk.CTkFrame(
            lib_frame, fg_color=COLORS["header_bg"], height=36, corner_radius=0
        )
        lh.grid(row=0, column=0, sticky="ew")
        ctk.CTkLabel(
            lh,
            text="📂 BIBLIOTECA DE AUDIOS",
            font=("JetBrains Mono", 11, "bold"),
            text_color=COLORS["accent_yellow"],
        ).pack(side="left", padx=10, pady=6)

        # Filtro / búsqueda
        filt = ctk.CTkFrame(lib_frame, fg_color="transparent")
        filt.grid(row=1, column=0, sticky="ew", padx=6, pady=(6, 2))
        filt.grid_columnconfigure(0, weight=1)
        self._tts_filter_var = ctk.StringVar()
        self._tts_filter_var.trace_add("write", self._tts_filter_library)
        ctk.CTkEntry(
            filt,
            textvariable=self._tts_filter_var,
            placeholder_text="🔍 Filtrar audios...",
            font=("JetBrains Mono", 10),
            fg_color="#111122",
            border_color=COLORS["border"],
            height=28,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 4))
        ctk.CTkButton(
            filt,
            text="↺",
            command=self._tts_refresh_library,
            fg_color="#1a1b2e",
            hover_color="#252640",
            width=30,
            height=28,
            font=("JetBrains Mono", 12),
        ).grid(row=0, column=1)

        # Lista scrollable
        self._tts_lib_scroll = ctk.CTkScrollableFrame(lib_frame, fg_color="transparent")
        self._tts_lib_scroll.grid(row=2, column=0, sticky="nsew", padx=4, pady=4)
        self._tts_lib_items = []  # [{path, nombre, dur, frame}]

        # Botones biblioteca
        lib_btns = ctk.CTkFrame(lib_frame, fg_color="transparent")
        lib_btns.grid(row=3, column=0, sticky="ew", padx=6, pady=(0, 6))
        ctk.CTkButton(
            lib_btns,
            text="📂 Abrir carpeta",
            command=self._tts_open_folder,
            fg_color="#1a1b2e",
            hover_color="#252640",
            font=("JetBrains Mono", 10),
            height=28,
        ).pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkButton(
            lib_btns,
            text="🗑 Limpiar todo",
            command=self._tts_clear_all,
            fg_color="#3a1010",
            hover_color="#5a1818",
            font=("JetBrains Mono", 10),
            height=28,
        ).pack(side="left", fill="x", expand=True)

        # ════════════════════════════════════════
        # PANEL DERECHO — Editor y controles pro
        # ════════════════════════════════════════
        edit_frame = ctk.CTkFrame(
            self.tab3,
            fg_color=COLORS["bg_panel"],
            corner_radius=10,
            border_width=1,
            border_color=COLORS["border"],
        )
        edit_frame.grid(row=1, column=1, sticky="nsew", padx=(4, 8), pady=(8, 8))
        edit_frame.grid_rowconfigure(3, weight=1)
        edit_frame.grid_columnconfigure(0, weight=1)

        eh = ctk.CTkFrame(
            edit_frame, fg_color=COLORS["header_bg"], height=36, corner_radius=0
        )
        eh.grid(row=0, column=0, sticky="ew")
        ctk.CTkLabel(
            eh,
            text="✏️  EDITOR DE VOZ",
            font=("JetBrains Mono", 11, "bold"),
            text_color="#AAAAAA",
        ).pack(side="left", padx=10, pady=6)

        # ── Controles pro ──
        ctrl = ctk.CTkFrame(edit_frame, fg_color="#0d0e1a", corner_radius=6)
        ctrl.grid(row=1, column=0, sticky="ew", padx=8, pady=(8, 4))
        ctrl.grid_columnconfigure((1, 3, 5, 7), weight=1)

        from kr_studio.core.audio_engine import AudioEngine as _AE  # type: ignore

        # Nombre archivo
        ctk.CTkLabel(
            ctrl, text="Nombre:", font=("JetBrains Mono", 10), text_color="#AAAAAA"
        ).grid(row=0, column=0, padx=(8, 4), pady=6, sticky="w")
        self._tts_name_var = ctk.StringVar(value="voz_01")
        ctk.CTkEntry(
            ctrl,
            textvariable=self._tts_name_var,
            font=("JetBrains Mono", 10),
            fg_color="#111122",
            border_color=COLORS["border"],
            height=28,
            width=120,
        ).grid(row=0, column=1, padx=(0, 12), pady=6, sticky="ew")

        # Voz
        ctk.CTkLabel(
            ctrl, text="Voz:", font=("JetBrains Mono", 10), text_color="#AAAAAA"
        ).grid(row=0, column=2, padx=(0, 4), pady=6)
        self._tts_voice_var = ctk.StringVar(value=list(_AE.VOICE_OPTIONS.keys())[0])  # type: ignore
        ctk.CTkOptionMenu(
            ctrl,
            variable=self._tts_voice_var,
            values=list(_AE.VOICE_OPTIONS.keys()),  # type: ignore
            fg_color="#1a1b2e",
            button_color=COLORS["accent_cyan"],
            font=("JetBrains Mono", 10),
            width=160,
        ).grid(row=0, column=3, padx=(0, 12), pady=6, sticky="ew")

        # Rate
        ctk.CTkLabel(
            ctrl, text="Rate:", font=("JetBrains Mono", 10), text_color="#AAAAAA"
        ).grid(row=1, column=0, padx=(8, 4), pady=6)
        self._tts_rate_var = ctk.StringVar(value="+0%")
        ctk.CTkOptionMenu(
            ctrl,
            variable=self._tts_rate_var,
            values=[
                "-20%",
                "-15%",
                "-10%",
                "-5%",
                "+0%",
                "+5%",
                "+10%",
                "+15%",
                "+20%",
                "+30%",
            ],
            fg_color="#1a1b2e",
            button_color="#FF8F00",
            font=("JetBrains Mono", 10),
            width=90,
        ).grid(row=1, column=1, padx=(0, 12), pady=6, sticky="w")

        # Pitch
        ctk.CTkLabel(
            ctrl, text="Pitch:", font=("JetBrains Mono", 10), text_color="#AAAAAA"
        ).grid(row=1, column=2, padx=(0, 4), pady=6)
        self._tts_pitch_var = ctk.StringVar(value="+0Hz")
        ctk.CTkOptionMenu(
            ctrl,
            variable=self._tts_pitch_var,
            values=[
                "-15Hz",
                "-10Hz",
                "-5Hz",
                "+0Hz",
                "+5Hz",
                "+10Hz",
                "+15Hz",
                "+20Hz",
            ],
            fg_color="#1a1b2e",
            button_color="#ff3333",
            font=("JetBrains Mono", 10),
            width=90,
        ).grid(row=1, column=3, padx=(0, 12), pady=6, sticky="w")

        # Volumen
        ctk.CTkLabel(
            ctrl, text="Vol:", font=("JetBrains Mono", 10), text_color="#AAAAAA"
        ).grid(row=1, column=4, padx=(0, 4), pady=6)
        self._tts_vol_var = ctk.StringVar(value="+0%")
        ctk.CTkOptionMenu(
            ctrl,
            variable=self._tts_vol_var,
            values=["-20%", "-10%", "+0%", "+10%", "+20%", "+50%"],
            fg_color="#1a1b2e",
            button_color="#00897B",
            font=("JetBrains Mono", 10),
            width=90,
        ).grid(row=1, column=5, padx=(0, 12), pady=6, sticky="w")

        # Modo batch desde JSON activo
        self._tts_batch_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            ctrl,
            text="Batch desde JSON activo",
            variable=self._tts_batch_var,
            font=("JetBrains Mono", 10),
            text_color="#AAAAAA",
            fg_color=COLORS["accent_cyan"],
            hover_color="#00ACC1",
        ).grid(row=1, column=6, columnspan=2, padx=8, pady=6, sticky="w")

        # ── Área de texto ──
        txt_header = ctk.CTkFrame(edit_frame, fg_color="transparent")
        txt_header.grid(row=2, column=0, sticky="ew", padx=8, pady=(4, 0))
        ctk.CTkLabel(
            txt_header,
            text="Texto a narrar:",
            font=("JetBrains Mono", 10),
            text_color="#AAAAAA",
        ).pack(side="left")
        self._tts_char_label = ctk.CTkLabel(
            txt_header, text="0 chars", font=("JetBrains Mono", 9), text_color="#555577"
        )
        self._tts_char_label.pack(side="right")

        self._tts_textbox = ctk.CTkTextbox(
            edit_frame,
            font=("JetBrains Mono", 12),
            fg_color="#080810",
            border_color=COLORS["border"],
            border_width=1,
            wrap="word",
        )
        self._tts_textbox.grid(row=3, column=0, sticky="nsew", padx=8, pady=(4, 4))
        self._tts_textbox.bind("<KeyRelease>", self._tts_update_charcount)
        PLACEHOLDER = "Escribe el texto que quieres convertir a voz profesional..."
        self._tts_textbox.insert("end", PLACEHOLDER)
        self._tts_textbox.bind(
            "<FocusIn>", lambda e: self._tts_clear_placeholder(PLACEHOLDER)
        )

        # ── Barra de progreso y estado ──
        prog_frame = ctk.CTkFrame(edit_frame, fg_color="transparent")
        prog_frame.grid(row=4, column=0, sticky="ew", padx=8, pady=(0, 4))
        prog_frame.grid_columnconfigure(0, weight=1)

        self._tts_progress = ctk.CTkProgressBar(
            prog_frame,
            fg_color="#111122",
            progress_color=COLORS["accent_cyan"],
            height=8,
        )
        self._tts_progress.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self._tts_progress.set(0)

        self._tts_status = ctk.CTkLabel(
            prog_frame,
            text="Listo.",
            font=("JetBrains Mono", 10),
            text_color="#555577",
            anchor="w",
            width=200,
        )
        self._tts_status.grid(row=0, column=1, sticky="w")

        # ── Botones de acción ──
        act_row = ctk.CTkFrame(edit_frame, fg_color="transparent")
        act_row.grid(row=5, column=0, sticky="ew", padx=8, pady=(0, 8))

        self._tts_btn_gen = ctk.CTkButton(
            act_row,
            text="🔊 Generar TTS",
            command=self._tts_generate,
            fg_color=COLORS["accent_cyan"],
            hover_color="#00ACC1",
            text_color="#000000",
            font=("JetBrains Mono", 12, "bold"),
            height=38,
        )
        self._tts_btn_gen.pack(side="left", fill="x", expand=True, padx=(0, 6))

        ctk.CTkButton(
            act_row,
            text="🎧 Preview",
            command=self._tts_preview,
            fg_color="#1a2a1a",
            hover_color="#2a4a2a",
            font=("JetBrains Mono", 11),
            height=38,
        ).pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            act_row,
            text="⏹ Stop",
            command=self._tts_stop_playback,
            fg_color="#3a1010",
            hover_color="#5a1818",
            font=("JetBrains Mono", 11),
            height=38,
        ).pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            act_row,
            text="🔄 Batch JSON",
            command=self._tts_batch_from_json,
            fg_color="#1a1b2e",
            hover_color="#252640",
            border_width=1,
            border_color=COLORS["accent_cyan"],
            font=("JetBrains Mono", 11),
            height=38,
        ).pack(side="left")

        # Estado interno
        self._tts_last_path = None
        self._tts_current_proc = None
        self._tts_lib_all = []  # todos los items sin filtro

        # Cargar biblioteca al arrancar
        self.after(500, self._tts_refresh_library)

    # ─── HELPERS TTS STUDIO ────────────────────────────────────────────────

    @staticmethod
    def _voz_pronunciable(voz) -> str:
        """Limpia texto: quita emojis, controles, espacios. Retorna '' si no pronunciable."""
        import unicodedata, re as _re

        if not isinstance(voz, str):
            return ""
        voz = unicodedata.normalize("NFC", voz)
        voz = _re.sub(
            r"[\U0001F300-\U0001F9FF\U00010000-\U0010FFFF"
            r"\u2600-\u27BF\u200B-\u200F\uFE00-\uFE0F]+",
            " ",
            voz,
            flags=_re.UNICODE,
        )
        voz = _re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", " ", voz)
        voz = _re.sub(r" {2,}", " ", voz).strip()
        return voz if sum(1 for ch in voz if ch.isalpha()) >= 2 else ""

    def _tts_clear_placeholder(self, placeholder: str):
        current = self._tts_textbox.get("1.0", "end").strip()
        if current == placeholder:
            self._tts_textbox.delete("1.0", "end")

    def _tts_update_charcount(self, event=None):
        n = len(self._tts_textbox.get("1.0", "end").strip())
        self._tts_char_label.configure(text=f"{n} chars")

    def _tts_get_engine(self):
        """Crea AudioEngine con los parámetros actuales del estudio."""
        from kr_studio.core.audio_engine import AudioEngine as _AE  # type: ignore

        voice_key = self._tts_voice_var.get()
        voice_id = _AE.VOICE_OPTIONS.get(voice_key, _AE.DEFAULT_VOICE)  # type: ignore
        engine = _AE(voice=voice_id)
        engine._studio_rate = self._tts_rate_var.get()
        engine._studio_pitch = self._tts_pitch_var.get()
        engine._studio_vol = self._tts_vol_var.get()
        return engine

    def _get_tts_dir(self) -> str:
        """Obtiene el directorio de TTS. Usa la carpeta del capítulo (donde está el JSON)."""
        if hasattr(self, "course_orchestrator") and self.course_orchestrator:
            course_dir = self.course_orchestrator._course_dir
            if course_dir:
                os.makedirs(course_dir, exist_ok=True)
                return course_dir
        return os.path.join(self.workspace_dir, "voces_manuales")

    def _tts_generate(self):
        """Genera WAV del texto actual con los parámetros pro del estudio."""
        raw = self._tts_textbox.get("1.0", "end").strip()
        texto = self._voz_pronunciable(raw)
        if not texto:
            self._tts_status.configure(
                text="⚠ Texto vacío o no pronunciable.", text_color="#FF5252"
            )
            return

        nombre = re.sub(r"[^\w\-]", "_", self._tts_name_var.get().strip() or "voz")
        voice_dir = self._get_tts_dir()
        os.makedirs(voice_dir, exist_ok=True)
        output_path = os.path.join(voice_dir, f"{nombre}.wav")

        self._tts_btn_gen.configure(state="disabled", text="⏳ Generando...")
        self._tts_progress.set(0.1)
        self._tts_status.configure(text="⏳ Generando audio...", text_color="#FF8F00")

        def _worker():
            try:
                engine = self._tts_get_engine()
                dur = engine.generar_audio(texto, output_path)
                self._tts_last_path = output_path
                self.after(0, self._tts_on_done, output_path, nombre, dur, 1, 1)
            except Exception as e:
                self.after(
                    0,
                    lambda err=e: (
                        self._tts_status.configure(
                            text=f"❌ {err}", text_color="#FF5252"
                        ),
                        self._tts_progress.set(0),
                        self._tts_btn_gen.configure(
                            state="normal", text="🔊 Generar TTS"
                        ),
                    ),
                )

        threading.Thread(target=_worker, daemon=True).start()

    def _tts_on_done(self, path: str, nombre: str, dur: float, idx: int, total: int):
        """Callback al terminar generación de un audio."""
        progress = idx / total
        self._tts_progress.set(progress)
        if idx == total:
            self._tts_status.configure(
                text=f"✅ {nombre}.wav  ({dur:.1f}s)  →  {os.path.dirname(path)}",
                text_color="#00E676",
            )
            self._tts_btn_gen.configure(state="normal", text="🔊 Generar TTS")
        else:
            self._tts_status.configure(
                text=f"⏳ {idx}/{total}  —  {nombre}.wav ({dur:.1f}s)",
                text_color="#FF8F00",
            )
        self._tts_add_to_library(path, nombre, dur)

    def _tts_add_to_library(self, path: str, nombre: str, dur: float):
        """Agrega un item a la biblioteca visual."""
        # Evitar duplicados
        for item in self._tts_lib_items:
            if item["path"] == path:
                return

        item_frame = ctk.CTkFrame(
            self._tts_lib_scroll,
            fg_color="#0d0e1a",
            corner_radius=6,
            border_width=1,
            border_color="#1a1b2e",
        )
        item_frame.pack(fill="x", pady=2, padx=2)
        item_frame.grid_columnconfigure(0, weight=1)

        # Nombre y duración
        info = ctk.CTkFrame(item_frame, fg_color="transparent")
        info.grid(row=0, column=0, sticky="ew", padx=6, pady=(4, 0))
        ctk.CTkLabel(
            info,
            text=f"🔊 {nombre}",
            font=("JetBrains Mono", 10, "bold"),
            text_color="#CCCCCC",
            anchor="w",
        ).pack(side="left")
        ctk.CTkLabel(
            info, text=f"{dur:.1f}s", font=("JetBrains Mono", 9), text_color="#555577"
        ).pack(side="right")

        # Ruta corta
        short_path = "..." + path[-45:] if len(path) > 48 else path  # type: ignore
        ctk.CTkLabel(
            item_frame,
            text=short_path,
            font=("JetBrains Mono", 8),
            text_color="#333355",
            anchor="w",
        ).grid(row=1, column=0, sticky="ew", padx=6, pady=(0, 2))

        # Botones
        btns = ctk.CTkFrame(item_frame, fg_color="transparent")
        btns.grid(row=0, column=1, rowspan=2, padx=(0, 4), pady=2)

        ctk.CTkButton(
            btns,
            text="▶",
            command=lambda p=path: self._tts_play(p),
            fg_color="#00695C",
            hover_color="#004D40",
            width=30,
            height=22,
            font=("JetBrains Mono", 10, "bold"),
        ).pack(pady=(0, 2))
        ctk.CTkButton(
            btns,
            text="🗑",
            command=lambda f=item_frame, p=path: self._tts_delete_item(f, p),
            fg_color="#3a1010",
            hover_color="#5a1818",
            width=30,
            height=22,
            font=("JetBrains Mono", 10),
        ).pack()

        record = {"path": path, "nombre": nombre, "dur": dur, "frame": item_frame}
        self._tts_lib_items.append(record)
        self._tts_lib_all.append(record)

    def _tts_batch_from_json(self):
        """
        Genera TTS para TODAS las escenas con campo 'voz' del JSON activo en el editor.
        Guarda en la carpeta del proyecto activo junto al JSON.
        Muestra progreso en tiempo real.
        """
        json_data = self._parse_editor_json()
        if not json_data:
            self._tts_status.configure(
                text="⚠ No hay JSON válido en el editor.", text_color="#FF5252"
            )
            return

        # Determinar carpeta destino (junto al JSON del proyecto)
        course_dir = None
        series_dir = None

        # Verificar si estamos en modo curso (módulos y capítulos)
        if hasattr(self, "course_orchestrator") and self.course_orchestrator:
            course_dir = getattr(self.course_orchestrator, "_course_dir", None)

        # Si no hay curso, verificar series
        if not course_dir:
            series_dir = getattr(self.series_orchestrator, "_series_dir", None)

        if course_dir:
            # Modo curso: guardar en la carpeta del capítulo (donde está el JSON)
            audio_dir = course_dir
        elif series_dir:
            try:
                tab = self.modules_tabview.get()
                tab_safe = re.sub(r"[^a-zA-Z0-9_\-]", "_", tab.lower())
                audio_dir = os.path.join(series_dir, tab_safe, "audio")
            except Exception:
                audio_dir = os.path.join(series_dir, "audio_batch")
        else:
            tts_dir = self._get_tts_dir()
            audio_dir = os.path.join(tts_dir, "batch")
        os.makedirs(audio_dir, exist_ok=True)

        escenas_con_voz = [
            (i, e)
            for i, e in enumerate(json_data)
            if self._voz_pronunciable(e.get("voz", ""))
        ]
        if not escenas_con_voz:
            self._tts_status.configure(
                text="⚠ Ninguna escena tiene texto pronunciable.", text_color="#FF5252"
            )
            return

        total = len(escenas_con_voz)
        self._tts_btn_gen.configure(state="disabled", text="⏳ Batch...")
        self._tts_progress.set(0)
        self._tts_status.configure(text=f"⏳ Batch: 0/{total}", text_color="#FF8F00")
        self.append_chat("TTS", f"🔊 Batch TTS iniciado: {total} escenas → {audio_dir}")

        def _worker():
            import hashlib

            engine = self._tts_get_engine()
            errores: int = 0
            for count, (idx, escena) in enumerate(escenas_con_voz, 1):
                voz = self._voz_pronunciable(escena.get("voz", ""))
                h = hashlib.md5(voz.encode()).hexdigest()[:8]  # type: ignore
                path = os.path.join(audio_dir, f"audio_{idx:03d}_{h}.wav")
                nombre = f"escena_{idx:03d}"

                if os.path.exists(path):
                    msg = f"  Cache ✓ {nombre}"
                    self.after(
                        0,
                        self._tts_status.configure,
                        {
                            "text": f"⏳ {count}/{total} — {msg}",
                            "text_color": "#FF8F00",
                        },
                    )
                    self.after(0, self._tts_progress.set, count / total)
                    self.after(0, self.append_chat, "TTS", msg)
                    continue

                try:
                    dur = engine.generar_audio(voz, path)
                    msg = f"  ✅ {nombre} — {dur:.1f}s"
                    self.after(0, self._tts_on_done, path, nombre, dur, count, total)
                    self.after(0, self.append_chat, "TTS", msg)
                except Exception as e:
                    errores = errores + 1  # type: ignore
                    msg = f"  ❌ {nombre}: {e}"
                    self.after(0, self.append_chat, "Error", msg)
                    self.after(
                        0,
                        self._tts_status.configure,
                        {"text": f"❌ Error en {nombre}", "text_color": "#FF5252"},
                    )

            final = (
                f"✅ Batch completo: {total - errores}/{total} audios → {audio_dir}"
                if errores == 0
                else f"⚠ Batch: {errores} errores de {total}"
            )
            self.after(0, self.append_chat, "Sistema", final)
            self.after(
                0,
                self._tts_status.configure,
                {"text": final, "text_color": "#00E676" if errores == 0 else "#FF8F00"},
            )
            self.after(0, self._tts_progress.set, 1.0)
            self.after(
                0,
                self._tts_btn_gen.configure,
                {"state": "normal", "text": "🔊 Generar TTS"},
            )

        threading.Thread(target=_worker, daemon=True).start()

    def _tts_play(self, path: str):
        """Reproduce WAV con mpv en background."""
        import subprocess as _sp

        if not os.path.exists(path):
            return
        self._tts_stop_playback()
        self._tts_current_proc = _sp.Popen(
            ["mpv", "--no-video", "--really-quiet", path],
            stdout=_sp.DEVNULL,
            stderr=_sp.DEVNULL,
        )

    def _tts_stop_playback(self):
        proc = self._tts_current_proc
        if proc and proc.poll() is None:
            try:
                proc.terminate()
                proc.wait(timeout=2)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
        self._tts_current_proc = None

    def _tts_preview(self):
        if not self._tts_last_path or not os.path.exists(self._tts_last_path):
            self._tts_status.configure(
                text="⚠ Primero genera un audio.", text_color="#FF8F00"
            )
            return
        self._tts_play(self._tts_last_path)

    def _tts_delete_item(self, frame, path: str):
        frame.destroy()
        try:
            if os.path.exists(path):
                os.remove(path)
        except OSError:
            pass
        self._tts_lib_items = [i for i in self._tts_lib_items if i["path"] != path]
        self._tts_lib_all = [i for i in self._tts_lib_all if i["path"] != path]

    def _tts_clear_all(self):
        for item in list(self._tts_lib_items):
            item["frame"].destroy()
            try:
                if os.path.exists(item["path"]):
                    os.remove(item["path"])
            except OSError:
                pass
        self._tts_lib_items.clear()
        self._tts_lib_all.clear()
        self._tts_status.configure(text="Biblioteca limpiada.", text_color="#AAAAAA")

    def _tts_filter_library(self, *args):
        query = self._tts_filter_var.get().lower()
        for item in self._tts_lib_all:
            if query in item["nombre"].lower() or query in item["path"].lower():
                item["frame"].pack(fill="x", pady=2, padx=2)
            else:
                item["frame"].pack_forget()

    def _tts_refresh_library(self):
        """Escanea la carpeta voces_manuales y recarga la biblioteca."""
        voice_dir = self._get_tts_dir()
        if not os.path.exists(voice_dir):
            return
        existing_paths = {i["path"] for i in self._tts_lib_all}
        for fname in sorted(os.listdir(voice_dir)):
            if not fname.endswith(".wav"):
                continue
            path = os.path.join(voice_dir, fname)
            if path in existing_paths:
                continue
            # Obtener duración
            try:
                import wave as _wave

                with _wave.open(path, "r") as wf:
                    dur = wf.getnframes() / float(wf.getframerate())
            except Exception:
                dur = 0.0
            nombre = fname.replace(".wav", "")
            self._tts_add_to_library(path, nombre, dur)

    def _tts_open_folder(self):
        import subprocess as _sp

        d = self._get_tts_dir()
        os.makedirs(d, exist_ok=True)
        _sp.Popen(["xdg-open", d])

    def _build_marketing_studio(self):
        """
        Marketing Studio - Rediseñado para Planificación y Promoción de Cursos.
        - Panel Izquierdo: Plan de Estudios (Syllabus).
        - Panel Central: Generación de Contenido Promocional (Tráiler, Posts, Blog).
        - Panel Derecho: Títulos Atractivos y Recursos del Curso.
        """
        # Configurar el grid principal de la pestaña de Marketing con 3 columnas
        self.tab4.grid_columnconfigure(0, weight=2)  # Plan de Estudios
        self.tab4.grid_columnconfigure(1, weight=3)  # Contenido Promocional
        self.tab4.grid_columnconfigure(2, weight=2)  # Títulos y Recursos
        self.tab4.grid_rowconfigure(0, weight=1)

        # ════════════════════════════════════════
        # PANEL IZQUIERDO — Plan de Estudios (Syllabus)
        # ════════════════════════════════════════
        syllabus_panel = ctk.CTkFrame(
            self.tab4,
            fg_color=COLORS["bg_panel"],
            corner_radius=10,
            border_width=1,
            border_color=COLORS["border"],
        )
        syllabus_panel.grid(row=0, column=0, sticky="nsew", padx=(8, 4), pady=8)
        syllabus_panel.grid_rowconfigure(2, weight=1)
        syllabus_panel.grid_columnconfigure(0, weight=1)

        # Header
        syllabus_header = ctk.CTkFrame(
            syllabus_panel, fg_color=COLORS["header_bg"], height=40
        )
        syllabus_header.grid(row=0, column=0, sticky="ew")
        ctk.CTkLabel(
            syllabus_header,
            text="📚 PLAN DE ESTUDIOS",
            font=("JetBrains Mono", 12, "bold"),
            text_color="#1E88E5",
        ).pack(side="left", padx=12)

        # Campo para el tema del curso
        syllabus_topic_frame = ctk.CTkFrame(syllabus_panel, fg_color="transparent")
        syllabus_topic_frame.grid(row=1, column=0, sticky="ew", padx=8, pady=8)
        self.mkt_course_topic_entry = ctk.CTkEntry(
            syllabus_topic_frame,
            placeholder_text="Ej: Hacking Ético con Python",
            font=("JetBrains Mono", 11),
        )
        self.mkt_course_topic_entry.pack(
            side="left", fill="x", expand=True, padx=(0, 4)
        )

        # Botones de acción del panel de syllabus
        self.mkt_generate_syllabus_btn = ctk.CTkButton(
            syllabus_topic_frame,
            text="Generar",
            width=80,
            command=lambda: self._mkt_generate_content("syllabus"),
        )
        self.mkt_generate_syllabus_btn.pack(side="left", padx=4)
        self.mkt_load_course_btn = ctk.CTkButton(
            syllabus_topic_frame,
            text="Cargar",
            width=70,
            command=self._mkt_load_course_from_folder,
        )
        self.mkt_load_course_btn.pack(side="left")

        # Área de texto para el plan de estudios
        self.mkt_syllabus_text = ctk.CTkTextbox(
            syllabus_panel,
            font=("JetBrains Mono", 10),
            wrap="word",
            fg_color=COLORS["bg_editor"],
            border_width=0,
        )
        self.mkt_syllabus_text.grid(row=2, column=0, sticky="nsew", padx=8, pady=(0, 8))

        # ════════════════════════════════════════
        # PANEL CENTRAL — Contenido Promocional
        # ════════════════════════════════════════
        promo_panel = ctk.CTkFrame(
            self.tab4,
            fg_color=COLORS["bg_panel"],
            corner_radius=10,
            border_width=1,
            border_color=COLORS["border"],
        )
        promo_panel.grid(row=0, column=1, sticky="nsew", padx=4, pady=8)
        promo_panel.grid_rowconfigure(1, weight=1)
        promo_panel.grid_columnconfigure(0, weight=1)

        # Header y botones de generación
        promo_header = ctk.CTkFrame(
            promo_panel, fg_color=COLORS["header_bg"], height=40
        )
        promo_header.grid(row=0, column=0, sticky="ew")
        ctk.CTkLabel(
            promo_header,
            text="📝 CONTENIDO PROMOCIONAL",
            font=("JetBrains Mono", 12, "bold"),
            text_color="#D81B60",
        ).pack(side="left", padx=12)

        promo_buttons_frame = ctk.CTkFrame(promo_header, fg_color="transparent")
        promo_buttons_frame.pack(side="right", padx=8)
        ctk.CTkButton(
            promo_buttons_frame,
            text="Tráiler",
            command=lambda: self._mkt_generate_content("trailer"),
            width=70,
        ).pack(side="left", padx=2)
        ctk.CTkButton(
            promo_buttons_frame,
            text="Posts",
            command=lambda: self._mkt_generate_content("posts"),
            width=70,
        ).pack(side="left", padx=2)
        ctk.CTkButton(
            promo_buttons_frame,
            text="Blog",
            command=lambda: self._mkt_generate_content("blog"),
            width=70,
        ).pack(side="left", padx=2)

        # Área de texto para el contenido promocional
        self.mkt_promo_content_text = ctk.CTkTextbox(
            promo_panel,
            font=("JetBrains Mono", 10),
            wrap="word",
            fg_color=COLORS["bg_editor"],
            border_width=0,
        )
        self.mkt_promo_content_text.grid(row=1, column=0, sticky="nsew", padx=8, pady=8)

        # ════════════════════════════════════════
        # PANEL DERECHO — Títulos y Recursos
        # ════════════════════════════════════════
        extra_panel = ctk.CTkFrame(
            self.tab4,
            fg_color=COLORS["bg_panel"],
            corner_radius=10,
            border_width=1,
            border_color=COLORS["border"],
        )
        extra_panel.grid(row=0, column=2, sticky="nsew", padx=(4, 8), pady=8)
        extra_panel.grid_rowconfigure(1, weight=1)
        extra_panel.grid_rowconfigure(3, weight=1)
        extra_panel.grid_columnconfigure(0, weight=1)

        # Header Títulos
        titles_header = ctk.CTkFrame(
            extra_panel, fg_color=COLORS["header_bg"], height=40
        )
        titles_header.grid(row=0, column=0, sticky="ew")
        ctk.CTkLabel(
            titles_header,
            text="💡 TÍTULOS ATRACTIVOS",
            font=("JetBrains Mono", 12, "bold"),
            text_color="#FFB300",
        ).pack(side="left", padx=12)
        ctk.CTkButton(
            titles_header,
            text="Generar",
            width=70,
            command=lambda: self._mkt_generate_content("titles"),
        ).pack(side="right", padx=8)

        # Área de texto para títulos
        self.mkt_titles_text = ctk.CTkTextbox(
            extra_panel,
            font=("JetBrains Mono", 10),
            wrap="word",
            fg_color=COLORS["bg_editor"],
            border_width=0,
            height=150,
        )
        self.mkt_titles_text.grid(row=1, column=0, sticky="nsew", padx=8, pady=8)

        # Header Recursos
        resources_header = ctk.CTkFrame(
            extra_panel, fg_color=COLORS["header_bg"], height=40
        )
        resources_header.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        ctk.CTkLabel(
            resources_header,
            text="🔗 RECURSOS DEL CURSO",
            font=("JetBrains Mono", 12, "bold"),
            text_color="#43A047",
        ).pack(side="left", padx=12)

        # Área de texto para recursos
        self.mkt_resources_text = ctk.CTkTextbox(
            extra_panel,
            font=("JetBrains Mono", 10),
            wrap="word",
            fg_color=COLORS["bg_editor"],
            border_width=0,
        )
        self.mkt_resources_text.grid(
            row=3, column=0, sticky="nsew", padx=8, pady=(8, 8)
        )

    def _mkt_generate_content(self, content_type: str):
        topic = self.mkt_course_topic_entry.get()
        if not topic:
            # Reutilizo la función de toast que creamos para Opencode, si no existe la creo.
            if not hasattr(self, "_show_toast"):
                # Simple fallback
                print("ERROR: Por favor, define primero el tema del curso.")
                return
            self._show_toast("ERROR", "Por favor, define primero el tema del curso.")
            return

        target_widget = None
        prompt = ""
        syllabus_content = self.mkt_syllabus_text.get("1.0", "end")

        if content_type == "syllabus":
            target_widget = self.mkt_syllabus_text
            prompt = f"Actúa como un diseñador instruccional experto en ciberseguridad y tecnología. Crea un plan de estudios detallado y completo para un curso online sobre '{topic}'. El resultado debe estar en formato Markdown, estructurado en módulos y lecciones (ej. 1.1, 1.2). Sé exhaustivo, práctico y cubre desde los fundamentos hasta temas avanzados y casos de uso reales."

        elif content_type in ["trailer", "posts", "blog", "titles"]:
            if not syllabus_content.strip() or "Generando" in syllabus_content:
                if not hasattr(self, "_show_toast"):
                    print("ERROR: Primero debes generar el Plan de Estudios.")
                    return
                self._show_toast("ERROR", "Primero debes generar el Plan de Estudios.")
                return

            if content_type == "trailer":
                target_widget = self.mkt_promo_content_text
                prompt = f"Actúa como un guionista de marketing viral para el sector tecnológico. Basado en el siguiente plan de estudios para un curso de '{topic}', escribe un guion de 60 segundos para un tráiler promocional. Formato: Markdown. Debe ser enérgico, atractivo, y enfocado en la transformación y las habilidades que obtendrá el estudiante.\n\nPlan de Estudios:\n{syllabus_content}"
            elif content_type == "posts":
                target_widget = self.mkt_promo_content_text
                prompt = f"Actúa como un Community Manager experto en tech. Basado en el plan de estudios para '{topic}', crea 5 publicaciones para redes sociales (3 para Twitter/X, 2 para LinkedIn) anunciando el nuevo curso. Usa un tono profesional pero entusiasta, y añade hashtags relevantes y llamados a la acción. Formato: Markdown.\n\nPlan de Estudios:\n{syllabus_content}"
            elif content_type == "blog":
                target_widget = self.mkt_promo_content_text
                prompt = f"Actúa como un redactor de contenido SEO especializado en tecnología. Escribe un artículo de blog de ~500 palabras titulado 'Domina {topic}: Anunciamos Nuestro Nuevo Curso Práctico'. El post debe explicar el valor del curso, para quién es, y qué aprenderán, basándose en el siguiente plan de estudios. Formato: Markdown.\n\nPlan de Estudios:\n{syllabus_content}"
            elif content_type == "titles":
                target_widget = self.mkt_titles_text
                prompt = f"Actúa como un experto en copywriting para YouTube. Genera 10 títulos 'clickbait' pero profesionales para videos promocionales de un curso de '{topic}'. Deben crear curiosidad y urgencia. Ejemplo: 'Los 5 secretos de {topic} que las empresas no quieren que sepas'. Formato: lista Markdown.\n\nPlan de Estudios:\n{syllabus_content}"

        if not prompt or not target_widget:
            return

        target_widget.delete("1.0", "end")
        target_widget.insert("1.0", "🧠 Generando con IA...")

        def generation_thread():
            try:
                response = self.ai.chat(prompt)

                def update_ui():
                    target_widget.delete("1.0", "end")
                    target_widget.insert("1.0", response)

                self.after(0, update_ui)
            except Exception as e:
                self.after(0, lambda: target_widget.delete("1.0", "end"))
                self.after(0, lambda: target_widget.insert("1.0", f"Error de IA: {e}"))

        threading.Thread(target=generation_thread, daemon=True).start()

    def _mkt_load_course_from_folder(self):
        """Abre un diálogo para seleccionar una carpeta de curso y carga su estructura."""
        course_path = filedialog.askdirectory(
            title="Selecciona la carpeta principal del curso"
        )
        if not course_path:
            return

        course_name = os.path.basename(course_path)
        self.mkt_course_topic_entry.delete(0, "end")
        self.mkt_course_topic_entry.insert(0, course_name)

        syllabus_md = f"# Plan de Estudios: {course_name}\n\n"

        try:
            # Asumimos que los subdirectorios son los módulos
            modules = sorted(
                [
                    d
                    for d in os.listdir(course_path)
                    if os.path.isdir(os.path.join(course_path, d))
                ]
            )

            for module_name in modules:
                syllabus_md += f"## Módulo: {module_name}\n"
                module_path = os.path.join(course_path, module_name)

                # Asumimos que los archivos .json son los capítulos
                chapters = sorted(
                    [f for f in os.listdir(module_path) if f.endswith(".json")]
                )

                for chapter_file in chapters:
                    # Extraer un nombre más limpio del archivo
                    chapter_name = (
                        os.path.splitext(chapter_file)[0].replace("_", " ").title()
                    )
                    syllabus_md += f"- {chapter_name}\n"

                syllabus_md += "\n"

            self.mkt_syllabus_text.delete("1.0", "end")
            self.mkt_syllabus_text.insert("1.0", syllabus_md)

        except Exception as e:
            self.mkt_syllabus_text.delete("1.0", "end")
            self.mkt_syllabus_text.insert(
                "1.0", f"Error al leer la carpeta del curso:\n\n{e}"
            )

    def _mkt_render_videos(self, tab, videos_data):
        """Renderiza los 15 videos de marketing con editor JSON."""
        main_frame = ctk.CTkFrame(tab, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=5, pady=5)

        if videos_data is None:
            ctk.CTkLabel(
                main_frame,
                text="⚠️ No hay videos generados.\n\nGenera los 15 videos de marketing primero.",
                font=("JetBrains Mono", 11),
                text_color=COLORS["text_dim"],
                justify="center",
            ).pack(pady=40)
            return

        videos = videos_data.get("videos", [])
        curso = videos_data.get("curso", "")

        # Header con info
        header = ctk.CTkFrame(main_frame, fg_color=COLORS["bg_panel"], corner_radius=8)
        header.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            header,
            text=f"📹 {len(videos)} Videos para: {curso}",
            font=("JetBrains Mono", 11, "bold"),
            text_color=COLORS["accent_green"],
        ).pack(anchor="w", padx=10, pady=(8, 4))

        # Resumen de tipos
        tipos_count = {}
        for v in videos:
            tipo = v.get("tipo", "unknown")
            tipos_count[tipo] = tipos_count.get(tipo, 0) + 1

        tipos_text = " • ".join([f"{k}: {v}" for k, v in tipos_count.items()])
        ctk.CTkLabel(
            header,
            text=f"📊 {tipos_text}",
            font=("JetBrains Mono", 9),
            text_color=COLORS["text_dim"],
        ).pack(anchor="w", padx=10, pady=(0, 8))

        # Scrollable para la lista de videos
        scroll = ctk.CTkScrollableFrame(main_frame, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        # Lista de videos
        for idx, video in enumerate(videos):
            nro = video.get("nro", idx + 1)
            tipo = video.get("tipo", "")
            titulo = video.get("titulo", "Sin título")
            red = video.get("red", "")
            duracion = video.get("duracion_seg", 0)
            hook = video.get("hook_primeros_3_seg", "")
            script = video.get("script_completo", "")
            cta = video.get("cta", "")
            hashtags = video.get("hashtags", [])

            tipo_colors = {
                "hook": "#E74C3C",
                "explicativo": "#3498DB",
                "retencion": "#F39C12",
                "venta": "#27AE60",
            }
            tipo_color = tipo_colors.get(tipo, COLORS["accent_cyan"])

            video_frame = ctk.CTkFrame(
                scroll, fg_color=COLORS["bg_panel"], corner_radius=8
            )
            video_frame.pack(fill="x", pady=6, padx=4)

            # Header del video
            vid_header = ctk.CTkFrame(video_frame, fg_color=tipo_color, corner_radius=6)
            vid_header.pack(fill="x", padx=6, pady=(6, 4))

            ctk.CTkLabel(
                vid_header,
                text=f"#{nro} {tipo.upper()} • {red} • {duracion}s",
                font=("JetBrains Mono", 10, "bold"),
                text_color="#FFFFFF",
            ).pack(side="left", padx=8, pady=4)

            ctk.CTkButton(
                vid_header,
                text="📝 Editar JSON",
                command=lambda v=video, t=titulo: self._mkt_open_video_editor(v, t),
                font=("JetBrains Mono", 9),
                fg_color="#1a1a2e",
                hover_color="#2a2a4e",
                text_color="#FFFFFF",
                width=80,
                height=24,
            ).pack(side="right", padx=4, pady=2)

            # Título
            ctk.CTkLabel(
                video_frame,
                text=f"🎬 {titulo}",
                font=("JetBrains Mono", 10, "bold"),
                text_color=COLORS["accent_cyan"],
                wraplength=500,
                justify="left",
            ).pack(anchor="w", padx=10, pady=(4, 2))

            # Hook
            if hook:
                hook_frame = ctk.CTkFrame(
                    video_frame, fg_color="#0d0e1a", corner_radius=4
                )
                hook_frame.pack(fill="x", padx=10, pady=2)
                ctk.CTkLabel(
                    hook_frame,
                    text=f"🎣 HOOK: {hook}",
                    font=("JetBrains Mono", 9),
                    text_color="#FF6B35",
                    wraplength=500,
                    justify="left",
                ).pack(anchor="w", padx=8, pady=4)

            # CTA y hashtags
            bottom = ctk.CTkFrame(video_frame, fg_color="transparent")
            bottom.pack(fill="x", padx=10, pady=(4, 6))

            if cta:
                ctk.CTkLabel(
                    bottom,
                    text=f"👉 {cta}",
                    font=("JetBrains Mono", 9),
                    text_color=COLORS["accent_green"],
                ).pack(side="left")

            if hashtags:
                hashtags_text = " ".join(hashtags[:5])
                ctk.CTkLabel(
                    bottom,
                    text=hashtags_text,
                    font=("JetBrains Mono", 8),
                    text_color=COLORS["text_dim"],
                ).pack(side="right")

        # Botón ver JSON completo
        ctk.CTkButton(
            main_frame,
            text="📄 Ver/Editar JSON Completo",
            command=lambda: self._mkt_open_videos_json_editor(videos_data),
            font=("JetBrains Mono", 11, "bold"),
            fg_color="#ff3333",
            hover_color="#cc2222",
            text_color="#FFFFFF",
            height=40,
        ).pack(fill="x", padx=4, pady=(10, 4))

    def _mkt_open_video_editor(self, video_data, titulo):
        """Abre editor JSON para un video individual."""
        popup = ctk.CTkToplevel(self)
        popup.title(f"Editar Video: {titulo}")
        popup.geometry("900x700")

        # Header
        header = ctk.CTkFrame(
            popup, fg_color=COLORS["header_bg"], height=40, corner_radius=0
        )
        header.pack(fill="x")
        ctk.CTkLabel(
            header,
            text=f"📹 Editor JSON - {titulo}",
            font=("JetBrains Mono", 12, "bold"),
            text_color="#FF6B35",
        ).pack(side="left", padx=10, pady=8)

        # Editor JSON
        editor_frame = ctk.CTkFrame(popup, fg_color="#08090a")
        editor_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        editor = tk.Text(
            editor_frame,
            bg="#08090a",
            fg="#a0ffa0",
            font=("JetBrains Mono", 10),
            insertbackground=COLORS["accent_green"],
            relief="flat",
        )
        editor.pack(fill="both", expand=True)

        json_str = json.dumps(video_data, indent=4, ensure_ascii=False)
        editor.insert("1.0", json_str)

        # Botones
        btn_frame = ctk.CTkFrame(popup, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=(0, 10))

        def save_video():
            try:
                new_data = json.loads(editor.get("1.0", "end"))
                idx = video_data.get("nro", 1) - 1
                if hasattr(self, "course_orchestrator") and self.course_orchestrator:
                    if hasattr(self.course_orchestrator, "_mkt_videos_data"):
                        videos_list = self.course_orchestrator._mkt_videos_data.get(
                            "videos", []
                        )
                        if 0 <= idx < len(videos_list):
                            videos_list[idx] = new_data
                            course_dir = self.course_orchestrator._course_dir
                            if course_dir:
                                import os

                                path = os.path.join(
                                    course_dir, "marketing", "videos_marketing.json"
                                )
                                with open(path, "w", encoding="utf-8") as f:
                                    json.dump(
                                        self.course_orchestrator._mkt_videos_data,
                                        f,
                                        indent=4,
                                        ensure_ascii=False,
                                    )
                popup.destroy()
                self.append_chat("Sistema", "✅ Video actualizado")
            except json.JSONDecodeError:
                self.append_chat("Error", "❌ JSON inválido")

        ctk.CTkButton(
            btn_frame,
            text="💾 Guardar",
            command=save_video,
            font=("JetBrains Mono", 10, "bold"),
            fg_color="#27AE60",
            hover_color="#229954",
            text_color="#FFFFFF",
            height=35,
        ).pack(side="left", fill="x", expand=True, padx=(0, 5))

        ctk.CTkButton(
            btn_frame,
            text="❌ Cerrar",
            command=popup.destroy,
            font=("JetBrains Mono", 10),
            fg_color="#E74C3C",
            hover_color="#C0392B",
            text_color="#FFFFFF",
            height=35,
        ).pack(side="right", fill="x", expand=True, padx=(5, 0))

    def _mkt_open_videos_json_editor(self, videos_data):
        """Abre editor JSON para todos los videos."""
        popup = ctk.CTkToplevel(self)
        popup.title("📹 15 Videos de Marketing - Editor JSON")
        popup.geometry("1000x800")

        # Header
        header = ctk.CTkFrame(
            popup, fg_color=COLORS["header_bg"], height=40, corner_radius=0
        )
        header.pack(fill="x")
        ctk.CTkLabel(
            header,
            text="📹 Editor JSON - 15 Videos de Marketing",
            font=("JetBrains Mono", 12, "bold"),
            text_color="#ff3333",
        ).pack(side="left", padx=10, pady=8)

        # Botón abrir carpeta
        def open_folder():
            if hasattr(self, "course_orchestrator") and self.course_orchestrator:
                course_dir = self.course_orchestrator._course_dir
                if course_dir:
                    import subprocess

                    mkt_dir = os.path.join(course_dir, "marketing")
                    os.makedirs(mkt_dir, exist_ok=True)
                    subprocess.Popen(["xdg-open", mkt_dir])

        ctk.CTkButton(
            header,
            text="📂 Abrir Carpeta",
            command=open_folder,
            font=("JetBrains Mono", 9),
            fg_color="#1a1a2e",
            hover_color="#2a2a4e",
            text_color="#FFFFFF",
            width=100,
        ).pack(side="right", padx=10, pady=4)

        # Editor JSON
        editor_frame = ctk.CTkFrame(popup, fg_color="#08090a")
        editor_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        editor = tk.Text(
            editor_frame,
            bg="#08090a",
            fg="#a0ffa0",
            font=("JetBrains Mono", 9),
            insertbackground=COLORS["accent_green"],
            relief="flat",
        )
        editor.pack(fill="both", expand=True)

        json_str = json.dumps(videos_data, indent=4, ensure_ascii=False)
        editor.insert("1.0", json_str)

        # Botones
        btn_frame = ctk.CTkFrame(popup, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=(0, 10))

        def save_all():
            try:
                new_data = json.loads(editor.get("1.0", "end"))
                if hasattr(self, "course_orchestrator") and self.course_orchestrator:
                    self.course_orchestrator._mkt_videos_data = new_data
                    course_dir = self.course_orchestrator._course_dir
                    if course_dir:
                        path = os.path.join(
                            course_dir, "marketing", "videos_marketing.json"
                        )
                        os.makedirs(os.path.dirname(path), exist_ok=True)
                        with open(path, "w", encoding="utf-8") as f:
                            json.dump(new_data, f, indent=4, ensure_ascii=False)
                popup.destroy()
                self.append_chat("Sistema", "✅ Videos actualizados correctamente")
            except json.JSONDecodeError as e:
                self.append_chat("Error", f"❌ JSON inválido: {e}")

        def copy_json():
            popup.clipboard_clear()
            popup.clipboard_append(editor.get("1.0", "end"))

        ctk.CTkButton(
            btn_frame,
            text="💾 Guardar Todo",
            command=save_all,
            font=("JetBrains Mono", 10, "bold"),
            fg_color="#27AE60",
            hover_color="#229954",
            text_color="#FFFFFF",
            height=35,
        ).pack(side="left", fill="x", expand=True, padx=(0, 5))

        ctk.CTkButton(
            btn_frame,
            text="📋 Copiar JSON",
            command=copy_json,
            font=("JetBrains Mono", 10),
            fg_color="#3498DB",
            hover_color="#2980B9",
            text_color="#FFFFFF",
            height=35,
        ).pack(side="left", fill="x", expand=True, padx=(0, 5))

        ctk.CTkButton(
            btn_frame,
            text="❌ Cerrar",
            command=popup.destroy,
            font=("JetBrains Mono", 10),
            fg_color="#E74C3C",
            hover_color="#C0392B",
            text_color="#FFFFFF",
            height=35,
        ).pack(side="right", fill="x", expand=True, padx=(5, 0))

    def _mkt_render_dict(self, parent, data, depth=0):
        """Renderiza un diccionario de forma visual."""
        for key, value in data.items():
            if isinstance(value, dict):
                frame = ctk.CTkFrame(
                    parent, fg_color=COLORS["bg_panel"], corner_radius=6
                )
                frame.pack(fill="x", pady=4, padx=(depth * 10, 0))

                ctk.CTkLabel(
                    frame,
                    text=f"🔹 {key.upper()}",
                    font=("JetBrains Mono", 10, "bold"),
                    text_color=COLORS["accent_cyan"],
                ).pack(anchor="w", padx=10, pady=(8, 4))

                inner = ctk.CTkFrame(frame, fg_color="transparent")
                inner.pack(fill="x", padx=(20, 10), pady=(0, 8))
                self._mkt_render_dict(inner, value, depth + 1)

            elif isinstance(value, list):
                ctk.CTkLabel(
                    parent,
                    text=f"📋 {key.upper()}:",
                    font=("JetBrains Mono", 10, "bold"),
                    text_color=COLORS["accent_yellow"],
                ).pack(anchor="w", pady=(8, 2))

                for item in value:
                    if isinstance(item, dict):
                        self._mkt_render_dict(parent, item, depth)
                    else:
                        ctk.CTkLabel(
                            parent,
                            text=f"  • {item}",
                            font=("JetBrains Mono", 9),
                            text_color=COLORS["text_primary"],
                        ).pack(anchor="w", padx=10)
            else:
                value_str = str(value)
                if key == "precio":
                    value_str = f"${value}"

                color = COLORS["text_primary"]
                if "precio" in key.lower():
                    color = "#27AE60"
                elif "cta" in key.lower() or "irresistible" in key.lower():
                    color = "#FF6B35"

                value_frame = ctk.CTkFrame(
                    parent, fg_color=COLORS["bg_panel"], corner_radius=4
                )
                value_frame.pack(fill="x", pady=1, padx=(depth * 10, 0))

                ctk.CTkLabel(
                    value_frame,
                    text=f"{key}: {value_str}",
                    font=("JetBrains Mono", 9),
                    text_color=color,
                    wraplength=500,
                    justify="left",
                ).pack(anchor="w", padx=10, pady=4)

    def _mkt_render_list(self, parent, data):
        """Renderiza una lista de forma visual."""
        for idx, item in enumerate(data):
            if isinstance(item, dict):
                self._mkt_render_dict(parent, item)
            else:
                ctk.CTkLabel(
                    parent,
                    text=f"  • {item}",
                    font=("JetBrains Mono", 9),
                    text_color=COLORS["text_primary"],
                ).pack(anchor="w", padx=10)

    def _mkt_generate_from_studio(self):
        """Genera el marketing desde el estudio."""
        if not hasattr(self, "course_orchestrator"):
            self.append_chat("Error", "❌ No hay orquestador de curso")
            return

        if not self.course_orchestrator.master_course_structure:
            self.append_chat("Error", "❌ Genera primero la estructura del curso")
            return

        self.course_orchestrator.ai = self.ai
        self.append_chat("Sistema", "🚀 Generando Marketing Launch Kit...")

        self._btn_mkt_generate.configure(state="disabled", text="⏳ Generando...")

        def on_success(json_data, path):
            self.course_orchestrator._mkt_data = json_data
            self.after(
                0,
                lambda: self._btn_mkt_generate.configure(
                    state="normal", text="✅ Marketing Generado"
                ),
            )
            self.after(0, self._mkt_on_generated, json_data, path)

        def on_error(msg):
            self.after(0, self.append_chat, "Error", f"❌ Error: {msg}")
            self.after(
                0,
                lambda: self._btn_mkt_generate.configure(
                    state="normal", text="🚀 Generar Marketing Launch Kit"
                ),
            )

        self.course_orchestrator.generate_marketing_plan(on_success, on_error)

    def _mkt_on_generated(self, json_data, path):
        """Callback cuando se genera el marketing."""
        self.append_chat("Sistema", "✅ Marketing Launch Kit generado")
        self.append_chat("Sistema", f"📁 {path}")

        # Actualizar info del curso
        if hasattr(self, "course_orchestrator"):
            course = self.course_orchestrator.master_course_structure
            if course:
                titulo = course.get("titulo_curso", "Sin título")
                nivel = course.get("nivel", "-")

                for child in self._mkt_course_info.winfo_children():
                    if isinstance(child, ctk.CTkLabel):
                        text = child.cget("text")
                        if "📚" in text:
                            child.configure(text=f"📚 {titulo[:40]}")
                        elif "🎯" in text:
                            child.configure(text=f"🎯 Nivel: {nivel}")

        # Mostrar sección de pricing por defecto
        self._mkt_show_section("pricing")

    def _mkt_generate_videos(self):
        """Genera los 15 videos de marketing."""
        if not hasattr(self, "course_orchestrator"):
            self.append_chat("Error", "❌ No hay orquestador de curso")
            return

        if not self.course_orchestrator.master_course_structure:
            self.append_chat("Error", "❌ Genera primero la estructura del curso")
            return

        self.course_orchestrator.ai = self.ai
        self.append_chat("Sistema", "📹 Generando 15 Videos de Marketing...")

        self._btn_mkt_videos.configure(state="disabled", text="⏳ Generando Videos...")

        def on_success(json_data, path):
            self.course_orchestrator._mkt_videos_data = json_data
            self.after(
                0,
                lambda: self._btn_mkt_videos.configure(
                    state="normal", text="✅ Videos Generados"
                ),
            )
            self.after(
                0, lambda: self._btn_mkt_videos.configure(text="📹 Regenerar Videos")
            )
            self.after(
                0,
                lambda: self.append_chat(
                    "Sistema", "✅ 15 Videos de Marketing generados"
                ),
            )
            self.after(0, lambda: self.append_chat("Sistema", f"📁 {path}"))
            self.after(0, self._mkt_show_section, "videos")

        def on_error(msg):
            self.after(0, self.append_chat, "Error", f"❌ Error: {msg}")
            self.after(
                0,
                lambda: self._btn_mkt_videos.configure(
                    state="normal", text="📹 Generar 15 Videos de Marketing"
                ),
            )

        self.course_orchestrator.generate_marketing_videos(on_success, on_error)

    def _mkt_load_course(self):
        """Carga un curso existente desde carpeta."""
        from tkinter import filedialog

        folder = filedialog.askdirectory(
            title="Seleccionar carpeta del curso",
            initialdir=self.course_orchestrator.projects_dir
            if hasattr(self.course_orchestrator, "projects_dir")
            else ".",
        )

        if not folder:
            return

        try:
            structure = self.course_orchestrator.load_course_structure(folder)
            if structure:
                titulo = structure.get("titulo_curso", "Sin título")
                nivel = structure.get("nivel", "-")
                num_modulos = len(structure.get("modulos", []))

                self.append_chat("Sistema", f"✅ Curso cargado: {titulo}")
                self.append_chat("Sistema", f"📚 {num_modulos} módulos")

                # Actualizar UI de info
                for child in self._mkt_course_info.winfo_children():
                    if isinstance(child, ctk.CTkLabel):
                        text = child.cget("text")
                        if "📚" in text:
                            child.configure(text=f"📚 {titulo[:40]}")
                        elif "🎯" in text:
                            child.configure(text=f"🎯 Nivel: {nivel}")

                # Mostrar descripción completa
                self._mkt_show_full_description(structure)
            else:
                self.append_chat(
                    "Error", "❌ No se encontró estructura de curso en la carpeta"
                )
        except Exception as e:
            self.append_chat("Error", f"❌ Error cargando curso: {e}")

    def _mkt_generate_full_description(self):
        """Genera la descripción completa del curso para Hotmart."""
        if not self.course_orchestrator.master_course_structure:
            self.append_chat("Error", "❌ Carga primero un curso")
            return

        self.append_chat("Sistema", "📝 Generando descripción completa...")

        # Obtener la descripción del orchestrator
        full_desc = self.course_orchestrator.get_course_description_full()

        if full_desc:
            self._mkt_show_full_description(
                self.course_orchestrator.master_course_structure
            )
            self.append_chat("Sistema", "✅ Descripción completa generada")
        else:
            self.append_chat("Error", "❌ Error generando descripción")

    def _mkt_show_full_description(self, structure):
        """Muestra la descripción completa del curso."""
        # Limpiar tabs existentes
        for tab_name in list(self._mkt_content_tabs._tab_dict.keys()):
            try:
                self._mkt_content_tabs.delete(tab_name)
            except:
                pass

        # Agregar tab de descripción completa
        self._mkt_content_tabs.add("📋 Descripción Completa")
        desc_tab = self._mkt_content_tabs.tab("📋 Descripción Completa")

        # Scroll frame
        scroll = ctk.CTkScrollableFrame(desc_tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=10)

        # Título del curso
        titulo = structure.get("titulo_curso", "Sin título")
        ctk.CTkLabel(
            scroll,
            text=f"#{titulo}",
            font=("JetBrains Mono", 16, "bold"),
            text_color="#FF6B35",
        ).pack(pady=(10, 5))

        # Info general
        info_frame = ctk.CTkFrame(scroll, fg_color=COLORS["bg_panel"], corner_radius=8)
        info_frame.pack(fill="x", pady=10)

        instructor = structure.get("instructor", "kr-clidn")
        nivel = structure.get("nivel", "Todos los niveles")
        duracion = structure.get("duracion_total", "Por definir")

        ctk.CTkLabel(
            info_frame,
            text=f"**Instructor:** {instructor}",
            font=("JetBrains Mono", 10),
            text_color=COLORS["accent_cyan"],
        ).pack(anchor="w", padx=10, pady=(8, 2))

        ctk.CTkLabel(
            info_frame,
            text=f"**Nivel:** {nivel}",
            font=("JetBrains Mono", 10),
            text_color=COLORS["text_primary"],
        ).pack(anchor="w", padx=10, pady=(0, 2))

        ctk.CTkLabel(
            info_frame,
            text=f"**Duración:** {duracion}",
            font=("JetBrains Mono", 10),
            text_color=COLORS["text_primary"],
        ).pack(anchor="w", padx=10, pady=(0, 8))

        # Objetivo principal
        objetivo = structure.get("objetivo_principal", "")
        if objetivo:
            ctk.CTkLabel(
                scroll,
                text="🎯 Objetivo Principal",
                font=("JetBrains Mono", 12, "bold"),
                text_color=COLORS["accent_green"],
            ).pack(anchor="w", pady=(10, 5))
            ctk.CTkLabel(
                scroll,
                text=objetivo,
                font=("JetBrains Mono", 10),
                text_color=COLORS["text_primary"],
                wraplength=600,
                justify="left",
            ).pack(anchor="w", pady=(0, 10))

        # Módulos
        ctk.CTkLabel(
            scroll,
            text="📚 Contenido del Curso",
            font=("JetBrains Mono", 14, "bold"),
            text_color=COLORS["accent_yellow"],
        ).pack(anchor="w", pady=(10, 10))

        for mod in structure.get("modulos", []):
            nro = mod.get("nro", "?")
            titulo_mod = mod.get("titulo", "")
            descripcion = mod.get("descripcion", "")
            capitulos = mod.get("capitulos", [])

            # Frame del módulo
            mod_frame = ctk.CTkFrame(
                scroll, fg_color=COLORS["bg_panel"], corner_radius=8
            )
            mod_frame.pack(fill="x", pady=8)

            # Header del módulo
            ctk.CTkLabel(
                mod_frame,
                text=f"📦 Módulo {nro}: {titulo_mod}",
                font=("JetBrains Mono", 11, "bold"),
                text_color=COLORS["accent_green"],
            ).pack(anchor="w", padx=10, pady=(10, 5))

            # Descripción del módulo
            if descripcion:
                desc_label = ctk.CTkLabel(
                    mod_frame,
                    text=descripcion,
                    font=("JetBrains Mono", 9),
                    text_color=COLORS["text_primary"],
                    wraplength=550,
                    justify="left",
                )
                desc_label.pack(anchor="w", padx=10, pady=(0, 5))

            # Capítulos
            ctk.CTkLabel(
                mod_frame,
                text="📺 Capítulos:",
                font=("JetBrains Mono", 10, "bold"),
                text_color=COLORS["accent_cyan"],
            ).pack(anchor="w", padx=10, pady=(5, 2))

            for cap in capitulos:
                cap_nro = cap.get("nro", "?")
                cap_titulo = cap.get("titulo", "")
                cap_desc = cap.get("descripcion", "")

                cap_frame = ctk.CTkFrame(
                    mod_frame, fg_color=COLORS["bg_dark"], corner_radius=4
                )
                cap_frame.pack(fill="x", padx=10, pady=4)

                ctk.CTkLabel(
                    cap_frame,
                    text=f"  C{cap_nro}: {cap_titulo}",
                    font=("JetBrains Mono", 9, "bold"),
                    text_color=COLORS["text_primary"],
                ).pack(anchor="w", padx=5, pady=(4, 2))

                if cap_desc:
                    ctk.CTkLabel(
                        cap_frame,
                        text=f"      {cap_desc[:100]}...",
                        font=("JetBrains Mono", 8),
                        text_color=COLORS["text_dim"],
                        wraplength=500,
                        justify="left",
                    ).pack(anchor="w", padx=5, pady=(0, 4))

            # Espaciado
            ctk.CTkLabel(mod_frame, text="").pack(pady=5)

        # Botón guardar
        btn_guardar = ctk.CTkButton(
            scroll,
            text="💾 Guardar Descripción",
            command=lambda: self._mkt_save_description(structure),
            font=("JetBrains Mono", 11, "bold"),
            fg_color="#27AE60",
            hover_color="#229954",
            text_color="#FFFFFF",
            height=40,
        )
        btn_guardar.pack(pady=20)

        # Seleccionar el tab
        self._mkt_content_tabs.set("📋 Descripción Completa")

    def _mkt_save_description(self, structure):
        """Guarda la descripción completa del curso."""
        try:
            desc_path = self.course_orchestrator._course_dir
            if desc_path:
                full_path = os.path.join(desc_path, "descripcion_completa.md")
                full_desc = self.course_orchestrator.get_course_description_full()
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(full_desc)
                self.append_chat("Sistema", f"✅ Descripción guardada en: {full_path}")
            else:
                self.append_chat("Error", "❌ No hay curso activo")
        except Exception as e:
            self.append_chat("Error", f"❌ Error guardando: {e}")

    def _build_postprod_tab(self):
        """Pestaña 2: Orquestador de Series y Cursos."""
        self.tab2.grid_rowconfigure(0, weight=1)
        self.tab2.grid_columnconfigure(0, weight=1)  # Panel Estructura
        self.tab2.grid_columnconfigure(1, weight=3)  # Panel View JSONs

        # ── PANEL IZQUIERDO: Estructura de la Serie ──
        left_panel = ctk.CTkFrame(
            self.tab2,
            fg_color=COLORS["bg_panel"],
            corner_radius=10,
            border_width=1,
            border_color=COLORS["border"],
        )
        left_panel.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)

        lh = ctk.CTkFrame(
            left_panel, fg_color=COLORS["header_bg"], height=40, corner_radius=0
        )
        lh.pack(fill="x")
        lh.pack_propagate(False)

        # Header dinámico (series/curso)
        self.series_header_label = ctk.CTkLabel(lh, text="📚", font=("Arial", 18))
        self.series_header_label.pack(side="left", padx=(12, 4))
        self.series_title_label = ctk.CTkLabel(
            lh,
            text="PLANIFICADOR DE SERIE",
            font=("JetBrains Mono", 12, "bold"),
            text_color=COLORS["accent_cyan"],
        )
        self.series_title_label.pack(side="left")

        # Controles
        ctrl_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        ctrl_frame.pack(fill="x", padx=10, pady=10)

        # ── SELECTOR SERIE / CURSO ──
        ctk.CTkLabel(
            ctrl_frame,
            text="Tipo de Contenido:",
            font=("JetBrains Mono", 10, "bold"),
            text_color=COLORS["text_dim"],
        ).pack(anchor="w", pady=(0, 4))

        # Variable para el toggle Serie/Curso
        self.content_type_var = ctk.StringVar(value="📺 Serie")
        self.content_type_seg = ctk.CTkSegmentedButton(
            ctrl_frame,
            values=["📺 Serie", "🎓 Curso"],
            variable=self.content_type_var,
            command=self._on_content_type_change,
            selected_color=COLORS["accent_red"],
            selected_hover_color="#9c27b0",
            unselected_color=COLORS["bg_panel"],
            unselected_hover_color="#2a2b3e",
            text_color="#ffffff",
            font=("JetBrains Mono", 10, "bold"),
        )
        self.content_type_seg.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(
            ctrl_frame,
            text="Tema Principal:",
            font=("JetBrains Mono", 10, "bold"),
            text_color=COLORS["text_dim"],
        ).pack(anchor="w", pady=(0, 2))
        self.series_topic_entry = ctk.CTkEntry(
            ctrl_frame,
            placeholder_text="Ej: Nmap de Cero a Experto...",
            font=("JetBrains Mono", 11),
            fg_color=COLORS["bg_dark"],
            border_color=COLORS["border"],
        )
        self.series_topic_entry.pack(fill="x", pady=(0, 8))

        # ── CONFIGURACIÓN DE MÓDULOS (solo para cursos) ──
        self.modules_config_frame = ctk.CTkFrame(ctrl_frame, fg_color="transparent")
        # Oculto inicialmente, se muestra cuando es curso
        self.modules_config_frame.pack(fill="x", pady=(0, 8))

        # Número de módulos
        modules_row = ctk.CTkFrame(self.modules_config_frame, fg_color="transparent")
        modules_row.pack(fill="x")
        ctk.CTkLabel(
            modules_row,
            text="# Módulos:",
            font=("JetBrains Mono", 10, "bold"),
            text_color=COLORS["text_dim"],
        ).pack(side="left")
        self.course_modules_var = ctk.StringVar(value="8")
        self.course_modules_combo = ctk.CTkComboBox(
            modules_row,
            values=[str(i) for i in range(1, 31)],
            variable=self.course_modules_var,
            width=60,
            font=("JetBrains Mono", 11),
            fg_color=COLORS["bg_dark"],
            border_color=COLORS["border"],
        )
        self.course_modules_combo.pack(side="left", padx=(4, 10))

        # Nivel del curso
        nivel_row = ctk.CTkFrame(self.modules_config_frame, fg_color="transparent")
        nivel_row.pack(fill="x", pady=(4, 0))
        ctk.CTkLabel(
            nivel_row,
            text="Nivel:",
            font=("JetBrains Mono", 10, "bold"),
            text_color=COLORS["text_dim"],
        ).pack(side="left")
        self.course_nivel_var = ctk.StringVar(value="principiante")
        self.course_nivel_combo = ctk.CTkOptionMenu(
            nivel_row,
            values=["principiante", "intermedio", "avanzado"],
            variable=self.course_nivel_var,
            font=("JetBrains Mono", 10),
            fg_color=COLORS["bg_dark"],
            button_color=COLORS["accent_cyan"],
            button_hover_color="#00b8d4",
            width=120,
        )
        self.course_nivel_combo.pack(side="left", padx=(8, 0))

        # Nota: Capítulos por módulo se generan automáticamente según el tema
        ctk.CTkLabel(
            self.modules_config_frame,
            text="📚 Los capítulos se generan automáticamente según el tema",
            font=("JetBrains Mono", 9),
            text_color=COLORS["accent_green"],
        ).pack(anchor="w", pady=(8, 0))

        # Botón generar curso (dentro del frame de config para modo curso)
        self.btn_generate_course = ctk.CTkButton(
            self.modules_config_frame,
            text="✨ Generar Estructura del Curso",
            command=self._generate_master_structure,
            font=("JetBrains Mono", 10, "bold"),
            fg_color="#ff3333",
            hover_color="#cc2222",
            height=35,
        )
        self.btn_generate_course.pack(fill="x", pady=(10, 0))

        # Ocultar configuración de módulos inicialmente (modo serie)
        for widget in self.modules_config_frame.winfo_children():
            widget.pack_forget()

        # Selector de Modo (DUAL AI / SOLO TERM)
        mode_frame = ctk.CTkFrame(ctrl_frame, fg_color="transparent")
        mode_frame.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(
            mode_frame,
            text="Estrategia de Ejecución:",
            font=("JetBrains Mono", 10, "bold"),
            text_color=COLORS["text_dim"],
        ).pack(side="left")
        self.orchestrator_mode_var = ctk.StringVar(value="DUAL AI")
        self.orchestrator_mode_seg = ctk.CTkSegmentedButton(
            mode_frame,
            values=["DUAL AI", "SOLO TERM", "OPERATIVO"],
            variable=self.orchestrator_mode_var,
            selected_color=COLORS["accent_red"],
            selected_hover_color="#00b8d4",
            unselected_color=COLORS["bg_dark"],
            unselected_hover_color="#2a2b3e",
            text_color=COLORS["text_primary"],
            font=("JetBrains Mono", 10, "bold"),
        )
        self.orchestrator_mode_seg.pack(
            side="right", fill="x", expand=True, padx=(10, 0)
        )

        # Selector de Formato
        format_frame = ctk.CTkFrame(ctrl_frame, fg_color="transparent")
        format_frame.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(
            format_frame,
            text="Formato de Video:",
            font=("JetBrains Mono", 10, "bold"),
            text_color=COLORS["text_dim"],
        ).pack(side="left")
        self.orchestrator_format_var = ctk.StringVar(value="16:9 (YouTube)")
        self.orchestrator_format_seg = ctk.CTkSegmentedButton(
            format_frame,
            values=["16:9 (YouTube)", "9:16 (Vertical)"],
            variable=self.orchestrator_format_var,
            selected_color="#ff3333",
            selected_hover_color="#cc2222",
            unselected_color=COLORS["bg_dark"],
            unselected_hover_color="#2a2b3e",
            text_color=COLORS["text_primary"],
            font=("JetBrains Mono", 10, "bold"),
        )
        self.orchestrator_format_seg.pack(
            side="right", fill="x", expand=True, padx=(10, 0)
        )

        # Fila para # Capítulos/Módulos y Botón Generar
        self.chapters_row = ctk.CTkFrame(ctrl_frame, fg_color="transparent")
        self.chapters_row.pack(fill="x")

        # Etiqueta dinámica para Capítulos/Módulos
        self.chapters_label = ctk.CTkLabel(
            self.chapters_row,
            text="# Capítulos:",
            font=("JetBrains Mono", 10, "bold"),
            text_color=COLORS["text_dim"],
        )
        self.chapters_label.pack(side="left")
        self.series_chapters_var = ctk.StringVar(value="5")
        # Selector: 1-20 para series, 8-30 para cursos
        self.series_chapters_combo = ctk.CTkComboBox(
            self.chapters_row,
            values=[str(i) for i in range(1, 21)],
            variable=self.series_chapters_var,
            width=60,
            font=("JetBrains Mono", 11),
            fg_color=COLORS["bg_dark"],
            border_color=COLORS["border"],
        )
        self.series_chapters_combo.pack(side="left", padx=(4, 10))

        self.btn_generate_master = ctk.CTkButton(
            self.chapters_row,
            text="⚡ GENERAR",
            command=self._generate_master_structure,
            font=("JetBrains Mono", 12, "bold"),
            fg_color=COLORS["accent_red"],
            hover_color=COLORS["accent_red_dim"],
            text_color="#ffffff",
            border_width=0,
            corner_radius=6,
            height=36,
        )
        self.btn_generate_master.pack(side="right", fill="x", expand=True, padx=(4, 0))

        # Separador
        ctk.CTkFrame(left_panel, height=1, fg_color=COLORS["border"]).pack(
            fill="x", padx=10, pady=5
        )

        # Lista de capítulos generados
        ctk.CTkLabel(
            left_panel,
            text="Estructura Generada:",
            font=("JetBrains Mono", 10, "bold"),
            text_color=COLORS["text_dim"],
        ).pack(anchor="w", padx=10)
        self.chapters_list_frame = ctk.CTkScrollableFrame(
            left_panel,
            fg_color=COLORS["bg_dark"],
            corner_radius=6,
            border_width=1,
            border_color=COLORS["border"],
        )
        self.chapters_list_frame.pack(fill="both", expand=True, padx=10, pady=(4, 10))

        # Botón Render de Serie Completa
        self.btn_render_series = ctk.CTkButton(
            left_panel,
            text="🎬 Renderizar Serie Completa",
            command=self._render_series,
            font=("JetBrains Mono", 12, "bold"),
            fg_color=COLORS["accent_green"],
            hover_color="#00A23D",
            text_color="#000000",
            height=40,
        )
        self.btn_render_series.pack(fill="x", padx=10, pady=(0, 10))

        # ── PANEL DERECHO: Editores Dinámicos (CTkTabview) ──
        right_panel = ctk.CTkFrame(
            self.tab2,
            fg_color=COLORS["bg_panel"],
            corner_radius=10,
            border_width=1,
            border_color=COLORS["border"],
        )
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(0, 6), pady=6)
        right_panel.grid_rowconfigure(1, weight=1)
        right_panel.grid_columnconfigure(0, weight=1)

        rh = ctk.CTkFrame(
            right_panel, fg_color=COLORS["header_bg"], height=40, corner_radius=0
        )
        rh.grid(row=0, column=0, sticky="ew")
        rh.grid_propagate(False)
        ctk.CTkLabel(rh, text="📝", font=("Arial", 18)).pack(side="left", padx=(12, 4))
        ctk.CTkLabel(
            rh,
            text="EDITORES DE CAPÍTULOS",
            font=("JetBrains Mono", 12, "bold"),
            text_color=COLORS["accent_yellow"],
        ).pack(side="left")

        # Tabview de MÓDULOS (cada módulo tiene sus capítulos) - DARK RED TEAM STYLE
        self.modules_tabview = ctk.CTkTabview(
            right_panel,
            fg_color=COLORS["bg_dark"],
            segmented_button_fg_color=COLORS["bg_panel"],
            segmented_button_selected_color=COLORS["accent_red"],  # Rojo accent
            segmented_button_selected_hover_color=COLORS["accent_red_dim"],
            segmented_button_unselected_color=COLORS["bg_dark"],
            segmented_button_unselected_hover_color=COLORS["bg_hover"],
            text_color=COLORS["text_primary"],
            corner_radius=8,
        )
        self.modules_tabview.grid(row=1, column=0, sticky="nsew", padx=6, pady=(0, 6))

        # Tabview de capítulos (se crea dinámicamente por módulo)
        self._module_chapter_tabs = {}  # {nro_mod: CTkTabview}

        # Tab inicial de Bienvenida
        welcome_tab = self.modules_tabview.add("📋 Bienvenido")
        welcome_label = ctk.CTkLabel(
            welcome_tab,
            text="👈 Selecciona un módulo para ver sus capítulos\no genera un capítulo para que aparezca aquí",
            font=("JetBrains Mono", 12),
            text_color=COLORS["text_dim"],
            justify="center",
        )
        welcome_label.pack(pady=50)

        # ── LOG DEL ORQUESTADOR (muestra progreso TTS y generación) ──
        orch_log_header = ctk.CTkFrame(
            right_panel, fg_color=COLORS["header_bg"], height=28, corner_radius=0
        )
        orch_log_header.grid(row=2, column=0, sticky="ew", padx=6, pady=(4, 0))
        ctk.CTkLabel(
            orch_log_header,
            text="📋 LOG DEL ORQUESTADOR",
            font=("JetBrains Mono", 10, "bold"),
            text_color=COLORS["accent_cyan"],
        ).pack(side="left", padx=8, pady=3)
        ctk.CTkButton(
            orch_log_header,
            text="🗑 Limpiar",
            command=lambda: (
                self.orch_log_box.configure(state="normal"),
                self.orch_log_box.delete("1.0", "end"),
                self.orch_log_box.configure(state="disabled"),
            ),
            fg_color="transparent",
            hover_color="#2a2b3e",
            font=("JetBrains Mono", 9),
            height=22,
            width=70,
        ).pack(side="right", padx=4, pady=2)

        self.orch_log_box = ctk.CTkTextbox(
            right_panel,
            font=("JetBrains Mono", 10),
            fg_color="#080810",
            text_color="#CCCCCC",
            border_color=COLORS["border"],
            border_width=1,
            height=120,
            state="disabled",
            wrap="word",
        )
        self.orch_log_box.grid(row=3, column=0, sticky="ew", padx=6, pady=(0, 4))

        # Botones de Lanzar Capítulo Individual - DARK RED TEAM
        chap_btn_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
        chap_btn_frame.grid(row=4, column=0, sticky="ew", padx=6, pady=(0, 6))

        self.btn_chap_duo = ctk.CTkButton(
            chap_btn_frame,
            text="🎭 Lanzar Cap (Duo)",
            command=lambda: self._launch_director(auto_record=False, is_solo=False),
            font=("JetBrains Mono", 11, "bold"),
            fg_color=COLORS["accent_red"],  # Rojo accent
            hover_color=COLORS["accent_red_dim"],
            text_color="#ffffff",
            border_color=COLORS["accent_red"],
            border_width=1,
        )
        self.btn_chap_duo.pack(side="left", padx=(0, 5), expand=True, fill="x")

        self.btn_chap_solo = ctk.CTkButton(
            chap_btn_frame,
            text="🖥️ Lanzar Cap (Solo)",
            command=lambda: self._launch_director(auto_record=False, is_solo=True),
            font=("JetBrains Mono", 11, "bold"),
            fg_color=COLORS["accent_cyan"],  # Cyan accent
            hover_color=COLORS["accent_cyan_dim"],
            text_color="#000000",
            border_color=COLORS["accent_cyan"],
            border_width=1,
        )
        self.btn_chap_solo.pack(side="left", padx=5, expand=True, fill="x")

        # Botón OSINT Radar
        self.btn_osint = ctk.CTkButton(
            chap_btn_frame,
            text="🌐 Radar",
            command=self.osint_search,
            font=("JetBrains Mono", 11, "bold"),
            fg_color=COLORS["accent_red"],  # Naranja
            hover_color="#cc5528",
            text_color="#000000",
            border_color=COLORS["accent_red"],
            border_width=1,
        )
        self.btn_osint.pack(side="left", padx=5, expand=True, fill="x")

        self.btn_chap_tts = ctk.CTkButton(
            chap_btn_frame,
            text="🔊 TTS Cap",
            command=self.generate_audios_for_chapter,
            font=("JetBrains Mono", 11, "bold"),
            fg_color=COLORS["accent_red"],  # Magenta
            hover_color="#cc0088",
            text_color="#ffffff",
            border_color=COLORS["accent_red"],
            border_width=1,
        )
        self.btn_chap_tts.pack(side="left", padx=5, expand=True, fill="x")

        self.btn_chap_stop = ctk.CTkButton(
            chap_btn_frame,
            text="⏹",
            command=self.stop_director,
            font=("Arial", 14),
            fg_color="#333340",
            hover_color="#444450",
            text_color="#ffffff",
            border_color=COLORS["border"],
            border_width=1,
            width=40,
            state="disabled",
        )
        self.btn_chap_stop.pack(side="right")

        self.chapter_editors = {}  # Almacena ref a los tk.Text de cada pestaña
        self.chapter_widgets = []  # Almacena ref a los frames de la lista izquierda
        self._btn_gen_running = False  # Control de animación del botón
        self._is_generating = False  # Previene doble-click
        self._module_chapters = {}  # {nro_mod: [capitulos_generados]}
        self._current_module_tab = None  # Módulo actualmente seleccionado
        self._current_module_data = None  # Datos del módulo actual
        self._current_course_structure = None  # Estructura completa del curso

    def _on_content_type_change(self, value: str):
        """Maneja el cambio entre Serie y Curso."""
        is_course = "🎓" in value  # Si contiene el emoji de curso

        # Actualizar título del header
        if hasattr(self, "series_title_label") and hasattr(self, "series_header_label"):
            if is_course:
                self.series_title_label.configure(
                    text="PLANIFICADOR DE CURSO - kr-clidn Academy"
                )
                self.series_header_label.configure(text="🎓")
            else:
                self.series_title_label.configure(text="PLANIFICADOR DE SERIE")
                self.series_header_label.configure(text="📚")

        # Mostrar/ocultar configuración de módulos
        if hasattr(self, "modules_config_frame"):
            if is_course:
                self.modules_config_frame.pack(
                    fill="x", pady=(0, 8)
                )  # Mostrar frame principal
                for widget in self.modules_config_frame.winfo_children():
                    widget.pack()
            else:
                for widget in self.modules_config_frame.winfo_children():
                    widget.pack_forget()
                self.modules_config_frame.pack_forget()

        # Ocultar chapters_row en modo curso, mostrar en serie
        # Ocultar/mostrar selector de capítulos según modo
        if hasattr(self, "chapters_row"):
            if is_course:
                self.chapters_row.pack_forget()
            else:
                self.chapters_row.pack(fill="x")

        # Actualizar etiqueta de capítulos
        if hasattr(self, "chapters_label"):
            if is_course:
                self.chapters_label.configure(text="# Módulos:")
                self.series_chapters_combo.configure(
                    values=[str(i) for i in range(1, 31)]
                )
                self.series_chapters_var.set("8")
            else:
                self.chapters_label.configure(text="# Capítulos:")
                self.series_chapters_combo.configure(
                    values=[str(i) for i in range(1, 21)]
                )
                self.series_chapters_var.set("5")

        self.append_chat(
            "Sistema", f"✅ Cambiado a: {'Curso' if is_course else 'Serie'}"
        )

    def _btn_animate_generating(self, base_text: str = None, dot_count: int = 0):
        """Animación profesional de construcción para el botón de generación."""
        if not hasattr(self, "_btn_gen_running") or not self._btn_gen_running:
            return

        try:
            if (
                hasattr(self, "btn_generate_master")
                and self.btn_generate_master.winfo_exists()
            ):
                btn = self.btn_generate_master

                # Pasos de la animación
                steps = [
                    ("🔨 Construyendo", COLORS["accent_red"]),
                    ("🛠️ Preparando", COLORS["accent_red_dim"]),
                    ("⚙️ Configurando", COLORS["accent_red"]),
                    ("📦 Empacando", COLORS["accent_red_dim"]),
                    ("✨ Finalizando", COLORS["accent_green"]),
                ]

                dot_count = dot_count % len(steps)
                text, color = steps[dot_count]

                btn.configure(text=text, fg_color=color)

                # Continuar la animación
                dot_count += 1
                self.after(500, lambda: self._btn_animate_generating(None, dot_count))
        except Exception as e:
            pass

    def _btn_stop_animation(
        self, final_text: str = "✅ Listo", final_state: str = "normal"
    ):
        """Detiene la animación profesional del botón."""
        self._btn_gen_running = False

        try:
            # Eliminar step counter si existe
            if hasattr(self, "_anim_step"):
                delattr(self, "_anim_step")
        except:
            pass

        try:
            if (
                hasattr(self, "btn_generate_master")
                and self.btn_generate_master.winfo_exists()
            ):
                btn = self.btn_generate_master
                # Mostrar éxito con verde
                btn.configure(
                    text=final_text, fg_color=COLORS["accent_green"], state="normal"
                )
                # Restaurar después de 2 segundos
                self.after(
                    2000,
                    lambda: btn.configure(
                        text="✨ Generar Estructura",
                        fg_color=COLORS["accent_red"],
                        state="normal",
                    ),
                )
        except:
            pass

    def _generate_master_structure(self):
        if hasattr(self, "_is_generating") and self._is_generating:
            self.append_chat("Sistema", "⚠️ Ya se está generando. Espera...")
            return
        self._is_generating = True

        topic = self.series_topic_entry.get().strip()
        if not topic:
            self._is_generating = False
            self.append_chat("Error", "⚠️ Debes ingresar un Tema Principal.")
            return

        content_type = getattr(self, "content_type_var", None)
        selected = content_type.get() if content_type else "📺 Serie"
        is_course = "🎓" in selected

        if is_course:
            num_modules = 8
            try:
                if hasattr(self, "course_modules_var"):
                    num_modules = int(self.course_modules_var.get())
            except (ValueError, AttributeError):
                num_modules = 8

            nivel_var = getattr(self, "course_nivel_var", None)
            nivel = nivel_var.get() if nivel_var else "intermedio"

            self.btn_generate_master.configure(state="disabled", text="⏳...")
            self.append_chat("Sistema", "🔄 Generando curso...")

            self.course_orchestrator.ai = self.ai

            def on_success_course(json_data):
                self.after(
                    0,
                    lambda: self.btn_generate_master.configure(
                        state="normal", text="⚡ GENERAR"
                    ),
                )
                self.after(50, self._render_course_structure_ui, json_data)

            def on_error_course(msg):
                self.after(
                    0,
                    lambda: self.btn_generate_master.configure(
                        state="normal", text="⚡ GENERAR"
                    ),
                )
                self.after(0, self.append_chat, "Error", f"❌ Error: {msg}")

            mode_var = getattr(self, "orchestrator_mode_var", None)
            mode = mode_var.get() if mode_var else "DUAL AI"
            aspect_var = getattr(self, "orchestrator_format_var", None)
            aspect = aspect_var.get() if aspect_var else "16:9 (YouTube)"

            self.course_orchestrator.generate_master_course_structure(
                topic,
                num_modules,
                nivel,
                mode,
                aspect,
                on_success_course,
                on_error_course,
            )
        else:
            try:
                num_chapters = int(self.series_chapters_var.get())
            except ValueError:
                num_chapters = 5

            self.btn_generate_master.configure(state="disabled", text="⏳...")
            self.append_chat("Sistema", "🔄 Generando serie...")

            self.series_orchestrator.ai = self.ai

            def on_success_series(json_data):
                self.after(
                    0,
                    lambda: self.btn_generate_master.configure(
                        state="normal", text="⚡ GENERAR"
                    ),
                )
                self.after(50, self._render_master_structure_ui, json_data)

            def on_error_series(msg):
                self.after(
                    0,
                    lambda: self.btn_generate_master.configure(
                        state="normal", text="⚡ GENERAR"
                    ),
                )
                self.after(0, self.append_chat, "Error", f"❌ Error: {msg}")

            mode_var = getattr(self, "orchestrator_mode_var", None)
            mode = mode_var.get() if mode_var else "DUAL AI"
            aspect_var = getattr(self, "orchestrator_format_var", None)
            aspect = aspect_var.get() if aspect_var else "16:9 (YouTube)"

            self.series_orchestrator.generate_master_structure(
                topic, num_chapters, mode, aspect, on_success_series, on_error_series
            )

    def _render_course_structure_ui(self, json_data):
        """Renderiza la estructura del curso en la UI."""
        modulos = json_data.get("modulos", [])
        titulo = json_data.get("titulo_curso", "Sin título")

        print(f"[DEBUG] Renderizando curso: '{titulo}' con {len(modulos)} módulos")
        print(f"[DEBUG] modules_tabview existe: {hasattr(self, 'modules_tabview')}")

        self.append_chat(
            "Sistema", f"✅ Curso '{titulo}' generado con {len(modulos)} módulos"
        )

        # Restaurar botón
        self._is_generating = False
        self.btn_generate_master.configure(state="normal", text="⚡ GENERAR")

        # Limpiar lista de widgets
        for w in self.chapter_widgets:
            w.destroy()
        self.chapter_widgets.clear()

        # Guardar estructura completa
        self._current_course_structure = json_data
        self._module_chapters = {}
        self._module_chapter_tabs = {}
        self._current_module_tabs = {}  # {nro_mod: {"chapter_tabs": ..., "scroll_frame": ...}}

        # Limpiar tabs existentes del modules_tabview (pero guardar referencia)
        try:
            existing_tabs = list(self.modules_tabview._tab_dict.keys())
            for tab in existing_tabs:
                self.modules_tabview.delete(tab)
        except:
            pass

        # Limpiar cache de tabs de módulos
        self._current_module_tabs = {}

        # Crear TODAS las pestañas de módulos de una vez (M1, M2, M3, etc.)
        for mod in modulos:
            nro = int(mod.get("nro", 0))
            tab_name = f"M{nro}"
            mod_colors = get_module_color(nro)
            mod_primary = mod_colors["primary"]

            self.modules_tabview.add(tab_name)
            module_tab = self.modules_tabview.tab(tab_name)

            # Guardar referencia al tab del módulo
            self._current_module_tabs[nro] = {
                "tab": module_tab,
                "data": mod,
                "chapters_loaded": False,
            }

            # Texto de bienvenida en cada tab de módulo (se reemplazará al seleccionar)
            welcome_lbl = ctk.CTkLabel(
                module_tab,
                text=f"📚 Módulo {nro}\n\nCarga los capítulos seleccionando este módulo",
                font=("JetBrains Mono", 12),
                text_color=COLORS["text_dim"],
            )
            welcome_lbl.pack(expand=True)

        # Crear botón Marketing Studio
        mkt_btn = ctk.CTkButton(
            self.chapters_list_frame,
            text="🚀 Marketing Studio",
            command=lambda: self.tabview.set("🚀 Marketing Studio"),
            font=("JetBrains Mono", 10, "bold"),
            fg_color=COLORS["accent_red"],
            hover_color=COLORS["accent_red_dim"],
            text_color="#FFFFFF",
            height=35,
        )
        mkt_btn.pack(fill="x", padx=8, pady=(4, 8))
        self.chapter_widgets.append(mkt_btn)

        # MOSTRAR LOS MÓDULOS EN EL PANEL IZQUIERDO (chapters_list_frame)
        modulos_header = ctk.CTkLabel(
            self.chapters_list_frame,
            text=f"📚 {len(modulos)} Módulos",
            font=("JetBrains Mono", 11, "bold"),
            text_color=COLORS["accent_red"],
        )
        modulos_header.pack(pady=(10, 5))
        self.chapter_widgets.append(modulos_header)

        # Crear botón por cada módulo en el panel izquierdo
        for mod in modulos:
            nro = int(mod.get("nro", 0))
            titulo_mod = mod.get("titulo", "Sin título")
            capitulos = mod.get("capitulos", [])

            mod_colors = get_module_color(nro)

            # Botón más visible con texto blanco
            mod_btn = ctk.CTkButton(
                self.chapters_list_frame,
                text=f"M{nro}: {titulo_mod[:30]}",
                command=lambda n=nro, t=titulo_mod, c=capitulos, m=mod: (
                    self._show_module_chapters(n, t, c, m)
                ),
                font=("JetBrains Mono", 11, "bold"),
                fg_color=COLORS["bg_panel"],
                hover_color=COLORS["accent_red"],
                text_color=COLORS["text_primary"],
                border_color=COLORS["accent_red"],
                border_width=1,
                height=36,
            )
            mod_btn.pack(fill="x", padx=8, pady=4)
            self.chapter_widgets.append(mod_btn)

        # Seleccionar el primer módulo automáticamente
        if modulos:
            first_mod = modulos[0]
            nro = int(first_mod.get("nro", 1))
            titulo_mod = first_mod.get("titulo", "")
            capitulos = first_mod.get("capitulos", [])
            self.after(
                100,
                lambda n=nro, t=titulo_mod, c=capitulos, m=first_mod: (
                    self._show_module_chapters(n, t, c, m)
                ),
            )

    def _show_module_chapters(self, nro_mod, titulo_mod, capitulos, modulo_obj=None):
        """Muestra los capítulos de un módulo - las pestañas M1, M2, M3... permanecen fijas."""
        nro_mod = int(nro_mod) if nro_mod else 1
        self._current_module_tab = nro_mod
        self._current_module_data = modulo_obj

        tab_name = f"M{nro_mod}"

        # SOLO cambiar a la pestaña existente (no crear/eliminar)
        self.modules_tabview.set(tab_name)

        # Verificar si los capítulos ya fueron cargados en este módulo
        if nro_mod in self._current_module_tabs and self._current_module_tabs[
            nro_mod
        ].get("chapters_loaded"):
            # Ya cargado, solo cambiar - no recargar
            return

        # Obtener el tab del módulo
        module_tab = self.modules_tabview.tab(tab_name)

        # Limpiar contenido anterior (solo el welcome label)
        for widget in module_tab.winfo_children():
            widget.destroy()

        # Marcar como cargado
        if nro_mod in self._current_module_tabs:
            self._current_module_tabs[nro_mod]["chapters_loaded"] = True

        # Inicializar _module_chapter_tabs si no existe
        if (
            not hasattr(self, "_module_chapter_tabs")
            or self._module_chapter_tabs is None
        ):
            self._module_chapter_tabs = {}

        # Obtener colores del módulo
        mod_colors = get_module_color(nro_mod)
        mod_primary = mod_colors["primary"]
        mod_dim = mod_colors["dim"]
        mod_bg = "#1a1a1a"

        # Crear sub-tabview para capítulos del módulo
        chapter_tabs = ctk.CTkTabview(
            module_tab,
            fg_color=mod_bg,
            segmented_button_fg_color=COLORS["bg_panel"],
            segmented_button_selected_color=mod_primary,
            segmented_button_selected_hover_color=mod_dim,
            segmented_button_unselected_color=COLORS["bg_dark"],
            segmented_button_unselected_hover_color=COLORS["bg_hover"],
            text_color=COLORS["text_primary"],
            corner_radius=6,
            border_width=1,
            border_color=mod_primary,
        )
        chapter_tabs.pack(fill="both", expand=True, padx=10, pady=10)
        self._module_chapter_tabs[nro_mod] = chapter_tabs

        # Crear pestaña por cada capítulo
        for cap in capitulos:
            nro_cap = cap.get("nro", "?")
            titulo_cap = cap.get("titulo", "Sin Título")
            cap_key = f"M{nro_mod}-C{nro_cap}"
            is_generated = cap_key in self._module_chapters.get(nro_mod, [])

            # Crear pestaña del capítulo
            chapter_tabs.add(f"C{nro_cap}")
            cap_tab = chapter_tabs.tab(f"C{nro_cap}")

            # Mostrar info del capítulo
            cap_header = ctk.CTkFrame(
                cap_tab,
                fg_color=COLORS["bg_panel"],
                corner_radius=6,
                border_width=1,
                border_color=mod_primary,
            )
            cap_header.pack(fill="x", padx=5, pady=5)

            ctk.CTkLabel(
                cap_header,
                text=f"C{nro_cap}: {titulo_cap}",
                font=("JetBrains Mono", 11, "bold"),
                text_color=COLORS["text_primary"],
            ).pack(side="left", padx=10, pady=10)

            # Frame para botón y estado
            btn_frame = ctk.CTkFrame(cap_header, fg_color="transparent")
            btn_frame.pack(side="right", padx=5)

            # Estado
            status_lbl = ctk.CTkLabel(
                btn_frame,
                text="✅" if is_generated else "⏳",
                font=("Arial", 14),
                text_color=COLORS["accent_green"]
                if is_generated
                else COLORS["text_dim"],
            )
            status_lbl.pack(side="right", padx=4)

            # Botón generar
            btn_gen = ctk.CTkButton(
                btn_frame,
                text="⚡",
                width=50,
                height=35,
                font=("Arial", 16, "bold"),
                fg_color=COLORS["accent_red"]
                if not is_generated
                else COLORS["accent_green"],
                hover_color=COLORS["accent_red_dim"]
                if not is_generated
                else COLORS["accent_green"],
                text_color="#ffffff",
                border_width=0,
            )
            btn_gen.pack(side="right", padx=4)

            # Configurar comando con closure correcta
            def make_gen_callback(m=modulo_obj, c=cap, b=btn_gen, s=status_lbl):
                def on_click():
                    try:
                        b.configure(state="disabled", fg_color="#555555", text="⏳")
                        s.configure(text="🔄", text_color=COLORS["accent_yellow"])
                        self._generate_course_chapter(m, c, b, s)
                    except:
                        pass

                return on_click

            btn_gen.configure(command=make_gen_callback())

            # Si ya generado, marcar
            if is_generated:
                btn_gen.configure(text="✅", state="disabled")

            # Área del editor JSON
            json_area = ctk.CTkFrame(cap_tab, fg_color=mod_bg, corner_radius=6)
            json_area.pack(fill="both", expand=True, padx=5, pady=(0, 5))

            ctk.CTkLabel(
                json_area,
                text="📝 Genera el capítulo para ver el JSON",
                font=("JetBrains Mono", 11),
                text_color=COLORS["text_dim"],
            ).pack(expand=True)

    def _generate_course_chapter(self, modulo, chapter, button, status_label=None):
        """Genera el JSON de un capítulo específico del curso."""
        button.configure(state="disabled", fg_color="#7F8C8D")
        nro_mod = int(modulo.get("nro", 1))
        nro_cap = int(chapter.get("nro", 1))

        self.append_chat(
            "Sistema", f"⏳ Generando Módulo {nro_mod} - Capítulo {nro_cap}..."
        )

        # Asegurar que el orchestrator tenga el AI configurado
        self.course_orchestrator.ai = self.ai

        target_ip = getattr(self, "target_combo", None)
        target = target_ip.get() if target_ip else "scanme.nmap.org"

        modo = getattr(self, "orchestrator_mode_var", None)
        modo_val = modo.get() if modo else "DUAL AI"
        aspect = getattr(self, "orchestrator_format_var", None)
        aspect_val = aspect.get() if aspect else "16:9 (YouTube)"

        def on_success(n_mod, n_cap, json_array, path):
            self.after(
                0,
                self._render_course_chapter_json,
                n_mod,
                n_cap,
                json_array,
                button,
                "",
                status_label,
            )

        def on_error(n_cap, msg):
            self.after(
                0, self.append_chat, "Error", f"❌ Error M{nro_mod}.C{n_cap}: {msg}"
            )
            try:
                if button.winfo_exists():
                    button.configure(state="normal", fg_color="#F39C12", text="⚡")
            except:
                pass
            if status_label:
                try:
                    status_label.configure(text="❌")
                except:
                    pass

        self.course_orchestrator.generate_chapter_json(
            target_ip=target,
            chapter=chapter,
            modulo_info=modulo,
            modo=modo_val,
            aspect=aspect_val,
            on_success=lambda n_mod, n_cap, json_arr, path: on_success(
                n_mod, n_cap, json_arr, path
            ),
            on_error=lambda n_cap, msg: on_error(n_cap, msg),
        )

    def _render_course_chapter_json(
        self, nro_mod, nro_cap, json_array, button, modulo_titulo="", status_label=None
    ):
        """Renderiza el JSON del capítulo en la UI."""
        # Convertir a enteros para evitar problemas de tipos
        nro_mod = int(nro_mod)
        nro_cap = int(nro_cap)

        try:
            if button.winfo_exists():
                button.configure(state="disabled", fg_color="#27AE60", text="✅")
        except:
            pass

        # Actualizar status label
        if status_label:
            try:
                status_label.configure(text="✅", text_color="#27AE60")
            except:
                pass

        self.append_chat(
            "Sistema", f"✅ Módulo {nro_mod} - Capítulo {nro_cap} generado"
        )

        # Registrar capítulo generado
        if nro_mod not in self._module_chapters:
            self._module_chapters[nro_mod] = []
        cap_key = f"M{nro_mod}-C{nro_cap}"
        if cap_key not in self._module_chapters[nro_mod]:
            self._module_chapters[nro_mod].append(cap_key)

        # Almacenar JSON generado para este capítulo
        if not hasattr(self, "_chapter_json_cache"):
            self._chapter_json_cache = {}
        self._chapter_json_cache[cap_key] = json_array

        # Refrescar la pestaña del capítulo para mostrar el JSON
        def refresh_chapter_tab():
            # Verificar si los chapter_tabs del módulo ya existen
            if nro_mod not in self._module_chapter_tabs:
                # Los chapter_tabs no existen, necesitamos crear los tabs del módulo primero
                print(f"Creando chapter_tabs para módulo {nro_mod}...")

                # Obtener datos del módulo desde la estructura del curso
                modulos = self._current_course_structure.get("modulos", [])
                modulo_data = None
                capitulos_data = []

                for m in modulos:
                    if int(m.get("nro", 0)) == nro_mod:
                        modulo_data = m
                        capitulos_data = m.get("capitulos", [])
                        break

                if modulo_data and capitulos_data:
                    # Crear los tabs del módulo y sus capítulos
                    self._show_module_chapters(
                        nro_mod,
                        modulo_data.get("titulo", ""),
                        capitulos_data,
                        modulo_data,
                    )
                else:
                    print(f"No se encontró datos del módulo {nro_mod}")
                    return

            # Ir al módulo
            try:
                self.modules_tabview.set(f"M{nro_mod}")
            except Exception as e:
                print(f"Error al cambiar módulo: {e}")
                return

            # Ir al capítulo
            chapter_tabs = self._module_chapter_tabs.get(nro_mod)
            if chapter_tabs is None:
                print(f"No se encontró chapter_tabs para módulo {nro_mod}")
                return

            cap_tab_name = f"C{nro_cap}"
            try:
                chapter_tabs.set(cap_tab_name)
            except Exception as e:
                print(f"Error al cambiar capítulo: {e}")
                return

            # Renderizar JSON en el tab del capítulo
            cap_tab = chapter_tabs.tab(cap_tab_name)

            # Limpiar TODOS los widgets hijos
            for widget in list(cap_tab.winfo_children()):
                widget.destroy()

            # Crear frame para el JSON
            json_frame = ctk.CTkFrame(cap_tab, fg_color=COLORS["bg_dark"])
            json_frame.pack(fill="both", expand=True, padx=5, pady=5)

            # Mostrar JSON formateado en un Textbox
            json_text = json.dumps(json_array, indent=2, ensure_ascii=False)
            json_textbox = ctk.CTkTextbox(
                json_frame,
                font=("JetBrains Mono", 9),
                fg_color=COLORS["bg_panel"],
                text_color=COLORS["text_primary"],
                wrap="none",
            )
            json_textbox.insert("1.0", json_text[:5000])
            json_textbox.configure(state="disabled")
            json_textbox.pack(fill="both", expand=True, padx=5, pady=5)

        self.after(200, refresh_chapter_tab)
        self._is_generating = False

    def _generate_course_module(self, modulo: dict):
        """Genera todos los capítulos de un módulo (método antiguo - ya no usado)."""
        pass

    def _render_master_structure_ui(self, json_data):
        self.btn_generate_master.configure(state="normal", text="✨ Re-Generar")
        self.append_chat(
            "Sistema",
            f"✅ Estructura Maestra '{json_data.get('titulo_serie', '')}' generada con éxito.",
        )

        # Limpiar lista anterior
        for w in self.chapter_widgets:
            w.destroy()
        self.chapter_widgets.clear()

        # Limpiar tabs anteriores (excepto Bienvenido)
        try:
            self.modules_tabview.delete("📋 Bienvenido")
        except:
            pass

        for name in list(self.chapter_editors.keys()):
            try:
                self.modules_tabview.delete(name)
            except:
                pass
        self.chapter_editors.clear()

        # Popular panel izquierdo
        capitulos = json_data.get("capitulos", [])
        for cap in capitulos:
            nro = cap.get("nro", "?")
            titulo = cap.get("titulo", "Sin Título")

            frame = ctk.CTkFrame(
                self.chapters_list_frame, fg_color=COLORS["bg_panel"], corner_radius=6
            )
            frame.pack(fill="x", pady=2)
            self.chapter_widgets.append(frame)

            ctk.CTkLabel(
                frame,
                text=f"Cap. {nro}",
                font=("JetBrains Mono", 11, "bold"),
                text_color=COLORS["accent_cyan"],
                width=50,
            ).pack(side="left", padx=5)
            # Acortar título muy largo
            display_title = titulo[:30] + "..." if len(titulo) > 30 else titulo
            ctk.CTkLabel(
                frame,
                text=display_title,
                font=("JetBrains Mono", 10),
                text_color=COLORS["text_primary"],
            ).pack(side="left", fill="x", expand=True)

            # Botón Generar JSON del capítulo
            btn_gen = ctk.CTkButton(
                frame,
                text="⚡",
                width=30,
                height=24,
                font=("Arial", 14),
                fg_color="#F39C12",
                hover_color="#D68910",
                text_color="#000000",
            )
            btn_gen.configure(
                command=lambda c=cap, b=btn_gen: self._generate_chapter_json(c, b)
            )
            btn_gen.pack(side="right", padx=5, pady=4)

            # Crear pestaña por capítulo
            tab_name = f"Cap {nro}"
            tab = self.modules_tabview.add(tab_name)

            # Editor tk.Text
            editor = tk.Text(
                tab,
                bg="#08090a",
                fg="#a0ffa0",
                font=("JetBrains Mono", 10),
                insertbackground=COLORS["accent_green"],
                selectbackground="#1a3a1a",
                relief="flat",
                bd=0,
                wrap="word",
                highlightthickness=0,
                padx=8,
                pady=4,
                undo=True,
            )
            editor.pack(fill="both", expand=True)

            # Apply Syntax highlighting tags
            editor.tag_config("json_key", foreground="#9CDCFE")
            editor.tag_config("json_string", foreground="#CE9178")
            editor.tag_config("json_bracket", foreground="#FFD700")
            editor.tag_config("json_keyword", foreground="#C586C0")
            editor.tag_config("json_colon", foreground="#D4D4D4")
            editor.tag_config("json_number", foreground="#B5CEA8")

            self.chapter_editors[tab_name] = editor

    def _generate_chapter_json(self, chapter_data, button):
        button.configure(state="disabled", fg_color="#7F8C8D")
        nro = chapter_data.get("nro", "?")
        self.append_chat("Sistema", f"⏳ Generando código para Capítulo {nro}...")

        target_ip = (
            self.target_combo.get()
            if hasattr(self, "target_combo")
            else "scanme.nmap.org"
        )  # type: ignore

        def on_success(n, json_array, saved_path):
            self.after(0, self._render_chapter_json_ui, n, json_array, button)

        def on_error(n, msg):
            self.after(0, self.append_chat, "Error", f"❌ Error Cap {n}: {msg}")
            self.after(0, lambda: button.configure(state="normal", fg_color="#F39C12"))

        mode_var = getattr(self, "orchestrator_mode_var", self.pre_mode_var)
        mode = mode_var.get() if mode_var is not None else "DUAL AI"  # type: ignore
        aspect_var = getattr(self, "orchestrator_format_var", None)
        aspect = aspect_var.get() if aspect_var is not None else "16:9 (YouTube)"  # type: ignore
        self.series_orchestrator.generate_chapter_json(
            target_ip, chapter_data, mode, aspect, on_success, on_error
        )

    def _render_chapter_json_ui(self, nro, json_array, button):
        button.configure(state="normal", fg_color=COLORS["accent_green"], text="✅")
        self.append_chat("Sistema", f"✅ Código para Capítulo {nro} generado.")

        tab_name = f"Cap {nro}"
        if tab_name in self.chapter_editors:
            editor = self.chapter_editors[tab_name]
            editor.delete("1.0", "end")
            editor.insert("end", json.dumps(json_array, indent=4, ensure_ascii=False))
            try:
                self.modules_tabview.set(tab_name)
            except:
                pass

    def _render_series(self):
        target_ip = (
            self.target_combo.get()
            if hasattr(self, "target_combo")
            else "scanme.nmap.org"
        )  # type: ignore

        if not self.wid_a or not self.wid_b:
            self.append_chat(
                "Error",
                "❌ Falta al menos una de las terminales. Dale click a Lanzar primero o espera a que esten disponibles.",
            )
            return

        def on_progress(msg):
            self.after(0, self.append_chat, "Sistema", msg)

        def on_finish(msg):
            self.after(0, self.append_chat, "Sistema", msg)
            self.after(
                0,
                lambda: self.btn_render_series.configure(
                    state="normal", text="🎬 Renderizar Serie Completa"
                ),
            )

        def on_error(msg):
            self.after(0, self.append_chat, "Error", msg)
            self.after(
                0,
                lambda: self.btn_render_series.configure(
                    state="normal", text="🎬 Renderizar Serie Completa"
                ),
            )

        self.append_chat(
            "Sistema", "🎬 Iniciando renderizado secuencial de la serie..."
        )
        self.btn_render_series.configure(state="disabled", text="⏳ Renderizando...")

        mode_var = getattr(self, "orchestrator_mode_var", self.pre_mode_var)
        mode = mode_var.get() if mode_var is not None else "DUAL AI"  # type: ignore
        aspect_var = getattr(self, "orchestrator_format_var", None)
        aspect = aspect_var.get() if aspect_var is not None else "16:9 (YouTube)"  # type: ignore

        # Necesitamos instanciar un _auto_thread que llame al orchestrator en lugar del codigo legacy
        self.series_orchestrator.process_series_loop(
            self, target_ip, mode, aspect, on_progress, on_finish, on_error
        )

    def _load_ui_preferences(self):
        """Carga las preferencias guardadas de UI."""
        if not hasattr(self.ai, "memory_manager"):
            return
        mm = self.ai.memory_manager

        # Cargar velocidad de tipeo
        saved_speed = mm.get_ui_preference("typing_speed")
        if saved_speed:
            self.typing_speed_pct = saved_speed
            if hasattr(self, "speed_slider"):
                self.speed_slider.set(saved_speed)
            if hasattr(self, "speed_label"):
                self.speed_label.configure(text=f"{saved_speed}%")

        # Cargar duración de video
        saved_duration = mm.get_ui_preference("video_duration")
        if saved_duration:
            self.video_duration_min = saved_duration
            if hasattr(self, "duration_slider"):
                self.duration_slider.set(saved_duration)
            if hasattr(self, "duration_label"):
                self.duration_label.configure(text=f"{saved_duration} min")

        # Cargar formato
        saved_format = mm.get_ui_preference("format")
        if saved_format and hasattr(self, "format_combo"):
            self.format_combo.set(saved_format)

        # Cargar modo
        saved_mode = mm.get_ui_preference("mode")
        if saved_mode and hasattr(self, "pre_mode_var"):
            self.pre_mode_var.set(saved_mode)

    def _on_speed_change(self, value):
        self.typing_speed_pct = int(value)
        self.speed_label.configure(text=f"{self.typing_speed_pct}%")
        if hasattr(self.ai, "memory_manager"):
            self.ai.memory_manager.save_ui_preference(
                "typing_speed", self.typing_speed_pct
            )

    def _on_duration_change(self, value):
        self.video_duration_min = int(value)
        self.duration_label.configure(text=f"{self.video_duration_min} min")
        if hasattr(self.ai, "memory_manager"):
            self.ai.memory_manager.save_ui_preference(
                "video_duration", self.video_duration_min
            )

    def _on_format_change(self, value):
        """Guarda la preferencia de formato."""
        if hasattr(self.ai, "memory_manager"):
            self.ai.memory_manager.save_ui_preference("format", value)

    def _on_mode_change(self, value):
        """Guarda la preferencia de modo."""
        if hasattr(self.ai, "memory_manager"):
            self.ai.memory_manager.save_ui_preference("mode", value)

    def _schedule_auto_save(self):
        """Schedule an auto-save after a delay."""
        if self._auto_save_after_id:
            self.after_cancel(self._auto_save_after_id)
        self._auto_save_after_id = self.after(
            self._auto_save_delay_ms, self._perform_auto_save
        )

    def _perform_auto_save(self):
        """Perform the actual auto-save."""
        self._auto_save_after_id = None
        # Get current JSON from active editor
        if self._get_active_mode() == "SOLO TERM":
            editor = self.editor_b
        else:
            editor = self.editor
        json_str = editor.get("1.0", "end-1c").strip()
        if not json_str:
            return
        try:
            json_data = json.loads(json_str)
            if isinstance(json_data, list):
                self._auto_save_project(json_data)
        except json.JSONDecodeError:
            # Not valid JSON yet, don't save
            pass

    def _on_video_config_change(self, *args):
        """Actualiza la configuración de video en AIEngine cuando cambia la UI."""
        if not self.ai:
            return
        try:
            # Obtener key desde label seleccionada
            vt_label = self._video_type_var.get()
            templates = get_template_list()
            vt_key = (
                self._template_keys[
                    [f"{t['icono']} {t['nombre']}" for t in templates].index(vt_label)
                ]
                if self._template_keys
                else "tutorial_profundo"
            )

            ps_label = self._presenter_style_var.get()
            presenters = get_presenter_list()
            ps_key = (
                self._presenter_keys[[p["nombre"] for p in presenters].index(ps_label)]
                if self._presenter_keys
                else "experto_tecnico"
            )

            aud_label = self._audience_var.get()
            audiences = get_audience_list()
            aud_key = (
                self._audience_keys[[a["nombre"] for a in audiences].index(aud_label)]
                if self._audience_keys
                else "intermedio"
            )

            extra = (
                self._extra_notes_text.get("1.0", "end").strip()
                if self._extra_notes_text
                else ""
            )

            self.ai.set_video_config(vt_key, ps_key, aud_key, extra)
            self.append_chat(
                "Sistema", f"✅ Config activa: {vt_label} | {ps_label} | {aud_key}"
            )
        except Exception as e:
            self.append_chat("Error", f"⚠ Config video: {e}")

    # ═══════════════════════════════════════════════
    # OSINT RADAR — Búsqueda de Tendencias en Vivo
    # ═══════════════════════════════════════════════

    def osint_search(self):
        """Busca tendencias de ciberseguridad en vivo."""
        if not self.ai:
            self.append_chat("Error", "❌ Conecta la API Key primero.")
            return
        self.append_chat(
            "Sistema", "🌐 Buscando tendencias de ciberseguridad en vivo..."
        )
        self.btn_osint.configure(state="disabled")
        self._start_processing_animation()
        threading.Thread(target=self._osint_thread, daemon=True).start()

    def _osint_thread(self):
        """Thread de búsqueda OSINT."""
        try:
            tendencias = self.ai.buscar_tendencias_live()
            self.after(0, self._stop_processing_animation)
            self.after(0, self.btn_osint.configure, {"state": "normal"})

            if tendencias:
                msg = "🔥 TENDENCIAS DE CIBERSEGURIDAD (últimas 48h):\n\n"
                for i, t in enumerate(tendencias, 1):
                    titulo = t.get("titulo", f"Capítulo {i + 1}")[:40]  # type: ignore
                    desc = t.get("descripcion", "")[:100]  # type: ignore
                    fuente = t.get("fuente", "")
                    msg += f"  {i}. {titulo}\n     {desc}\n     📌 {fuente}\n\n"
                msg += (
                    "💡 Escribe el número o el tema en el chat para generar un guion."
                )
                self.after(0, self.append_chat, "OSINT", msg)
            else:
                self.after(
                    0,
                    self.append_chat,
                    "OSINT",
                    "⚠ No se encontraron tendencias. Intenta de nuevo.",
                )
        except Exception as e:
            self.after(0, self._stop_processing_animation)
            self.after(0, self.btn_osint.configure, {"state": "normal"})
            self.after(0, self.append_chat, "Error", f"❌ Error OSINT: {e}")

    # ═══════════════════════════════════════════════
    # MODO DINÁMICO
    # ═══════════════════════════════════════════════

    def start_processing_animation(self):
        self._start_processing_animation()

    def stop_processing_animation(self):
        self._stop_processing_animation()

    def auto_save_project(self, json_data: list):
        self._auto_save_project(json_data)

    def generate_seo_metadata(self, prompt: str, json_data: list):
        self._generate_seo_metadata(prompt, json_data)

    def parse_editor_json(self, mode: str = "a"):
        """Wrapper para el ActionHandler — pasa el mode hint al parser real."""
        return self._parse_editor_json(editor_hint=mode)

    def get_project_name(self):
        """Retorna el nombre del proyecto basado en el título metadata."""
        title = self.meta_title.get().strip()
        if not title:
            return "default"
        # Limpiar para usar como nombre de carpeta
        import re

        return str(re.sub(r"[^a-zA-Z0-9_\-]", "_", title))[:30]  # type: ignore

    def show_floating_controller(self):
        """Muestra el controlador flotante si existe."""
        if self._floating_ctrl:
            self._floating_ctrl.deiconify()  # type: ignore
            self._floating_ctrl.lift()  # type: ignore

    def _get_last_user_topic(self) -> str:
        """Extrae el tema del último mensaje del usuario en el chat."""
        if hasattr(self, "_last_user_message") and self._last_user_message:
            return self._last_user_message
        return ""

    # ═══════════════════════════════════════════════
    # EDITOR: NÚMEROS DE LÍNEA + SYNTAX HIGHLIGHTING
    # ═══════════════════════════════════════════════

    def _sync_scroll(self, *args):
        """Sincroniza scroll del editor con los números de línea."""
        self.line_numbers.yview_moveto(args[0] if args else 0)

    def _update_editor(self):
        """Actualiza números de línea y syntax highlighting."""
        self._update_line_numbers()
        self._apply_syntax_highlighting()

    def _update_line_numbers(self):
        content = self.editor.get("1.0", "end-1c")
        lines = content.split("\n")
        ln_text = "\n".join(str(i + 1) for i in range(len(lines)))

        self.line_numbers.configure(state="normal")
        self.line_numbers.delete("1.0", "end")
        self.line_numbers.insert("1.0", ln_text)
        self.line_numbers.configure(state="disabled")

        # Sync scroll position
        self.line_numbers.yview_moveto(self.editor.yview()[0])

    def _apply_syntax_highlighting(self):
        """Aplica colores de sintaxis JSON al editor."""
        content = self.editor.get("1.0", "end-1c")

        # Limpiar tags existentes
        for tag in (
            "json_key",
            "json_string",
            "json_bracket",
            "json_keyword",
            "json_colon",
            "json_number",
        ):
            self.editor.tag_remove(tag, "1.0", "end")

        # Brackets
        for match in re.finditer(r"[\[\]\{\}]", content):
            start_idx = f"1.0+{match.start()}c"
            end_idx = f"1.0+{match.end()}c"
            self.editor.tag_add("json_bracket", start_idx, end_idx)

        # Colons and commas
        for match in re.finditer(r"[:,]", content):
            start_idx = f"1.0+{match.start()}c"
            end_idx = f"1.0+{match.end()}c"
            self.editor.tag_add("json_colon", start_idx, end_idx)

        # Keys (before colon)
        for match in re.finditer(r'"(\w+)"\s*:', content):
            start_idx = f"1.0+{match.start()}c"
            end_idx = f"1.0+{match.start() + len(match.group(0)) - 1}c"
            self.editor.tag_add("json_key", start_idx, end_idx)

        # String values (after colon) — quotes + content
        for match in re.finditer(r':\s*"([^"]*)"', content):
            val_start = content.index('"', match.start() + 1)
            val_end = content.index('"', val_start + 1) + 1
            start_idx = f"1.0+{val_start}c"
            end_idx = f"1.0+{val_end}c"
            self.editor.tag_add("json_string", start_idx, end_idx)

        # Keywords inside strings
        for kw in ("narracion", "ejecucion"):
            for match in re.finditer(re.escape(kw), content):
                start_idx = f"1.0+{match.start()}c"
                end_idx = f"1.0+{match.end()}c"
                self.editor.tag_add("json_keyword", start_idx, end_idx)

        # Numbers
        for match in re.finditer(r"\b\d+\b", content):
            start_idx = f"1.0+{match.start()}c"
            end_idx = f"1.0+{match.end()}c"
            self.editor.tag_add("json_number", start_idx, end_idx)

    # ═══════════════════════════════════════════════
    # KONSOLE AL EJECUTAR
    # ═══════════════════════════════════════════════

    def ensure_terminals_open(self, callback=None, mode="dual"):
        if mode == "dual":
            if self.wid_a and self.wid_b:
                if callback:
                    self.after(0, callback)
                return
        else:
            if self.wid_b:
                if callback:
                    self.after(0, callback)
                return

        threading.Thread(
            target=self._startup_konsole_thread, args=(callback, mode), daemon=True
        ).start()

    def _startup_konsole_thread(self, callback=None, mode="dual"):
        import subprocess as sp

        is_solo = mode == "solo"

        if is_solo:
            self.after(
                0,
                self.append_chat,
                "Sistema",
                "🖥 Abriendo 1 terminal Konsole...\n"
                "  Terminal B → Ejecución de comandos (Modo Solo)",
            )
        else:
            self.after(
                0,
                self.append_chat,
                "Sistema",
                "🖥 Abriendo 2 terminales Konsole...\n"
                "  Terminal A → KR-CLIDN (dashboard/AI) [KaliRootCLI + venv]\n"
                "  Terminal B → Ejecución de comandos",
            )
        try:
            if not is_solo:
                # Terminal A: inicia en KaliRootCLI (mantiene shell del usuario)
                sp.Popen(
                    ["konsole", "--workdir", "/home/rk13/RK13CODE/KaliRootCLI"],
                    stdout=sp.DEVNULL,
                    stderr=sp.DEVNULL,
                )
                time.sleep(1.5)
                # Terminal B: normal
                sp.Popen(["konsole"], stdout=sp.DEVNULL, stderr=sp.DEVNULL)
                time.sleep(1.5)
            else:
                # Solo Terminal B
                sp.Popen(["konsole"], stdout=sp.DEVNULL, stderr=sp.DEVNULL)
                time.sleep(1.5)
        except FileNotFoundError:
            self.after(0, self.append_chat, "Error", "❌ Konsole no encontrado.")
            return

        time.sleep(2.0)
        try:
            result = sp.run(
                ["xdotool", "search", "--class", "konsole"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            wids = [w.strip() for w in result.stdout.strip().split("\n") if w.strip()]

            if is_solo and len(wids) >= 1:
                self.wid_b = wids[-1]
                self.wid_a = None
            elif not is_solo and len(wids) >= 2:
                self.wid_a = wids[-2]  # Terminal A
                self.wid_b = wids[-1]  # Terminal B
            elif not is_solo and len(wids) == 1:
                self.wid_a = wids[0]
                self.wid_b = wids[0]
                self.after(
                    0,
                    self.append_chat,
                    "Sistema",
                    f"⚠ Solo 1 Konsole encontrada (WID: {self.wid_a}).\nUsando misma terminal para A y B.",
                )
            elif len(wids) == 0:
                self.after(
                    0,
                    self.append_chat,
                    "Sistema",
                    "⚠ Konsoles abiertas pero sin WID detectado.",
                )
                return

            # ─── Geometría según modo ───
            # Obtener tamaño de pantalla
            try:
                screen_w = int(
                    sp.run(
                        ["xdotool", "getdisplaygeometry"],
                        capture_output=True,
                        text=True,
                    ).stdout.split()[0]
                )
                screen_h = int(
                    sp.run(
                        ["xdotool", "getdisplaygeometry"],
                        capture_output=True,
                        text=True,
                    ).stdout.split()[1]
                )
            except Exception:
                screen_w, screen_h = 1920, 1080

            # Leer formato para decidir geometría
            aspect = ""
            if hasattr(self, "orchestrator_format_var"):
                aspect = self.orchestrator_format_var.get()
            elif hasattr(self, "format_combo"):
                aspect = self.format_combo.get()
            is_vertical = "9:16" in aspect and not is_solo

            if is_vertical:
                # VERTICAL (9:16): Terminal B con resize exacto 60x40
                if self.wid_b:
                    sp.run(
                        [
                            "xdotool",
                            "type",
                            "--window",
                            str(self.wid_b),
                            "--delay",
                            "15",
                            "resize -s 40 60",
                        ],  # type: ignore
                        capture_output=True,
                        timeout=5,
                    )
                    geo_text = "60x40 (exacto) — Modo Reels"

                    sp.run(
                        ["xdotool", "key", "--window", str(self.wid_b), "Return"],  # type: ignore
                        capture_output=True,
                        timeout=5,
                    )
                    time.sleep(0.5)
                    sp.run(
                        [
                            "xdotool",
                            "type",
                            "--window",
                            str(self.wid_b),
                            "--delay",
                            "15",
                            "clear",
                        ],  # type: ignore
                        capture_output=True,
                        timeout=5,
                    )
                    sp.run(
                        ["xdotool", "key", "--window", str(self.wid_b), "Return"],  # type: ignore
                        capture_output=True,
                        timeout=5,
                    )

                self.after(
                    0,
                    self.append_chat,
                    "Sistema",
                    f"✅ Terminal B (WID: {self.wid_b}) — Ejecución\n"
                    f"Tamaño: {geo_text}\n"
                    f"Configura OBS con 'Terminal-B'",
                )
            elif is_solo:
                # SOLO TERM horizontal (16:9): Terminal B full width
                if self.wid_b:
                    sp.run(
                        [
                            "xdotool",
                            "type",
                            "--window",
                            str(self.wid_b),
                            "--delay",
                            "15",
                            "resize -s 30 110",
                        ],  # type: ignore
                        capture_output=True,
                        timeout=5,
                    )
                    geo_text = "110x30 (exacto) — Modo YouTube"

                    sp.run(
                        ["xdotool", "key", "--window", str(self.wid_b), "Return"],  # type: ignore
                        capture_output=True,
                        timeout=5,
                    )
                    time.sleep(0.5)
                    sp.run(
                        [
                            "xdotool",
                            "type",
                            "--window",
                            str(self.wid_b),
                            "--delay",
                            "15",
                            "clear",
                        ],  # type: ignore
                        capture_output=True,
                        timeout=5,
                    )
                    sp.run(
                        ["xdotool", "key", "--window", str(self.wid_b), "Return"],  # type: ignore
                        capture_output=True,
                        timeout=5,
                    )

                self.after(
                    0,
                    self.append_chat,
                    "Sistema",
                    f"✅ Terminal B (WID: {self.wid_b}) — Ejecución\n"
                    f"Tamaño: {geo_text}\n"
                    f"Configura OBS con 'Terminal-B'",
                )
            else:
                # DUAL AI: Dividir pantalla 50/50 horizontal (para YouTube)
                half_w = screen_w // 2
                term_h = screen_h - 40  # Margen para panel de tareas

                # Terminal A: mitad izquierda
                geo_a = f"0,0,0,{half_w},{term_h}"
                # Terminal B: mitad derecha
                geo_b = f"0,{half_w},0,{half_w},{term_h}"

                if self.wid_a and self.wid_a != self.wid_b:
                    hex_a = hex(int(self.wid_a))  # type: ignore
                    sp.run(
                        ["wmctrl", "-i", "-r", hex_a, "-e", geo_a],  # type: ignore
                        capture_output=True,
                        timeout=5,
                    )
                if self.wid_b:
                    hex_b = hex(int(self.wid_b))  # type: ignore
                    sp.run(
                        ["wmctrl", "-i", "-r", hex_b, "-e", geo_b],  # type: ignore
                        capture_output=True,
                        timeout=5,
                    )

                desc_formato = f"{half_w}x{term_h} cada una (50/50)"
                self.after(
                    0,
                    self.append_chat,
                    "Sistema",
                    f"✅ Terminal A (WID: {self.wid_a}) — KR-CLIDN [Izquierda]\n"
                    f"✅ Terminal B (WID: {self.wid_b}) — Ejecución [Derecha]\n"
                    f"Pantalla dividida: {desc_formato} — Modo YouTube\n"
                    f"Configura OBS con 2 escenas:\n"
                    f"  Scene 'Terminal-A' → captura Terminal A\n"
                    f"  Scene 'Terminal-B' → captura Terminal B",
                )

            if callback:
                print(f"DEBUG: Calling callback after startup, wid_b={self.wid_b}")
                self.after(1000, callback)
        except Exception as e:
            print(f"DEBUG: Exception in startup: {e}")
            self.after(0, self.append_chat, "Error", f"⚠ {e}")

    # ═══════════════════════════════════════════════
    # CHAT AI — MENSAJES ELEGANTES
    # ═══════════════════════════════════════════════

    def _connect_obs(self):
        """Conecta a OBS, crea escenas Terminal-A y Terminal-B si no existen."""
        from kr_studio.core.obs_controller import OBSController  # type: ignore

        self.append_chat("Sistema", "📺 Conectando a OBS Studio...")
        self._obs = OBSController()
        self._obs.password = self._load_env_value("OBS_PASSWORD", "")

        if not self._obs.connect():
            self.append_chat(
                "Error",
                "❌ No se pudo conectar a OBS.\n"
                "Verifica:\n"
                "  1. OBS está abierto\n"
                "  2. Tools → WebSocket Server Settings → Enable\n"
                "  3. Puerto: 4455\n"
                f"  4. Password: {self._obs.password or '(sin password)'}",
            )
            self.obs_btn.configure(fg_color="#e74c3c")
            return

        # Auto-setup de escenas
        scenes = self._obs._get_scene_names()
        result = self._obs.setup_dual_scenes(self.wid_a or "0", self.wid_b or "0")

        self.obs_btn.configure(fg_color="#27ae60", text="📺 ✅")
        scenes_final = self._obs._get_scene_names()
        current = self._obs.get_current_scene()

        msg = (
            f"✅ OBS Conectado\n"
            f"  Escenas: {', '.join(scenes_final)}\n"
            f"  Escena activa: {current}\n"
        )

        if "Terminal-A" in scenes_final and "Terminal-B" in scenes_final:
            msg += "  ✅ Terminal-A y Terminal-B listas\n"
            msg += "\n⚠ IMPORTANTE: En cada escena, agrega manualmente:\n"
            msg += "  Terminal-A → Source → Window Capture → Konsole (Terminal A)\n"
            msg += "  Terminal-B → Source → Window Capture → Konsole (Terminal B)\n"
            msg += "  Ajusta el tamaño a 450×800 (9:16) en cada fuente"
        else:
            msg += f"  ⚠ Errores: {result.get('errors', [])}"

        self.append_chat("Sistema", msg)

    def save_api_key(self):
        key = self.api_entry.get().strip()
        if not key:
            self.append_chat("Sistema", "⚠ La API Key está vacía.")
            return
        try:
            self.ai = AIEngine(key)
            self._save_env_key(key)
            self.append_chat(
                "Sistema", "✅ API Key conectada y guardada en .env — DOMINION listo."
            )
            # Ocultar la barra de API tras guardar exitosamente
            if hasattr(self, "_api_bar"):
                self._api_bar.grid_forget()
        except Exception as e:
            self.append_chat("Error", f"❌ {e}")

    def _load_env_key(self) -> str:
        """Lee GEMINI_API_KEY desde .env si existe."""
        return self._load_env_value("GEMINI_API_KEY", "")

    def _load_env_value(self, key: str, default: str = "") -> str:
        """Lee cualquier valor desde .env."""
        if not os.path.exists(self._env_path):
            return default
        try:
            with open(self._env_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith(f"{key}="):
                        return line.split("=", 1)[1].strip().strip('"').strip("'")
        except Exception:
            pass
        return default

    def _save_env_key(self, key: str):
        """Guarda GEMINI_API_KEY en .env (crea o actualiza)."""
        lines = []
        found = False
        if os.path.exists(self._env_path):
            with open(self._env_path, "r") as f:
                for line in f:
                    if line.strip().startswith("GEMINI_API_KEY="):
                        lines.append(f"GEMINI_API_KEY={key}\n")
                        found = True
                    else:
                        lines.append(line)
        if not found:
            lines.append(f"GEMINI_API_KEY={key}\n")
        with open(self._env_path, "w") as f:
            f.writelines(lines)

    def append_chat(self, sender: str, text: str):
        """Agrega un mensaje estilizado al chat."""
        self.chat_display.configure(state="normal")
        tb = self.chat_display._textbox

        # Determinar tag de color del sender
        sender_lower = sender.lower()
        if sender_lower in ("sistema", "tts"):
            tag = "sender_system"
        elif sender_lower in ("tú",):
            tag = "sender_user"
        elif sender_lower in ("gemini", "dominion"):
            tag = "sender_ai"
        elif sender_lower in ("director",):
            tag = "sender_director"
        elif sender_lower in ("osint",):
            tag = "sender_osint"
        else:
            tag = "sender_error"

        # Insertar sender con badge de color
        tb.insert("end", f"[{sender}] ", tag)
        tb.insert("end", f"{text}\n\n", "msg_body")

        self.chat_display.see("end")
        self.chat_display.configure(state="disabled")

    def send_chat(self):
        user_text = self.chat_entry.get().strip()
        if not user_text:
            return
        self._last_user_message = user_text  # Guardar para modo dinámico
        self.chat_entry.delete(0, "end")
        self.append_chat("Tú", user_text)
        self.chat_entry.configure(state="disabled")
        self.chat_btn.configure(state="disabled")

        # Iniciar animación de procesamiento
        self._start_processing_animation()

        threading.Thread(
            target=self._process_chat, args=(user_text,), daemon=True
        ).start()

    def _start_processing_animation(self):
        """Animación pulsante en el status label."""
        self._anim_dots = 0
        self.status_label.configure(text_color=COLORS["accent_yellow"])
        self._animate_processing()

    def _animate_processing(self):
        self._anim_dots = (self._anim_dots + 1) % 4
        dots = "." * self._anim_dots
        self.status_label.configure(text=f"⚡ PROCESANDO{dots}")
        self._anim_id = self.after(400, self._animate_processing)

    def _stop_processing_animation(self):
        if self._anim_id:
            self.after_cancel(self._anim_id)
            self._anim_id = None
        self.status_label.configure(
            text="● EN LÍNEA", text_color=COLORS["accent_green"]
        )

    def _process_chat(self, prompt: str):
        try:
            mode = self.pre_mode_var.get() if self.pre_mode_var else "DUAL AI"  # type: ignore
            target_editor = "Editor B" if mode == "SOLO TERM" else "Editor A"
            self._active_tab = "b" if mode == "SOLO TERM" else "a"

            # Obtener tipo de contenido seleccionado
            content_type = (
                self.content_combo.get()
                if hasattr(self, "content_combo")
                else "Por defecto"
            )
            content_type = None if content_type == "Por defecto" else content_type

            # Verificar si ya existe un JSON en el editor activo
            existing_json = self._parse_editor_json()

            # Si NO hay JSON, reseteamos la sesión para generar uno limpio
            if not existing_json:
                if self.ai.model:
                    self.ai.chat_session = self.ai.model.start_chat(history=[])

            solo_instruction = ""
            if mode == "SOLO TERM":
                solo_instruction = (
                    "\n\n[MODO SOLO TERM ACTIVADO]\n"
                    "OBLIGATORIO: Estás generando/modificando un guion para MODO SOLO (SOLO TERMINAL DE COMANDOS).\n"
                    "REGLAS ESTRICTAS PARA MODO SOLO:\n"
                    "1. IGNORA EL FLUJO DE 'MENU'. NO uses el tipo de escena 'menu' ni 'leer'.\n"
                    "2. Empieza directamente con una 'narracion' introduciendo el tema y el problema a resolver.\n"
                    "3. Usa escenas de 'ejecucion' para mostrar los comandos reales en la Terminal B.\n"
                    "   IMPORTANTE: Toda escena de tipo 'ejecucion' DEBE OBLIGATORIAMENTE incluir la clave 'comando_visual' con el comando exacto a tipear en la terminal.\n"
                    "4. Intercala 'narracion' explicando EDUCATIVAMENTE qué hace cada comando y cómo interpretar los resultados.\n"
                    "5. Puedes usar 'pausa' de 2 a 3 segundos si es necesario.\n"
                    "6. Cierra con una 'narracion' de despedida resumiendo lo aprendido.\n"
                    "ESTRUCTURA JSON REQUERIDA:\n"
                    "[\n"
                    '  {"tipo": "narracion", "voz": "Texto a hablar"},\n'
                    '  {"tipo": "ejecucion", "comando_visual": "nmap -sV target", "voz": "Explicación en audio..."}\n'
                    "]\n"
                    "El JSON debe contener toda la interacción técnica directa con la terminal."
                )

            # Inyectar el target legal seleccionado
            target = (
                self.target_combo.get()
                if hasattr(self, "target_combo")
                else "scanme.nmap.org"
            )

            # Detectar si el usuario pide modificar o quiere un tema nuevo
            mod_keywords = [
                "modifica",
                "cambia",
                "agrega",
                "elimina",
                "quita",
                "pon",
                "ajusta",
                "corrige",
                "actualiza",
                "en la escena",
                "reemplaza",
            ]
            is_modification = any(k in prompt.lower() for k in mod_keywords)

            # Si es un tema completamente nuevo, limpiar el directorio de audios viejos para evitar superposiciones
            if not is_modification and mode == "SOLO TERM":
                import shutil

                audio_dir = os.path.join(self.workspace_dir, "audio_solo")
                if os.path.exists(audio_dir):
                    shutil.rmtree(audio_dir, ignore_errors=True)
                os.makedirs(audio_dir, exist_ok=True)

            # Leer parámetros de duración y velocidad (Delay) de la UI
            dur_mins = (
                int(self.duration_slider.get())
                if hasattr(self, "duration_slider")
                else 5
            )  # type: ignore
            speed_delay = (
                int(self.speed_slider.get()) if hasattr(self, "speed_slider") else 80
            )  # type: ignore

            # Dinamismo de tamaño basado en duración solicitada
            escenas_aprox = dur_mins * 6  # Estimación ruda de escenas por minuto
            dur_instruction = (
                f"\n\n[PARAMETROS DE DURACION Y VELOCIDAD]\n"
                f"- El usuario ha solicitado que este video dure aproximadamente {dur_mins} minuto(s).\n"
                f"- Genera un JSON profundo y desarrollado que abarque este tiempo (aprox {escenas_aprox} escenas ricas en contenido y narración). Si es 1 minuto, hazlo directo y rápido (tipo TikTok/Reel, 5-8 escenas). Si son 5-10 minutos o más, profundiza con múltiples comandos, análisis exhaustivo, y ejemplos prácticos variados.\n"
                f"- La velocidad de tipeo actual (Delay) está configurada a {speed_delay}ms por tecla.\n"
            )

            # Instrucción de memoria de contenido
            content_instruction = ""
            if content_type:
                from kr_studio.core.content_memory import get_content_prompt  # type: ignore

                memory_ctx = self.ai.memory_manager.retrieve_memory_context()
                labs_ctx = (
                    self.ai.targets_db.get_targets_summary_for_prompt()
                    if hasattr(self.ai, "targets_db")
                    else ""
                )
                content_instruction = (
                    f"\n\n[MEMORIA DE CONTENIDO ACTIVADA: {content_type}]\n"
                    + get_content_prompt(
                        content_type=content_type,
                        tema=prompt,
                        labs_context=labs_ctx,
                        memory_context=memory_ctx,
                    )
                )

            if existing_json and is_modification:
                # Si ya hay un JSON y el usuario expresamente pide modificarlo
                enriched_prompt = (
                    f"El usuario solicita la siguiente modificación al guion actual: {prompt}\n\n"
                    f"[TARGET LEGAL OBLIGATORIO: {target}]\n\n"
                    f"AQUÍ ESTÁ EL GUION JSON ACTUAL:\n{json.dumps(existing_json, ensure_ascii=False)}\n\n"
                    f"Modifica el JSON actual para cumplir con la petición del usuario, "
                    f"manteniendo la estructura original.\n"
                    f"Responde CIENTO POR CIENTO SOLO CON UN ARREGLO JSON VALIDO. Nada de texto extra."
                    f"{dur_instruction}"
                    f"{solo_instruction}"
                    f"{content_instruction}"
                )
            else:
                # Generación desde cero (tema nuevo)
                enriched_prompt = (
                    f"TEMA SOLICITADO POR EL USUARIO: {prompt}\n\n"
                    f"[TARGET LEGAL OBLIGATORIO: {target}]\n\n"
                    f"Genera un guion sobre EXACTAMENTE este tema: {prompt}\n"
                    f"NO generes sobre nmap ni otro tema diferente al solicitado."
                    f"{dur_instruction}"
                    f"{solo_instruction}"
                    f"{content_instruction}"
                )

            response = self.ai.chat(enriched_prompt)
            json_data = self.ai.extraer_json(response)

            if json_data:
                self.after(0, self._stop_processing_animation)

                if existing_json:
                    msg_txt = f"✅ Guion ({mode}) modificado — {len(json_data)} escenas. Revisa revisa {target_editor} →"
                else:
                    msg_txt = f"✅ Guion ({mode}) generado — {len(json_data)} escenas. Revisa {target_editor} →"

                self.after(0, self.append_chat, "DOMINION", msg_txt)
                json_str = json.dumps(json_data, indent=4, ensure_ascii=False)

                def inject_json():
                    if mode == "SOLO TERM":
                        self.editor_b.delete("1.0", "end")
                        self.editor_b.insert("end", json_str)
                        self._switch_editor_tab("b")
                    else:
                        self.editor.delete("1.0", "end")
                        self.editor.insert("end", json_str)
                        self._switch_editor_tab("a")
                        self._update_editor()

                    # Auto-poblar Metadatos SEO con IA
                    self._generate_seo_metadata(prompt, json_data)

                    self._auto_save_project(json_data)

                self.after(0, inject_json)

                # Guardar preferencia de contenido si se usó
                if content_type:
                    self.ai.memory_manager.save_content_preference(content_type)
            else:
                self.after(0, self._stop_processing_animation)
                self.after(0, self.append_chat, "DOMINION", response)

        except Exception as e:
            self.after(0, self._stop_processing_animation)
            self.after(0, self.append_chat, "Error", f"❌ {str(e)}")

        self.after(0, lambda: self.chat_entry.configure(state="normal"))
        self.after(0, lambda: self.chat_btn.configure(state="normal"))

    def _generate_seo_metadata(self, prompt: str, json_data: list):
        """Genera metadatos SEO virales usando la IA en un thread aparte."""
        # Placeholder rápido mientras la IA responde
        self.meta_title.delete(0, "end")
        self.meta_title.insert(0, "⏳ Generando título SEO...")
        self.meta_desc.delete("1.0", "end")
        self.meta_desc.insert("end", "⏳ Optimizando descripción...")
        self.meta_tags.delete(0, "end")
        self.meta_tags.insert(0, "⏳ Calculando hashtags...")

        def _seo_thread():
            try:
                # Extraer las voces del guión para contexto
                voces = [s.get("voz", "") for s in json_data if s.get("voz")]
                resumen_voces = " | ".join(
                    voces[:5]
                )  # Primeras 5 narraciones # type: ignore

                seo_prompt = (
                    f"Eres un experto en SEO y marketing viral para redes sociales (TikTok, YouTube Shorts, Instagram Reels).\n"
                    f"El usuario creó un video de ciberseguridad/hacking ético sobre: {prompt}\n"
                    f"Contexto del guion: {resumen_voces[:500]}\n\n"  # type: ignore
                    f"Genera EXACTAMENTE este JSON (sin markdown, sin explicaciones):\n"
                    f'{{"titulo": "Título viral SEO (máx 60 chars, con emoji, que retenga y genere curiosidad)", '
                    f'"descripcion": "Descripción optimizada para SEO (máx 150 chars, con keywords naturales y CTA)", '
                    f'"hashtags": "#tag1 #tag2 #tag3 ... (15-20 hashtags relevantes para ciberseguridad, trending, en español e inglés)"}}\n'
                    f"IMPORTANTE: El título DEBE ser clickbait profesional que retenga. Los hashtags DEBEN incluir keywords de búsqueda populares."
                )

                response = self.ai.chat(seo_prompt)
                text = response.strip()
                # Limpiar markdown
                text = re.sub(r"```json\s*", "", text)
                text = re.sub(r"```\s*", "", text)
                text = text.strip()

                seo_data = json.loads(text)

                def _apply():
                    self.meta_title.delete(0, "end")
                    self.meta_title.insert(0, seo_data.get("titulo", prompt[:60]))  # type: ignore

                    self.meta_desc.delete("1.0", "end")
                    self.meta_desc.insert("end", seo_data.get("descripcion", ""))

                    self.meta_tags.delete(0, "end")
                    self.meta_tags.insert(
                        0, seo_data.get("hashtags", "#cybersecurity #hacking")
                    )

                    self.append_chat(
                        "Sistema",
                        "🔍 Metadatos SEO generados por IA — listos para copiar.",
                    )

                self.after(0, _apply)

            except Exception as e:
                # Fallback básico
                def _fallback():
                    self.meta_title.delete(0, "end")
                    self.meta_title.insert(0, f"🔒 {prompt[:55].title()}")  # type: ignore
                    self.meta_desc.delete("1.0", "end")
                    first_voz = next(
                        (s.get("voz", "") for s in json_data if s.get("voz")), ""
                    )
                    self.meta_desc.insert("end", first_voz[:150])  # type: ignore
                    self.meta_tags.delete(0, "end")
                    self.meta_tags.insert(
                        0,
                        "#cybersecurity #kalilinux #hacking #ethicalhacking #DOMINION #infosec",
                    )

                self.after(0, _fallback)

        threading.Thread(target=_seo_thread, daemon=True).start()

    # ═══════════════════════════════════════════════
    # GENERAR AUDIOS TTS
    # ═══════════════════════════════════════════════

    def generate_audios(self):
        json_data = self._parse_editor_json()
        if json_data is None:
            return
        self.btn_tts.configure(state="disabled")
        self.append_chat("Sistema", "🔊 Compilando audios TTS...")
        threading.Thread(
            target=self._generate_audios_thread, args=(json_data,), daemon=True
        ).start()

    def generate_audios_for_chapter(self):
        json_data = self._parse_editor_json()
        if json_data is None:
            return

        try:
            tab_name = self.modules_tabview.get() if self.modules_tabview else "Cap 1"
        except Exception:
            tab_name = "cap_unknown"

        # ── Construir ruta de audio junto al JSON del capítulo ──
        course_dir = None
        series_dir = None

        # Verificar si estamos en modo curso (módulos y capítulos)
        if hasattr(self, "course_orchestrator") and self.course_orchestrator:
            course_dir = getattr(self.course_orchestrator, "_course_dir", None)

        if not course_dir:
            # Truncar topic a 40 chars para evitar [Errno 36] File name too long
            topic_raw = self.series_topic_entry.get().strip() or "serie_generica"
            topic_safe = (
                re.sub(r"[^a-zA-Z0-9_\-]", "_", topic_raw)[:40].strip("_") or "serie"
            )  # type: ignore
            series_dir = getattr(self.series_orchestrator, "_series_dir", None)
            if not series_dir:
                series_dir = os.path.join(self.workspace_dir, "projects", topic_safe)

        if course_dir:
            # Modo curso: guardar en la carpeta del capítulo (donde está el JSON)
            output_dir = course_dir
        else:
            tab_safe = re.sub(r"[^a-zA-Z0-9_\-]", "_", tab_name.lower())
            output_dir = os.path.join(series_dir, tab_safe, "audio")

        os.makedirs(output_dir, exist_ok=True)

        self.btn_chap_tts.configure(state="disabled")
        # Log va al chat principal Y al panel orquestador
        msg = f"🔊 Compilando audios TTS para {tab_name}... → {output_dir}"
        self.append_chat("Sistema", msg)
        self._orch_log("Sistema", msg)
        threading.Thread(
            target=self._generate_audios_thread_orch,
            args=(json_data, output_dir, tab_name, self.btn_chap_tts),
            daemon=True,
        ).start()

    # ─────────────────────────────────────────────────────────────
    #  LOG DEDICADO DEL ORQUESTADOR
    # ─────────────────────────────────────────────────────────────

    def _orch_log(self, sender: str, message: str):
        """
        Muestra un mensaje en el panel de log del orquestador (self.orch_log_box).
        Igual que append_chat pero en el widget del orquestador.
        Si no existe el widget, solo usa append_chat (fallback).
        """
        if not hasattr(self, "orch_log_box"):
            return
        try:
            import time as _t

            COLORES_SENDER = {
                "Sistema": "#00E5FF",
                "TTS": "#ff3333",
                "Error": "#FF5252",
                "OK": "#00E676",
            }
            color = COLORES_SENDER.get(sender, "#AAAAAA")
            self.orch_log_box.configure(state="normal")
            self.orch_log_box.insert("end", f"[{_t.strftime('%H:%M:%S')}] ", "ts")
            self.orch_log_box.insert("end", f"{sender}: ", sender)
            self.orch_log_box.insert("end", f"{message}\n", "msg")
            self.orch_log_box.tag_config("ts", foreground="#555577")
            self.orch_log_box.tag_config(
                sender, foreground=color, font=("JetBrains Mono", 10, "bold")
            )
            self.orch_log_box.tag_config(
                "msg", foreground="#CCCCCC", font=("JetBrains Mono", 10)
            )
            self.orch_log_box.see("end")
            self.orch_log_box.configure(state="disabled")
        except Exception:
            pass

    def _generate_audios_thread_orch(
        self, json_data: list, output_dir: str, tab_name: str, btn_to_restore=None
    ):
        """
        Versión del thread TTS para el orquestador.
        Loguea tanto en append_chat como en _orch_log para máxima visibilidad.
        """
        import hashlib

        audio_engine = AudioEngine()
        total = len(json_data)
        errores = 0
        omitidos = 0

        os.makedirs(output_dir, exist_ok=True)

        for idx, escena in enumerate(json_data):
            voz_raw = escena.get("voz", "")
            voz = self._voz_pronunciable(voz_raw)
            if not voz:
                omitidos = omitidos + 1  # type: ignore
                continue

            text_hash = hashlib.md5(voz.encode("utf-8")).hexdigest()[:8]  # type: ignore
            path = os.path.join(output_dir, f"audio_{idx:03d}_{text_hash}.wav")

            if os.path.exists(path):
                msg = f"Audio {idx + 1}/{total} [{tab_name}] — Cache ✓"
                self.after(0, self.append_chat, "TTS", msg)
                self.after(0, self._orch_log, "TTS", msg)
                continue

            try:
                dur = audio_engine.generar_audio(voz, path)
                msg = f"Audio {idx + 1}/{total} [{tab_name}] — {dur:.1f}s ✅"
                self.after(0, self.append_chat, "TTS", msg)
                self.after(0, self._orch_log, "TTS", msg)
            except Exception as e:
                errores = errores + 1  # type: ignore
                msg = f"❌ TTS {idx + 1} [{tab_name}]: {e}"
                self.after(0, self.append_chat, "Error", msg)
                self.after(0, self._orch_log, "Error", msg)

        if errores == 0 and omitidos == 0:
            final = f"✅ Todos los audios de {tab_name} listos → {output_dir}"
        elif errores == 0:
            final = (
                f"✅ {tab_name} listo ({omitidos} sin texto omitidos) → {output_dir}"
            )
        else:
            final = f"⚠ {tab_name}: {errores} errores, {omitidos} omitidos."

        self.after(0, self.append_chat, "Sistema", final)
        self.after(0, self._orch_log, "OK", final)
        if btn_to_restore:
            self.after(0, lambda: btn_to_restore.configure(state="normal"))

    def _generate_audios_thread(
        self,
        json_data: list,
        override_dir: typing.Optional[str] = None,
        btn_to_restore=None,
    ):
        """
        Thread TTS para el guion principal (Tab 1).
        - Usa _voz_pronunciable para filtrar texto vacío/emojis antes de llamar edge-tts
        - Guarda junto al JSON del proyecto si override_dir está definido
        - Progreso visible en chat principal
        """
        import hashlib

        audio_engine = AudioEngine()
        total = len(json_data)
        errores = 0
        omitidos = 0

        for idx, escena in enumerate(json_data):
            voz = self._voz_pronunciable(escena.get("voz", ""))
            if not voz:
                omitidos = omitidos + 1  # type: ignore
                continue

            text_hash = hashlib.md5(voz.encode("utf-8")).hexdigest()[:8]  # type: ignore

            if override_dir:
                os.makedirs(override_dir, exist_ok=True)  # type: ignore
                path = os.path.join(override_dir, f"audio_{idx:03d}_{text_hash}.wav")  # type: ignore
            else:
                mode = self.pre_mode_var.get() if self.pre_mode_var else "DUAL AI"  # type: ignore
                is_solo = mode == "SOLO TERM"
                if is_solo:
                    d = os.path.join(self.workspace_dir, "audio_solo")
                    os.makedirs(d, exist_ok=True)
                    path = os.path.join(d, f"audio_{idx:03d}_{text_hash}.wav")
                else:
                    path = os.path.join(
                        self.workspace_dir, f"audio_{idx:03d}_{text_hash}.wav"
                    )

            if os.path.exists(path):
                self.after(
                    0, self.append_chat, "TTS", f"Audio {idx + 1}/{total} — Cache ✓"
                )
                continue

            try:
                dur = audio_engine.generar_audio(voz, path)
                self.after(
                    0,
                    self.append_chat,
                    "TTS",
                    f"Audio {idx + 1}/{total} — {dur:.1f}s ✅",
                )
            except Exception as e:
                errores = errores + 1  # type: ignore
                self.after(0, self.append_chat, "Error", f"❌ TTS {idx + 1}: {e}")

        if errores == 0 and omitidos == 0:
            msg = "✅ Todos los audios listos."
        elif errores == 0:
            msg = f"✅ Audios listos ({omitidos} sin texto omitidos)."
        else:
            msg = f"⚠ {errores} error(es). {omitidos} omitidos."
        self.after(0, self.append_chat, "Sistema", msg)
        btn = btn_to_restore if btn_to_restore else self.btn_tts
        self.after(0, lambda: btn.configure(state="normal"))

    # ═══════════════════════════════════════════════
    # LANZAR KONSOLE + XDOTOOL
    # ═══════════════════════════════════════════════

    def smart_launch(self):
        """Lanzar JSON a la terminal — detecta modo (Solo/Dual) automáticamente."""
        mode = self._get_active_mode()
        if mode == "SOLO TERM":
            self.ensure_terminals_open(
                lambda: self._launch_director(auto_record=False, is_solo=True),
                mode="solo",
            )
        else:
            self.ensure_terminals_open(
                lambda: self._launch_director(auto_record=False, is_solo=False),
                mode="dual",
            )

    def launch_konsole(self):
        """Alias de smart_launch para compatibilidad."""
        self.smart_launch()

    def launch_and_record(self):
        """Lanzar JSON + activar grabación OBS — detecta modo automáticamente."""
        mode = self._get_active_mode()
        if mode == "SOLO TERM":
            self.ensure_terminals_open(
                lambda: self._launch_director(auto_record=True, is_solo=True),
                mode="solo",
            )
        else:
            self.ensure_terminals_open(
                lambda: self._launch_director(auto_record=True, is_solo=False),
                mode="dual",
            )

    def _launch_director(self, auto_record=False, is_solo=None):
        """Lanza el MasterDirector unificado según el modo detectado."""
        json_data = self._parse_editor_json()
        if json_data is None:
            return

        # Determinar modo desde UI si no se pasó explícito
        if is_solo is None:
            mode_str = (
                self.pre_mode_var.get()
                if hasattr(self, "pre_mode_var") and self.pre_mode_var
                else "DUAL AI"
            )  # type: ignore[union-attr]
            is_solo = mode_str == "SOLO TERM"

        # Leer formato seleccionado en la UI
        # Prioridad: 1) format_combo (panel chat), 2) orchestrator_format_var (panel orquestador)
        aspect = ""

        # Usar format_combo si está en el panel principal de chat
        # El formato seleccionado por el usuario en el chat tiene prioridad
        if hasattr(self, "format_combo"):
            aspect = self.format_combo.get()
        # Si no hay format_combo, usar orchestrator_format_var
        elif hasattr(self, "orchestrator_format_var"):
            aspect = self.orchestrator_format_var.get()
        # Fallback: inferir según modo
        else:
            aspect = "9:16 (Vertical)" if is_solo else "16:9 (YouTube)"

        director_mode = DirectorMode.SOLO_TERM if is_solo else DirectorMode.DUAL_AI
        project_name = self._get_last_user_topic() or "proyecto"

        self.append_chat(
            "Sistema",
            f"🎬 Lanzando {'SOLO' if is_solo else 'DUAL'} "
            f"| Formato: {aspect} "
            f"| Tipeo: {self.typing_speed_pct}% "
            f"| {'+ OBS' if auto_record else 'sin grabación'}",
        )

        # Deshabilitar botones del orquestador
        for btn_name in ["btn_chap_duo", "btn_chap_solo"]:
            if hasattr(self, btn_name):
                getattr(self, btn_name).configure(state="disabled")
        if hasattr(self, "btn_chap_stop"):
            self.btn_chap_stop.configure(state="normal")

        self._active_director = MasterDirector(
            guion=json_data,
            mode=director_mode,
            workspace_dir=self.workspace_dir,
            typing_speed=self.typing_speed_pct,
            wid_a=self.wid_a,
            wid_b=self.wid_b,
            project_name=project_name,
            progress_callback=self._director_update_progress,
        )
        self._active_director.floating_ctrl = self._floating_ctrl

        # Lanzar en thread daemon
        threading.Thread(
            target=self._director_thread, args=(self._active_director,), daemon=True
        ).start()

    def _director_thread(self, director):
        """Hilo que ejecuta el director y limpia."""
        director.run()
        self.after(0, self._on_director_finished)

    def _director_update_progress(self, current: int, total: int):
        """Callback para actualizar el floating control desde el director."""
        if self._floating_ctrl:
            self.after(0, lambda: self._floating_ctrl.set_progress(current, total))

    def _on_director_finished(self):
        """Se ejecuta en el hilo principal cuando el director termina."""
        self.append_chat("Sistema", "✅ Secuencia finalizada.")

        # Resetear widget flotante
        if self._floating_ctrl:
            self._floating_ctrl._set_idle()

        # Resetear botones del orquestador si existen
        if hasattr(self, "btn_chap_stop"):
            self.btn_chap_stop.configure(state="disabled")
        if hasattr(self, "btn_chap_duo"):
            self.btn_chap_duo.configure(state="normal")
        if hasattr(self, "btn_chap_solo"):
            self.btn_chap_solo.configure(state="normal")

        self._active_director = None

    def stop_director(self):
        """Detiene la secuencia del Director y mata procesos en la terminal."""
        import subprocess as sp

        if self._active_director and self._active_director.is_running:
            self._active_director.stop()
            self.append_chat("Sistema", "⏹ Secuencia detenida.")

        # Enviar Ctrl+C a las terminales para matar procesos activos
        try:
            if self.wid_b:
                sp.run(
                    ["xdotool", "key", "--window", str(self.wid_b), "ctrl+c"],
                    capture_output=True,
                    timeout=3,
                )
                time.sleep(0.2)
                sp.run(
                    ["xdotool", "key", "--window", str(self.wid_b), "ctrl+c"],
                    capture_output=True,
                    timeout=3,
                )
            if self.wid_a and self.wid_a != self.wid_b:
                sp.run(
                    ["xdotool", "key", "--window", str(self.wid_a), "ctrl+c"],
                    capture_output=True,
                    timeout=3,
                )
        except Exception:
            pass

        self.append_chat("Sistema", "✅ Terminales listas para relanzar.")

        if hasattr(self, "btn_chap_stop"):
            self.btn_chap_stop.configure(state="disabled")
            self.btn_chap_duo.configure(state="normal")
            self.btn_chap_solo.configure(state="normal")

        # Resetear widget flotante
        if self._floating_ctrl:
            self._floating_ctrl._set_idle()

    def _on_director_finished(self):
        """Callback del MasterDirector al finalizar — re-habilita botones."""
        for btn_name in ["btn_chap_duo", "btn_chap_solo"]:
            if hasattr(self, btn_name):
                getattr(self, btn_name).configure(state="normal")
        if hasattr(self, "btn_chap_stop"):
            self.btn_chap_stop.configure(state="disabled")
        if self._floating_ctrl:
            self._floating_ctrl._set_idle()  # type: ignore
        self.append_chat("Sistema", "✅ Secuencia finalizada.")

    def _reinforce_terminal_size(self):
        """Re-fuerza el tamaño de la terminal para evitar que Konsole lo resetee."""
        import subprocess as sp

        try:
            mode = self._get_active_mode()
            is_solo = mode == "SOLO TERM"

            # Leer formato para decidir geometría
            format_val = self._get_active_format()
            is_vertical = "9:16" in format_val

            if is_vertical and self.wid_b:
                # Resize exacto 60x40 para formato vertical
                sp.run(
                    [
                        "xdotool",
                        "type",
                        "--window",
                        self.wid_b,
                        "--delay",
                        "15",
                        "resize -s 40 60",
                    ],  # type: ignore
                    capture_output=True,
                    timeout=5,
                )
                sp.run(
                    ["xdotool", "key", "--window", self.wid_b, "Return"],  # type: ignore
                    capture_output=True,
                    timeout=5,
                )
                time.sleep(0.3)
                sp.run(
                    [
                        "xdotool",
                        "type",
                        "--window",
                        self.wid_b,
                        "--delay",
                        "15",
                        "clear",
                    ],  # type: ignore
                    capture_output=True,
                    timeout=5,
                )
                sp.run(
                    ["xdotool", "key", "--window", self.wid_b, "Return"],  # type: ignore
                    capture_output=True,
                    timeout=5,
                )
            elif is_solo and not is_vertical and self.wid_b:
                # Solo horizontal: resize 110x30
                sp.run(
                    [
                        "xdotool",
                        "type",
                        "--window",
                        self.wid_b,
                        "--delay",
                        "15",
                        "resize -s 30 110",
                    ],  # type: ignore
                    capture_output=True,
                    timeout=5,
                )
                sp.run(
                    ["xdotool", "key", "--window", self.wid_b, "Return"],  # type: ignore
                    capture_output=True,
                    timeout=5,
                )
                time.sleep(0.3)
                sp.run(
                    [
                        "xdotool",
                        "type",
                        "--window",
                        self.wid_b,
                        "--delay",
                        "15",
                        "clear",
                    ],  # type: ignore
                    capture_output=True,
                    timeout=5,
                )
                sp.run(
                    ["xdotool", "key", "--window", self.wid_b, "Return"],  # type: ignore
                    capture_output=True,
                    timeout=5,
                )
            elif not is_solo:
                # DUAL: dividir pantalla 50/50
                screen_w = int(
                    sp.run(
                        ["xdotool", "getdisplaygeometry"],
                        capture_output=True,
                        text=True,
                    ).stdout.split()[0]
                )  # type: ignore
                screen_h = int(
                    sp.run(
                        ["xdotool", "getdisplaygeometry"],
                        capture_output=True,
                        text=True,
                    ).stdout.split()[1]
                )  # type: ignore
                half_w = screen_w // 2
                term_h = screen_h - 40
                if self.wid_a and self.wid_a != self.wid_b:
                    sp.run(
                        [
                            "wmctrl",
                            "-i",
                            "-r",
                            hex(int(self.wid_a)),
                            "-e",
                            f"0,0,0,{half_w},{term_h}",
                        ],  # type: ignore
                        capture_output=True,
                        timeout=5,
                    )
                if self.wid_b:
                    sp.run(
                        [
                            "wmctrl",
                            "-i",
                            "-r",
                            hex(int(self.wid_b)),
                            "-e",
                            f"0,{half_w},0,{half_w},{term_h}",
                        ],  # type: ignore
                        capture_output=True,
                        timeout=5,
                    )
        except Exception:
            pass

    # ═══════════════════════════════════════════════
    # SISTEMA DE PROYECTOS
    # ═══════════════════════════════════════════════

    def save_project(self):
        """Guarda el JSON del editor en una carpeta de proyecto."""
        json_data = self._parse_editor_json()
        if json_data is None:
            return

        # Extraer título de la primera escena
        title = self._extract_project_title(json_data)
        proj_dir = os.path.join(self.projects_dir, title)
        os.makedirs(proj_dir, exist_ok=True)

        filepath = os.path.join(proj_dir, "guion.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=4, ensure_ascii=False)

        self.project_name_label.configure(
            text=f"📁 {title}", text_color=COLORS["accent_cyan"]
        )
        self.append_chat("Sistema", f"💾 Proyecto guardado: {title}/guion.json")

    def load_project(self):
        """Abre un diálogo para cargar un proyecto existente."""
        filepath = filedialog.askopenfilename(
            initialdir=self.projects_dir,
            title="Cargar Guion",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not filepath:
            return

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, list):
                self.append_chat(
                    "Error", "⚠ El archivo no contiene un arreglo JSON válido."
                )
                return

            json_str = json.dumps(data, indent=4, ensure_ascii=False)
            self.editor.delete("1.0", "end")
            self.editor.insert("end", json_str)
            self._update_editor()

            # Actualizar label del proyecto
            folder_name = os.path.basename(os.path.dirname(filepath))
            self.project_name_label.configure(
                text=f"📁 {folder_name}", text_color=COLORS["accent_cyan"]
            )
            self.append_chat("Sistema", f"📂 Proyecto cargado: {folder_name}")

        except Exception as e:
            self.append_chat("Error", f"❌ Error al cargar: {e}")

    def _auto_save_project(self, json_data: list):
        """Auto-guarda el proyecto cuando la IA genera un guion."""
        title = self._extract_project_title(json_data)
        proj_dir = os.path.join(self.projects_dir, title)
        os.makedirs(proj_dir, exist_ok=True)

        filepath = os.path.join(proj_dir, "guion.json")
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=4, ensure_ascii=False)
            self.project_name_label.configure(
                text=f"📁 {title}", text_color=COLORS["accent_cyan"]
            )
        except Exception:
            pass

    def _manual_save_project(self):
        """Guarda manualmente el proyecto actual desde el editor."""
        # Determine active editor based on mode
        if self._get_active_mode() == "SOLO TERM":
            editor = self.editor_b
        else:
            editor = self.editor

        json_str = editor.get("1.0", "end-1c").strip()
        if not json_str:
            self.append_chat("Sistema", "⚠ El editor está vacío.")
            return

        try:
            json_data = json.loads(json_str)
            if not isinstance(json_data, list):
                self.append_chat(
                    "Sistema", "⚠ El JSON debe ser un arreglo [] de escenas."
                )
                return
        except json.JSONDecodeError as e:
            self.append_chat("Sistema", f"⚠ JSON inválido: {e}")
            return

        # If we get here, we have valid JSON data (a list)
        title = self._extract_project_title(json_data)
        if not title:
            title = f"proyecto_{int(time.time())}"

        proj_dir = os.path.join(self.projects_dir, title)
        os.makedirs(proj_dir, exist_ok=True)

        filepath = os.path.join(proj_dir, "guion.json")
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=4, ensure_ascii=False)
            self.append_chat("Sistema", f"✅ Proyecto guardado como '{title}'")
            # Update the project name label if we have one
            if hasattr(self, "project_name_label"):
                self.project_name_label.configure(
                    text=f"📁 {title}", text_color=COLORS["accent_cyan"]
                )
        except Exception as e:
            self.append_chat("Error", f"❌ No se pudo guardar el proyecto: {e}")

    def _extract_project_title(self, json_data: list) -> str:
        """Extrae un título legible del contenido del guion."""
        for scene in json_data:
            text = scene.get("comando_visual", "") or scene.get("voz", "")
            if text:
                # Limpiar y truncar
                clean = re.sub(r"[^\w\s\-]", "", text).strip()
                clean = clean[:40].strip()  # type: ignore
                if clean:
                    return clean.replace(" ", "_")
        return f"guion_{int(time.time())}"

    # ═══════════════════════════════════════════════
    # UTILIDADES
    # ═══════════════════════════════════════════════

    def _get_active_mode(self):
        current_main_tab = getattr(self, "tabview", None)
        if current_main_tab and current_main_tab.get() == "🎬 Orquestador de Series":  # type: ignore
            return (
                self.orchestrator_mode_var.get()
                if self.orchestrator_mode_var
                else "DUAL AI"
            )  # type: ignore
        return self.pre_mode_var.get() if self.pre_mode_var else "DUAL AI"  # type: ignore

    def _get_active_format(self):
        current_main_tab = getattr(self, "tabview", None)
        if current_main_tab and current_main_tab.get() == "🎬 Orquestador de Series":  # type: ignore
            return (
                self.orchestrator_format_var.get()
                if self.orchestrator_format_var
                else "9:16"
            )  # type: ignore
        return "9:16"

    def _parse_editor_json(self, editor_hint: str | None = None):
        """Parsea el JSON del editor correcto según el contexto activo."""
        # Detectar si estamos en el Orquestador
        current_main_tab = self.tabview.get() if hasattr(self, "tabview") else None  # type: ignore
        if current_main_tab == "🎬 Orquestador de Series":
            current_chapter_tab = (
                self.modules_tabview.get() if self.modules_tabview else "Bienvenido"
            )  # type: ignore

            # Primero verificar si hay JSON en chapter_editors (sistema series)
            if current_chapter_tab in self.chapter_editors:
                json_str = (
                    self.chapter_editors[current_chapter_tab].get("1.0", "end").strip()
                )
                editor_name = f"Orquestador ({current_chapter_tab})"
            # Verificar si hay capítulo seleccionado con sub-tabs
            elif hasattr(self, "_module_chapter_tabs") and self._module_chapter_tabs:
                # El tab actual es un módulo, buscar capítulo seleccionado
                current_mod = None
                for mod_nro, chapter_tabs in self._module_chapter_tabs.items():
                    tab_name = f"M{mod_nro}"
                    if tab_name == current_chapter_tab:
                        current_mod = mod_nro
                        break

                if current_mod is not None:
                    chapter_tabs = self._module_chapter_tabs[current_mod]
                    selected_cap = chapter_tabs.get()  # Obtener capítulo seleccionado
                    cap_key = f"M{current_mod}-{selected_cap}"

                    # Buscar en caché de JSON del curso
                    if (
                        hasattr(self, "_chapter_json_cache")
                        and cap_key in self._chapter_json_cache
                    ):
                        json_array = self._chapter_json_cache[cap_key]
                        editor_name = f"Curso ({cap_key})"
                        return json_array

                self.append_chat(
                    "Sistema",
                    "⚠ Selecciona un capítulo del curso y genera su JSON primero.",
                )
                return None
            else:
                self.append_chat(
                    "Sistema",
                    "⚠ No hay ningún capítulo seleccionado en el Orquestador.",
                )
                return None
        else:
            # Determinar qué editor leer:
            # 1. Si viene un hint del ActionHandler ("a" o "b"), usarlo.
            # 2. Si no, usar el modo activo para decidir.
            if editor_hint is None:
                mode = self._get_active_mode()
                use_b = mode == "SOLO TERM"
            else:
                use_b = editor_hint == "b"

            if use_b:
                json_str = self.editor_b.get("1.0", "end").strip()
                editor_name = "Terminal B"
            else:
                json_str = self.editor.get("1.0", "end").strip()
                editor_name = "Terminal A"

        if not json_str:
            self.append_chat("Sistema", f"⚠ El editor de {editor_name} está vacío.")
            return None
        try:
            data = json.loads(json_str)
            if not isinstance(data, list):
                self.append_chat("Sistema", "⚠ El JSON debe ser un arreglo [].")
                return None
            return data
        except json.JSONDecodeError as e:
            self.append_chat("Error", f"❌ JSON inválido: {e}")
            return None

    def _build_opencode_chat_panel(self):
        """Opencode tab — Chat panel for interacting with the AI about the project."""
        panel = ctk.CTkFrame(
            self.tab6,
            fg_color=COLORS["bg_panel"],
            corner_radius=12,
            border_width=1,
            border_color=COLORS["border"],
        )
        panel.grid(row=0, column=0, sticky="nsew", padx=(4, 2), pady=8)
        panel.grid_rowconfigure(1, weight=1)
        panel.grid_columnconfigure(0, weight=1)

        # Header
        header = ctk.CTkFrame(
            panel, fg_color=COLORS["header_bg"], height=48, corner_radius=0
        )
        header.grid(row=0, column=0, sticky="ew")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text="🧠", font=("Arial", 20)).pack(
            side="left", padx=(12, 4)
        )
        ctk.CTkLabel(
            header,
            text="OPENCODE AI",
            font=("JetBrains Mono", 14, "bold"),
            text_color=COLORS["accent_cyan"],
        ).pack(side="left")
        self._opencode_chat_status_label = ctk.CTkLabel(
            header,
            text="● EN LÍNEA",
            font=("JetBrains Mono", 10),
            text_color=COLORS["accent_green"],
        )
        self._opencode_chat_status_label.pack(side="right", padx=12)

        # Chat display
        self._opencode_chat_display = ctk.CTkTextbox(
            panel,
            wrap="word",
            font=("JetBrains Mono", 12),
            fg_color=COLORS["bg_chat"],
            text_color=COLORS["text_primary"],
            state="disabled",
            border_width=0,
            height=250,
        )
        self._opencode_chat_display.grid(
            row=1, column=0, sticky="nsew", padx=6, pady=(4, 4)
        )

        # Configure tags for messages
        self._opencode_chat_display._textbox.tag_config(
            "opencode_sender_system", foreground=COLORS["accent_yellow"]
        )
        self._opencode_chat_display._textbox.tag_config(
            "opencode_sender_user", foreground=COLORS["accent_cyan"]
        )
        self._opencode_chat_display._textbox.tag_config(
            "opencode_sender_ai", foreground=COLORS["accent_green"]
        )
        self._opencode_chat_display._textbox.tag_config(
            "opencode_sender_error", foreground=COLORS["accent_red"]
        )
        self._opencode_chat_display._textbox.tag_config(
            "opencode_msg_body", foreground=COLORS["text_primary"]
        )

        # Input
        input_frame = ctk.CTkFrame(panel, fg_color="transparent")
        input_frame.grid(row=2, column=0, sticky="ew", padx=6, pady=(0, 6))
        self._opencode_chat_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="Pídele a la AI que analice la salida o sugiera próximos pasos...",
            font=("JetBrains Mono", 12),
            fg_color=COLORS["bg_dark"],
            border_color=COLORS["border"],
        )
        self._opencode_chat_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self._opencode_chat_entry.bind(
            "<Return>", lambda e: self._opencode_send_chat_message()
        )
        self._opencode_chat_btn = ctk.CTkButton(
            input_frame,
            text="⚡",
            width=45,
            command=self._opencode_send_chat_message,
            font=("Arial", 18),
            fg_color=COLORS["accent_cyan"],
            text_color="#000000",
            hover_color="#00b8d4",
        )
        self._opencode_chat_btn.pack(side="right")

    def _opencode_send_chat_message(self):
        """Send a message in the Opencode chat and get AI response."""
        user_text = self._opencode_chat_entry.get().strip()
        if not user_text:
            return
        self._opencode_chat_entry.delete(0, "end")
        self._opencode_append_chat("Tú", user_text)
        self._opencode_chat_entry.configure(state="disabled")
        self._opencode_chat_btn.configure(state="disabled")
        self._opencode_chat_status_label.configure(
            text="⚡ PROCESANDO", text_color=COLORS["accent_yellow"]
        )
        threading.Thread(
            target=self._opencode_process_chat, args=(user_text,), daemon=True
        ).start()

    def _opencode_append_chat(self, sender: str, text: str):
        """Append a styled message to the Opencode chat display."""
        self._opencode_chat_display.configure(state="normal")
        tb = self._opencode_chat_display._textbox
        sender_lower = sender.lower()
        if sender_lower in ("sistema",):
            tag = "opencode_sender_system"
        elif sender_lower in ("tú",):
            tag = "opencode_sender_user"
        elif sender_lower in ("opencode ai", "ai"):
            tag = "opencode_sender_ai"
        else:
            tag = "opencode_sender_error"
        tb.insert("end", f"[{sender}] ", tag)
        tb.insert("end", f"{text}\n\n", "opencode_msg_body")
        self._opencode_chat_display.see("end")
        self._opencode_chat_display.configure(state="disabled")

    def _opencode_process_chat(self, prompt: str):
        """Process a chat message in a background thread."""
        try:
            # For now, just echo and suggest a next step
            response = f"[OPENCODE AI] He recibido: '{prompt}'. Para continuar con el desarrollo iterativo, necesitas proporcionar un JSON inicial en el editor y presionar 'Iniciar Iteración'."
            self.after(0, self._opencode_append_chat, "OPENCODE AI", response)
        except Exception as e:
            self.after(0, self._opencode_append_chat, "Error", f"❌ {str(e)}")
        finally:
            self.after(0, lambda: self._opencode_chat_entry.configure(state="normal"))
            self.after(0, lambda: self._opencode_chat_btn.configure(state="normal"))
            self.after(
                0,
                lambda: self._opencode_chat_status_label.configure(
                    text="● EN LÍNEA", text_color=COLORS["accent_green"]
                ),
            )

    def _build_opencode_editor_panel(self):
        """Opencode tab — Editor panel for the iterative JSON."""
        panel = ctk.CTkFrame(
            self.tab6,
            fg_color=COLORS["bg_panel"],
            corner_radius=12,
            border_width=1,
            border_color=COLORS["border"],
        )
        panel.grid(row=0, column=1, sticky="nsew", padx=(2, 4), pady=8)
        panel.grid_rowconfigure(1, weight=1)
        panel.grid_columnconfigure(0, weight=1)

        # Header
        header = ctk.CTkFrame(
            panel, fg_color=COLORS["header_bg"], height=42, corner_radius=0
        )
        header.grid(row=0, column=0, sticky="ew")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text="📝", font=("Arial", 18)).pack(
            side="left", padx=(12, 4)
        )
        ctk.CTkLabel(
            header,
            text="OPENCODE EDITOR",
            font=("JetBrains Mono", 13, "bold"),
            text_color=COLORS["accent_cyan"],
        ).pack(side="left")

        # Editor container with line numbers and syntax highlighting (similar to main editor)
        editor_container = ctk.CTkFrame(panel, fg_color="transparent")
        editor_container.grid(row=1, column=0, sticky="nsew", padx=6, pady=(2, 6))
        editor_container.grid_rowconfigure(1, weight=1)
        editor_container.grid_columnconfigure(0, weight=1)

        # Line numbers
        self._opencode_line_numbers = tk.Text(
            editor_container,
            width=4,
            bg="#08090a",
            fg="#3a3a5a",
            font=("JetBrains Mono", 10),
            state="disabled",
            relief="flat",
            bd=0,
            selectbackground="#08090a",
            highlightthickness=0,
            padx=6,
            pady=4,
        )
        self._opencode_line_numbers.pack(side="left", fill="y")

        # Main editor
        self._opencode_editor = tk.Text(
            editor_container,
            bg=COLORS["bg_editor"],
            fg=COLORS["text_primary"],
            font=("JetBrains Mono", 10),
            insertbackground=COLORS["accent_cyan"],
            selectbackground="#1a2a4a",
            relief="flat",
            bd=0,
            wrap="word",
            highlightthickness=0,
            padx=8,
            pady=4,
            undo=True,
        )
        self._opencode_editor.pack(side="left", fill="both", expand=True)

        # Scrollbar
        _opencode_scrollbar = ctk.CTkScrollbar(
            editor_container, command=self._opencode_editor.yview
        )
        _opencode_scrollbar.pack(side="right", fill="y")
        self._opencode_editor.configure(yscrollcommand=self._opencode_sync_scroll)

        # Syntax highlighting tags
        for ed in [self._opencode_editor]:
            ed.tag_config("opencode_json_key", foreground="#9CDCFE")
            ed.tag_config("opencode_json_string", foreground="#CE9178")
            ed.tag_config("opencode_json_bracket", foreground="#FFD700")
            ed.tag_config("opencode_json_keyword", foreground="#C586C0")
            ed.tag_config("opencode_json_colon", foreground="#D4D4D4")
            ed.tag_config("opencode_json_number", foreground="#B5CEA8")

        # Bind events for auto-save and line numbers
        self._opencode_editor.bind(
            "<KeyRelease>", lambda e: self._opencode_schedule_auto_save()
        )
        self._opencode_editor.bind(
            "<ButtonRelease-1>", lambda e: self._opencode_update_line_numbers()
        )

        # Control buttons below the editor
        btn_frame = ctk.CTkFrame(panel, fg_color="transparent")
        btn_frame.grid(row=2, column=0, sticky="ew", padx=6, pady=(0, 6))

        self._opencode_start_btn = ctk.CTkButton(
            btn_frame,
            text="▶️ Iniciar Iteración",
            command=self._opencode_start_iteration,
            font=("JetBrains Mono", 11, "bold"),
            height=35,
            fg_color="#1a1b2e",
            hover_color="#252640",
            border_width=1,
            border_color=COLORS["accent_cyan"],
        )
        self._opencode_start_btn.pack(side="left", expand=True, fill="x", padx=(0, 5))

        self._opencode_stop_btn = ctk.CTkButton(
            btn_frame,
            text="⏹ Detener",
            command=self._opencode_stop_iteration,
            font=("JetBrains Mono", 11, "bold"),
            height=35,
            fg_color="#1a1b2e",
            hover_color="#252640",
            border_width=1,
            border_color=COLORS["accent_red"],
        )
        self._opencode_stop_btn.pack(side="left", expand=True, fill="x", padx=5)
        self._opencode_stop_btn.configure(state="disabled")

        self._opencode_export_btn = ctk.CTkButton(
            btn_frame,
            text="💾 Exportar para Kdenlive",
            command=self._opencode_export_for_kdenlive,
            font=("JetBrains Mono", 11, "bold"),
            height=35,
            fg_color="#1a1b2e",
            hover_color="#252640",
            border_width=1,
            border_color=COLORS["accent_yellow"],
        )
        self._opencode_export_btn.pack(side="left", expand=True, fill="x", padx=(5, 0))
        self._opencode_export_btn.configure(state="disabled")

    def _opencode_sync_scroll(self, *args):
        self._opencode_line_numbers.yview_moveto(args[0] if args else 0)

    def _opencode_update_line_numbers(self):
        content = self._opencode_editor.get("1.0", "end-1c")
        lines = content.split("\n")
        ln_text = "\n".join(str(i + 1) for i in range(len(lines)))
        self._opencode_line_numbers.configure(state="normal")
        self._opencode_line_numbers.delete("1.0", "end")
        self._opencode_line_numbers.insert("1.0", ln_text)
        self._opencode_line_numbers.configure(state="disabled")
        self._opencode_line_numbers.yview_moveto(self._opencode_editor.yview()[0])

    def _opencode_schedule_auto_save(self):
        # Placeholder for auto-save logic (similar to main editor)
        if self._opencode_auto_save_after_id:
            self.after_cancel(self._opencode_auto_save_after_id)
        self._opencode_auto_save_after_id = self.after(
            self._auto_save_delay_ms, self._opencode_perform_auto_save
        )

    def _opencode_perform_auto_save(self):
        self._opencode_auto_save_after_id = None
        json_str = self._opencode_editor.get("1.0", "end-1c").strip()
        if not json_str:
            return
        try:
            json_data = json.loads(json_str)
            if isinstance(json_data, list):
                # Use the same auto-save project logic as main editor but maybe with a different prefix?
                self._opencode_auto_save_project(json_data)
        except json.JSONDecodeError:
            pass

    def _opencode_auto_save_project(self, json_data: list):
        # Save to a special opencode autosave folder or just use the main projects dir with a tag?
        title = self._extract_project_title(json_data)
        if not title:
            title = f"opencode_{int(time.time())}"
        proj_dir = os.path.join(self.projects_dir, title)
        os.makedirs(proj_dir, exist_ok=True)
        filepath = os.path.join(proj_dir, "guion.json")
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=4, ensure_ascii=False)
            # Optionally update a label to show the autosave project name
        except Exception:
            pass

    def _opencode_start_iteration(self):
        # Placeholder for starting the iterative process
        self._opencode_append_chat(
            "Sistema", "🚀 Iniciando proceso iterativo Opencode..."
        )
        self._opencode_start_btn.configure(state="disabled")
        self._opencode_stop_btn.configure(state="normal")
        # Set a flag that the iteration is running
        self._opencode_is_running = True
        # We'll implement the actual cycle in a separate method that we call via after
        self._opencode_iteration_cycle()

    def _opencode_stop_iteration(self):
        self._opencode_append_chat("Sistema", "⏹ Deteniendo proceso iterativo.")
        self._opencode_is_running = False
        self._opencode_start_btn.configure(state="normal")
        self._opencode_stop_btn.configure(state="disabled")
        self._opencode_export_btn.configure(
            state="normal"
        )  # Enable export after stopping

    def _opencode_export_for_kdenlive(self):
        self._opencode_append_chat(
            "Sistema", "🎬 Exportando proyecto para Kdenlive (placeholder)..."
        )
        # Here we would generate the TTS scripts and Kdenlive project file

    def _opencode_iteration_cycle(self):
        """One cycle of the Opencode iterative process."""
        if not self._opencode_is_running:
            return

        # 1. Get current JSON from the editor
        json_str = self._opencode_editor.get("1.0", "end-1c").strip()
        if not json_str:
            self._opencode_append_chat(
                "Sistema", "⚠ Editor vacío. Proporcione un JSON inicial."
            )
            self._opencode_stop_iteration()
            return
        try:
            current_json = json.loads(json_str)
            if not isinstance(current_json, list):
                self._opencode_append_chat(
                    "Sistema", "⚠ El JSON debe ser un arreglo de escenas."
                )
                self._opencode_stop_iteration()
                return
        except json.JSONDecodeError as e:
            self._opencode_append_chat("Sistema", f"⚠ JSON inválido: {e}")
            self._opencode_stop_iteration()
            return

        # 2. Execute the JSON in terminal (we'll need to implement a safe executor)
        # For now, we'll simulate execution and then use the AI to analyze and suggest next steps.
        self._opencode_append_chat(
            "Sistema", "🔧 Ejecutando JSON actual en terminal (simulado)..."
        )
        # In a real implementation, we would capture the output of executing the commands.
        # For this placeholder, we'll just pretend we got some output.
        execution_result = {
            "success": True,
            "output": "Simulated execution: all commands succeeded.",
            # In reality, we would have more detailed output per command.
        }

        # 3. Use the AI to analyze the output and suggest next steps
        self._opencode_append_chat("Sistema", "🤖 Analizando resultados con la AI...")
        # We'll create a prompt for the AI to analyze the execution and update the JSON.
        # For brevity, we'll use a simple placeholder response.
        # In a full implementation, we would call the AI engine with a detailed prompt.
        ai_suggestion = {
            "analysis": "La ejecución fue exitosa. Próximos pasos: añadir una escena de conclusión y exportar.",
            "next_json": current_json
            + [
                {
                    "tipo": "narracion",
                    "voz": "En este punto, hemos completado los pasos iniciales. El siguiente paso sería finalizar y exportar el proyecto.",
                }
            ],
        }

        # 4. Update the editor with the new JSON from the AI
        self._opencode_editor.delete("1.0", "end")
        self._opencode_editor.insert(
            "end", json.dumps(ai_suggestion["next_json"], indent=4, ensure_ascii=False)
        )
        self._opencode_update_line_numbers()
        self._opencode_append_chat("OPENCODE AI", ai_suggestion["analysis"])

        # 5. Check if we should stop (for now, we'll stop after one cycle for demonstration)
        # In a real implementation, we would have a condition to detect when the project is complete.
        self._opencode_append_chat(
            "Sistema", "🔄 Ciclo completado. Deteniendo por demostración."
        )
        self._opencode_stop_iteration()

        # In a real version, we would not stop here but schedule another cycle:
        # if self._opencode_is_running:
        #     self.after(2000, self._opencode_iteration_cycle)

    def _build_opencode_tab(self):
        # Initialize state variables for the Opencode iterative process
        if not hasattr(self, "_opencode_is_running"):
            self._opencode_is_running = False
        if not hasattr(self, "_opencode_auto_save_after_id"):
            self._opencode_auto_save_after_id = None
        if not hasattr(self, "_opencode_iteration_after_id"):
            self._opencode_iteration_after_id = None

        # Create a main frame for the tab with two columns: chat and editor
        main_frame = ctk.CTkFrame(self.tab6, fg_color="transparent")
        main_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.tab6.grid_rowconfigure(0, weight=1)
        self.tab6.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)

        # === LEFT PANEL: CHAT ===
        chat_frame = ctk.CTkFrame(
            main_frame, fg_color=COLORS["bg_panel"], corner_radius=8
        )
        chat_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 3), pady=0)
        chat_frame.grid_rowconfigure(1, weight=1)
        chat_frame.grid_columnconfigure(0, weight=1)

        # Chat header
        chat_header = ctk.CTkFrame(
            chat_frame, fg_color=COLORS["header_bg"], height=40, corner_radius=0
        )
        chat_header.grid(row=0, column=0, sticky="ew")
        chat_header.grid_propagate(False)
        ctk.CTkLabel(chat_header, text="💬", font=("Arial", 18)).pack(
            side="left", padx=(10, 5)
        )
        ctk.CTkLabel(
            chat_header,
            text="OPENCODE CHAT",
            font=("JetBrains Mono", 12, "bold"),
            text_color=COLORS["accent_cyan"],
        ).pack(side="left")
        self._opencode_chat_status_label = ctk.CTkLabel(
            chat_header,
            text="● IDLE",
            font=("JetBrains Mono", 10),
            text_color=COLORS["text_dim"],
        )
        self._opencode_chat_status_label.pack(side="right", padx=10)

        # Chat display
        self._opencode_chat_display = ctk.CTkTextbox(
            chat_frame,
            wrap="word",
            font=("JetBrains Mono", 11),
            fg_color=COLORS["bg_chat"],
            text_color=COLORS["text_primary"],
            state="disabled",
            border_width=0,
            height=200,
        )
        self._opencode_chat_display.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        # Configure chat tags
        self._opencode_chat_display._textbox.tag_config(
            "opencode_sender_system", foreground=COLORS["accent_yellow"]
        )
        self._opencode_chat_display._textbox.tag_config(
            "opencode_sender_user", foreground=COLORS["accent_cyan"]
        )
        self._opencode_chat_display._textbox.tag_config(
            "opencode_sender_ai", foreground=COLORS["accent_green"]
        )
        self._opencode_chat_display._textbox.tag_config(
            "opencode_sender_error", foreground=COLORS["accent_red"]
        )
        self._opencode_chat_display._textbox.tag_config(
            "opencode_msg_body", foreground=COLORS["text_primary"]
        )

        # Chat input
        chat_input_frame = ctk.CTkFrame(chat_frame, fg_color="transparent")
        chat_input_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=(0, 5))
        self._opencode_chat_entry = ctk.CTkEntry(
            chat_input_frame,
            placeholder_text="Escribe un mensaje para la IA...",
            font=("JetBrains Mono", 11),
            fg_color=COLORS["bg_dark"],
            border_color=COLORS["border"],
        )
        self._opencode_chat_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self._opencode_chat_entry.bind(
            "<Return>", lambda e: self._opencode_send_chat_message()
        )
        self._opencode_chat_btn = ctk.CTkButton(
            chat_input_frame,
            text="⚡",
            width=35,
            command=self._opencode_send_chat_message,
            font=("Arial", 14),
            fg_color=COLORS["accent_cyan"],
            text_color="#000000",
            hover_color="#00b8d4",
        )
        self._opencode_chat_btn.pack(side="right")

        # === RIGHT PANEL: EDITOR AND CONTROLS ===
        editor_frame = ctk.CTkFrame(
            main_frame, fg_color=COLORS["bg_panel"], corner_radius=8
        )
        editor_frame.grid(row=0, column=1, sticky="nsew", padx=(3, 0), pady=0)
        editor_frame.grid_rowconfigure(1, weight=1)
        editor_frame.grid_columnconfigure(0, weight=1)
        editor_frame.grid_rowconfigure(2, weight=0)  # For control buttons

        # Editor header
        editor_header = ctk.CTkFrame(
            editor_frame, fg_color=COLORS["header_bg"], height=40, corner_radius=0
        )
        editor_header.grid(row=0, column=0, sticky="ew")
        editor_header.grid_propagate(False)
        ctk.CTkLabel(editor_header, text="📄", font=("Arial", 18)).pack(
            side="left", padx=(10, 5)
        )
        ctk.CTkLabel(
            editor_header,
            text="OPENCODE EDITOR",
            font=("JetBrains Mono", 12, "bold"),
            text_color=COLORS["accent_cyan"],
        ).pack(side="left")

        # Editor with line numbers
        editor_container = ctk.CTkFrame(editor_frame, fg_color="transparent")
        editor_container.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        editor_container.grid_rowconfigure(1, weight=1)
        editor_container.grid_columnconfigure(0, weight=1)

        # Line numbers
        self._opencode_line_numbers = tk.Text(
            editor_container,
            width=4,
            bg="#08090a",
            fg="#3a3a5a",
            font=("JetBrains Mono", 10),
            state="disabled",
            relief="flat",
            bd=0,
            selectbackground="#08090a",
            highlightthickness=0,
            padx=6,
            pady=4,
        )
        self._opencode_line_numbers.pack(side="left", fill="y")

        # Main editor
        self._opencode_editor = tk.Text(
            editor_container,
            bg=COLORS["bg_editor"],
            fg=COLORS["text_primary"],
            font=("JetBrains Mono", 10),
            insertbackground=COLORS["accent_cyan"],
            selectbackground="#1a2a4a",
            relief="flat",
            bd=0,
            wrap="word",
            highlightthickness=0,
            padx=8,
            pady=4,
            undo=True,
        )
        self._opencode_editor.pack(side="left", fill="both", expand=True)

        # Scrollbar for editor
        _opencode_scrollbar = ctk.CTkScrollbar(
            editor_container, command=self._opencode_editor.yview
        )
        _opencode_scrollbar.pack(side="right", fill="y")
        self._opencode_editor.configure(yscrollcommand=self._opencode_sync_scroll)

        # Syntax highlighting tags for the editor
        self._opencode_editor.tag_config("opencode_json_key", foreground="#9CDCFE")
        self._opencode_editor.tag_config("opencode_json_string", foreground="#CE9178")
        self._opencode_editor.tag_config("opencode_json_bracket", foreground="#FFD700")
        self._opencode_editor.tag_config("opencode_json_keyword", foreground="#C586C0")
        self._opencode_editor.tag_config("opencode_json_colon", foreground="#D4D4D4")
        self._opencode_editor.tag_config("opencode_json_number", foreground="#B5CEA8")

        # Bind events for auto-save and line number updates
        self._opencode_editor.bind(
            "<KeyRelease>", lambda e: self._opencode_schedule_auto_save()
        )
        self._opencode_editor.bind(
            "<ButtonRelease-1>", lambda e: self._opencode_update_line_numbers()
        )

        # Control buttons below the editor
        btn_frame = ctk.CTkFrame(editor_frame, fg_color="transparent")
        btn_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=(0, 5))

        self._opencode_start_btn = ctk.CTkButton(
            btn_frame,
            text="▶️ Iniciar Iteración",
            command=self._opencode_start_iteration,
            font=("JetBrains Mono", 11, "bold"),
            height=35,
            fg_color="#1a1b2e",
            hover_color="#252640",
            border_width=1,
            border_color=COLORS["accent_cyan"],
        )
        self._opencode_start_btn.pack(side="left", expand=True, fill="x", padx=(0, 3))

        self._opencode_stop_btn = ctk.CTkButton(
            btn_frame,
            text="⏹ Detener",
            command=self._opencode_stop_iteration,
            font=("JetBrains Mono", 11, "bold"),
            height=35,
            fg_color="#1a1b2e",
            hover_color="#252640",
            border_width=1,
            border_color=COLORS["accent_red"],
        )
        self._opencode_stop_btn.pack(side="left", expand=True, fill="x", padx=3)
        self._opencode_stop_btn.configure(state="disabled")

        self._opencode_export_btn = ctk.CTkButton(
            btn_frame,
            text="🚀 Ejecutar en Terminal",
            command=self._opencode_execute_in_terminal,
            font=("JetBrains Mono", 11, "bold"),
            height=35,
            fg_color="#1a1b2e",
            hover_color="#252640",
            border_width=1,
            border_color=COLORS["accent_green"],
        )
        self._opencode_export_btn.pack(side="left", expand=True, fill="x", padx=(3, 0))
        self._opencode_export_btn.configure(state="disabled")

        self._opencode_test_btn = ctk.CTkButton(
            btn_frame,
            text="🐞 Test Terminal",
            command=self._opencode_test_terminal,
            font=("JetBrains Mono", 11, "bold"),
            height=35,
            fg_color="#3D3D3D",
            hover_color="#555555",
        )
        self._opencode_test_btn.pack(side="left", padx=(5, 0))

        # Status label for iteration progress
        self._opencode_iteration_status_label = ctk.CTkLabel(
            editor_frame,
            text="Listo para comenzar",
            font=("JetBrains Mono", 10),
            text_color=COLORS["text_dim"],
            height=20,
        )
        self._opencode_iteration_status_label.grid(
            row=3, column=0, sticky="ew", padx=5, pady=(0, 5)
        )

    def _opencode_test_terminal(self):
        """Función de diagnóstico para probar el control de la terminal."""
        self._opencode_append_chat("Sistema", "🐞 Iniciando test de terminal...")
        if not self.wid_b:
            self._opencode_append_chat(
                "Error", "❌ Terminal B (wid_b) no está definida. Ábrela primero."
            )
            return

        self._opencode_append_chat(
            "Sistema", f"Intentando escribir en WID: {self.wid_b}"
        )

        # Usar un hilo para no bloquear la UI
        def test_thread():
            try:
                from kr_studio.core.x11_controller import X11Controller

                x11 = X11Controller()
                # 1. Foco (opcional pero bueno para visibilidad)
                x11.focus_window(str(self.wid_b))
                time.sleep(0.5)

                # 2. Escribir comando
                test_cmd = 'echo "✅ TEST DE TERMINAL EXITOSO"'
                x11.type_text(str(self.wid_b), test_cmd, speed_pct=100)
                time.sleep(0.5)

                # 3. Enviar Enter
                x11.send_key(str(self.wid_b), "Return")

                self.after(
                    0,
                    self._opencode_append_chat,
                    "Sistema",
                    "✅ Test enviado. Revisa la terminal.",
                )
            except Exception as e:
                self.after(
                    0, self._opencode_append_chat, "Error", f"❌ Falló el test: {e}"
                )

        threading.Thread(target=test_thread, daemon=True).start()

    def _opencode_sync_scroll(self, *args):
        self._opencode_line_numbers.yview_moveto(args[0] if args else 0)

    def _opencode_update_line_numbers(self):
        content = self._opencode_editor.get("1.0", "end-1c")
        lines = content.split("\n")
        ln_text = "\n".join(str(i + 1) for i in range(len(lines)))
        self._opencode_line_numbers.configure(state="normal")
        self._opencode_line_numbers.delete("1.0", "end")
        self._opencode_line_numbers.insert("1.0", ln_text)
        self._opencode_line_numbers.configure(state="disabled")
        self._opencode_line_numbers.yview_moveto(self._opencode_editor.yview()[0])

    def _opencode_schedule_auto_save(self):
        if self._opencode_auto_save_after_id:
            self.after_cancel(self._opencode_auto_save_after_id)
        self._opencode_auto_save_after_id = self.after(
            self._auto_save_delay_ms, self._opencode_perform_auto_save
        )

    def _opencode_perform_auto_save(self):
        self._opencode_auto_save_after_id = None
        json_str = self._opencode_editor.get("1.0", "end-1c").strip()
        if not json_str:
            return
        try:
            json_data = json.loads(json_str)
            if isinstance(json_data, list):
                self._opencode_auto_save_project(json_data)
        except json.JSONDecodeError:
            pass

    def _opencode_auto_save_project(self, json_data: list):
        title = self._extract_project_title(json_data)
        if not title:
            title = f"opencode_{int(time.time())}"
        proj_dir = os.path.join(self.projects_dir, title)
        os.makedirs(proj_dir, exist_ok=True)
        filepath = os.path.join(proj_dir, "guion.json")
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=4, ensure_ascii=False)
            # Update a status label if we have one (optional)
            if hasattr(self, "_opencode_iteration_status_label"):
                self._opencode_iteration_status_label.configure(
                    text=f"Proyecto guardado: {title}", text_color=COLORS["accent_cyan"]
                )
                self.after(
                    3000,
                    lambda: self._opencode_iteration_status_label.configure(
                        text="Listo para continuar", text_color=COLORS["text_dim"]
                    ),
                )
        except Exception as e:
            if hasattr(self, "_opencode_iteration_status_label"):
                self._opencode_iteration_status_label.configure(
                    text=f"Error al guardar: {e}", text_color=COLORS["accent_red"]
                )

    def _opencode_send_chat_message(self):
        user_text = self._opencode_chat_entry.get().strip()
        if not user_text:
            return
        self._opencode_chat_entry.delete(0, "end")
        self._opencode_append_chat("Tú", user_text)
        self._opencode_chat_entry.configure(state="disabled")
        self._opencode_chat_btn.configure(state="disabled")
        self._opencode_chat_status_label.configure(
            text="⚡ PROCESANDO", text_color=COLORS["accent_yellow"]
        )
        threading.Thread(
            target=self._opencode_process_chat, args=(user_text,), daemon=True
        ).start()

    def _opencode_append_chat(self, sender: str, text: str):
        self._opencode_chat_display.configure(state="normal")
        tb = self._opencode_chat_display._textbox
        sender_lower = sender.lower()
        if sender_lower in ("sistema",):
            tag = "opencode_sender_system"
        elif sender_lower in ("tú",):
            tag = "opencode_sender_user"
        elif sender_lower in ("opencode ai", "ai"):
            tag = "opencode_sender_ai"
        else:
            tag = "opencode_sender_error"
        tb.insert("end", f"[{sender}] ", tag)
        tb.insert("end", f"{text}\n\n", "opencode_msg_body")
        self._opencode_chat_display.see("end")
        self._opencode_chat_display.configure(state="disabled")

    def _opencode_process_chat(self, prompt: str):
        self._opencode_append_chat("OPENCODE AI", "🔄 Generando JSON iterativo...")
        threading.Thread(
            target=self._opencode_generate_json, args=(prompt,), daemon=True
        ).start()

    def _opencode_generate_json(self, prompt: str):
        try:
            opencode_prompt = (
                f"Eres un generador de guiones JSON para videos tutoriales de terminal.\n"
                f"Crea un guion completo para el tema: {prompt}\n\n"
                f"Genera EXACTAMENTE un JSON array con este formato:\n"
                f'[\n  {{\n    "tipo": "narracion",\n    "voz": "Texto de narración para TTS",\n    "espera": 2\n  }},\n  {{\n    "tipo": "ejecucion",\n    "comando_real": "comando de terminal",\n    "voz": "Narración mientras se ejecuta el comando"\n  }},\n  {{\n    "tipo": "pausa",\n    "espera": 3\n  }}\n]\n\n'
                f"REGLAS:\n"
                f"- 'narracion': Texto para narrar (TTS) + espera adicional en segundos\n"
                f"- 'ejecucion': Comando a ejecutar en terminal + narración\n"
                f"- 'pausa': Pausa pura en segundos (para esperar resultado)\n"
                f"- Incluye comandos realistas de terminal Linux/Bash\n"
                f"- La voz describe lo que hace el comando\n"
                f"Solo responde con el JSON válido, sin markdown ni explicaciones."
            )
            response = self.ai.chat(opencode_prompt)
            text = response.strip()
            text = re.sub(r"```json\s*", "", text)
            text = re.sub(r"```\s*", "", text)
            text = text.strip()
            json_data = json.loads(text)
            json_str = json.dumps(json_data, indent=4, ensure_ascii=False)

            def update_editor():
                self._opencode_editor.delete("1.0", "end")
                self._opencode_editor.insert("end", json_str)
                self._opencode_update_line_numbers()
                self._opencode_append_chat(
                    "OPENCODE AI",
                    f"✅ Guion generado con {len(json_data)} escena(s)\n"
                    "Presiona '🚀 Ejecutar en Terminal' para iniciar.",
                )
                self._opencode_iteration_status_label.configure(
                    text=f"Guion listo: {len(json_data)} escenas",
                    text_color=COLORS["accent_green"],
                )
                self._opencode_export_btn.configure(state="normal")

            response = self.ai.chat(opencode_prompt)
            text = response.strip()
            text = re.sub(r"```json\s*", "", text)
            text = re.sub(r"```\s*", "", text)
            text = text.strip()
            json_data = json.loads(text)
            json_str = json.dumps(json_data, indent=4, ensure_ascii=False)

            def update_editor():
                self._opencode_editor.delete("1.0", "end")
                self._opencode_editor.insert("end", json_str)
                self._opencode_update_line_numbers()
                self._opencode_append_chat(
                    "OPENCODE AI",
                    f"✅ JSON generado con {len(json_data)} escena(s)\n"
                    "Edita el JSON manualmente o usa 'Iniciar Iteración' para refinarlo.",
                )
                self._opencode_iteration_status_label.configure(
                    text=f"JSON listo: {len(json_data)} escenas",
                    text_color=COLORS["accent_green"],
                )

            self.after(0, update_editor)
        except json.JSONDecodeError as e:
            self.after(0, self._opencode_append_chat, "Error", f"❌ JSON inválido: {e}")
        except Exception as e:
            self.after(0, self._opencode_append_chat, "Error", f"❌ {str(e)}")
        finally:
            self.after(0, lambda: self._opencode_chat_entry.configure(state="normal"))
            self.after(0, lambda: self._opencode_chat_btn.configure(state="normal"))
            self.after(
                0,
                lambda: self._opencode_chat_status_label.configure(
                    text="● IDLE", text_color=COLORS["text_dim"]
                ),
            )

    def _opencode_start_iteration(self):
        # Validate that we have a JSON in the editor
        json_str = self._opencode_editor.get("1.0", "end-1c").strip()
        if not json_str:
            self._opencode_append_chat(
                "Sistema", "⚠ El editor está vacío. Proporcione un JSON inicial."
            )
            return
        try:
            data = json.loads(json_str)
            if not isinstance(data, list):
                self._opencode_append_chat(
                    "Sistema", "⚠ El JSON debe ser un arreglo de escenas."
                )
                return
        except json.JSONDecodeError as e:
            self._opencode_append_chat("Sistema", f"⚠ JSON inválido: {e}")
            return

        # Start the iteration process
        self._opencode_is_running = True
        self._opencode_start_btn.configure(state="disabled")
        self._opencode_stop_btn.configure(state="normal")
        self._opencode_export_btn.configure(state="disabled")
        self._opencode_chat_status_label.configure(
            text="⚡ EJECUTANDO", text_color=COLORS["accent_yellow"]
        )
        self._opencode_iteration_status_label.configure(
            text="Iniciando proceso iterativo...", text_color=COLORS["accent_cyan"]
        )
        self._opencode_append_chat(
            "Sistema", "🚀 Iniciando proceso iterativo Opencode..."
        )
        # Start the iteration cycle
        self._opencode_iteration_cycle()

    def _opencode_stop_iteration(self):
        self._opencode_is_running = False
        self._opencode_start_btn.configure(state="normal")
        self._opencode_stop_btn.configure(state="disabled")
        self._opencode_export_btn.configure(
            state="normal"
        )  # Enable export after stopping
        self._opencode_chat_status_label.configure(
            text="● IDLE", text_color=COLORS["text_dim"]
        )
        self._opencode_iteration_status_label.configure(
            text="Proceso detenido por el usuario", text_color=COLORS["accent_red"]
        )
        self._opencode_append_chat("Sistema", "⏹ Proceso iterativo detenido.")

    def _opencode_execute_in_terminal(self):
        json_str = self._opencode_editor.get("1.0", "end-1c").strip()
        if not json_str:
            self._opencode_append_chat(
                "Sistema", "⚠ Editor vacío. Genera un guion primero."
            )
            return
        try:
            json_data = json.loads(json_str)
            if not isinstance(json_data, list):
                self._opencode_append_chat(
                    "Sistema", "⚠ El JSON debe ser un arreglo de escenas."
                )
                return
        except json.JSONDecodeError as e:
            self._opencode_append_chat("Sistema", f"⚠ JSON inválido: {e}")
            return

        self._opencode_append_chat("Sistema", "🚀 Abriendo Terminal para Opencode...")
        self._opencode_iteration_status_label.configure(
            text="Abriendo terminal...", text_color=COLORS["accent_yellow"]
        )
        self._opencode_start_btn.configure(state="disabled")
        self._opencode_export_btn.configure(state="disabled")
        self._opencode_stop_btn.configure(state="normal")

        threading.Thread(
            target=self._opencode_open_terminal,
            args=(self._opencode_run_guion,),
            daemon=True,
        ).start()

    def _opencode_open_terminal(self, callback=None):
        """Abre una única terminal Konsole para Opencode, la configura y llama al callback."""
        import subprocess as sp
        import time

        try:
            # Cierra terminales previas para un estado limpio
            if self.wid_b:
                try:
                    sp.run(["xdotool", "windowclose", str(self.wid_b)], timeout=2)
                    self.wid_b = None
                except Exception:
                    pass  # Ignorar si la ventana ya no existe
            if self.wid_a:
                try:
                    sp.run(["xdotool", "windowclose", str(self.wid_a)], timeout=2)
                    self.wid_a = None
                except Exception:
                    pass
            time.sleep(0.5)

            # Abre una nueva y única terminal
            sp.Popen(["konsole"], stdout=sp.DEVNULL, stderr=sp.DEVNULL)
            time.sleep(2.0)

            # Busca el WID de la nueva terminal
            result = sp.run(
                ["xdotool", "search", "--class", "konsole"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            wids = [w.strip() for w in result.stdout.strip().split("\n") if w.strip()]

            if not wids:
                self.after(
                    0,
                    self._opencode_append_chat,
                    "Error",
                    "❌ No se pudo encontrar Konsole.",
                )
                return

            self.wid_b = wids[-1]
            self.wid_a = None
            self.after(
                0,
                self._opencode_append_chat,
                "Sistema",
                f"✅ Terminal B (WID: {self.wid_b}) lista.",
            )

            # Configura geometría y limpia la terminal
            sp.run(
                [
                    "xdotool",
                    "type",
                    "--window",
                    str(self.wid_b),
                    "--delay",
                    "15",
                    "resize -s 30 110",
                ],
                capture_output=True,
                timeout=5,
            )
            sp.run(
                ["xdotool", "key", "--window", str(self.wid_b), "Return"],
                capture_output=True,
                timeout=5,
            )
            time.sleep(0.5)
            sp.run(
                [
                    "xdotool",
                    "type",
                    "--window",
                    str(self.wid_b),
                    "--delay",
                    "15",
                    "clear",
                ],
                capture_output=True,
                timeout=5,
            )
            sp.run(
                ["xdotool", "key", "--window", str(self.wid_b), "Return"],
                capture_output=True,
                timeout=5,
            )

            if callback:
                self.after(500, callback)
        except FileNotFoundError:
            self.after(
                0,
                self._opencode_append_chat,
                "Error",
                "❌ 'konsole' o 'xdotool' no encontrado.",
            )
        except Exception as e:
            self.after(
                0, self._opencode_append_chat, "Error", f"⚠ Error de terminal: {e}"
            )

    def _opencode_run_guion(self):
        print("DEBUG: _opencode_run_guion called")
        self._opencode_append_chat("Sistema", "🎬 Iniciando ejecución del guion...")
        threading.Thread(target=self._opencode_execute_guion, daemon=True).start()

    def _opencode_execute_guion(self):
        print(f"DEBUG: _opencode_execute_guion starting, WID_B = {self.wid_b}")
        from kr_studio.core.master_director import MasterDirector, DirectorMode

        json_str = self._opencode_editor.get("1.0", "end-1c").strip()
        print(f"DEBUG: JSON length = {len(json_str)}")
        try:
            guion = json.loads(json_str)
            print(f"DEBUG: Loaded {len(guion)} scenes")
        except json.JSONDecodeError as e:
            print(f"DEBUG: JSON error: {e}")
            self.after(
                0,
                self._opencode_append_chat,
                "Sistema",
                f"⚠ Error al leer el JSON: {e}",
            )
            return

        director = MasterDirector(
            guion=guion,
            mode=DirectorMode.SOLO_TERM,
            workspace_dir=self.workspace_dir,
            typing_speed=self.typing_speed_pct,
            wid_a=None,
            wid_b=self.wid_b,
            project_name="opencode_terminal",
            progress_callback=self._opencode_update_progress,
        )
        self._active_director = director

        self.after(
            0,
            self._opencode_append_chat,
            "Sistema",
            f"🎬 Ejecutando {len(guion)} escenas...",
        )

        threading.Thread(
            target=self._opencode_director_thread, args=(director,), daemon=True
        ).start()

    def _opencode_director_thread(self, director):
        """Hilo que ejecuta el director y luego limpia la UI."""
        director.run()  # Esto es bloqueante y se ejecuta en el hilo

        # Una vez terminado, agenda la finalización en el hilo principal de la UI
        self.after(0, self._opencode_finalize_execution)

    def _opencode_update_progress(self, current: int, total: int):
        """Actualiza la etiqueta de progreso (llamado desde el hilo del director)."""
        self.after(
            0,
            lambda: self._opencode_iteration_status_label.configure(
                text=f"🎬 Escena {current}/{total}..."
            ),
        )

    def _opencode_finalize_execution(self):
        """Limpia y resetea la UI después de que el guion termina."""
        self._opencode_append_chat("Sistema", "✅ Guion completado.")
        self._opencode_iteration_status_label.configure(
            text="Listo", text_color=COLORS["accent_green"]
        )
        self._opencode_start_btn.configure(state="normal")
        self._opencode_stop_btn.configure(state="disabled")
        self._opencode_export_btn.configure(state="normal")
        self._active_director = None

    def _opencode_iteration_cycle(self):
        """One cycle of the Opencode iterative process."""
        if not self._opencode_is_running:
            return

        # Get current JSON from the editor
        json_str = self._opencode_editor.get("1.0", "end-1c").strip()
        if not json_str:
            self._opencode_append_chat(
                "Sistema", "⚠ Editor vacío durante la iteración."
            )
            self._opencode_stop_iteration()
            return
        try:
            current_json = json.loads(json_str)
            if not isinstance(current_json, list):
                self._opencode_append_chat(
                    "Sistema", "⚠ El JSON no es un arreglo durante la iteración."
                )
                self._opencode_stop_iteration()
                return
        except json.JSONDecodeError as e:
            self._opencode_append_chat(
                "Sistema", f"⚠ JSON inválido durante la iteración: {e}"
            )
            self._opencode_stop_iteration()
            return

        # Simulate execution of the JSON (in a real implementation, we would run the commands and capture output)
        self._opencode_append_chat("Sistema", "🔧 Ejecutando JSON actual (simulado)...")
        # For demonstration, we'll pretend the execution was successful and produced some output.
        execution_result = {
            "success": True,
            "output": "Simulated execution: all commands completed successfully.",
            # In a real implementation, we would have detailed output per command and possibly errors.
        }

        # Use the AI to analyze the execution result and suggest the next JSON state
        self._opencode_append_chat("Sistema", "🤖 Analizando resultados con la IA...")
        # In a real implementation, we would construct a detailed prompt for the AI engine.
        # For now, we'll simulate a response that adds a concluding scene.
        # We'll create a new JSON that is the current JSON plus a concluding narration scene.
        concluding_scene = {
            "tipo": "narracion",
            "voz": "Hemos completado los pasos especificados en el JSON inicial. El proceso iterativo ha finalizado.",
        }

        # We'll also add a small delay to simulate processing time.
        # In a real implementation, we would call the AI engine and wait for the response.
        # Here, we'll just update the JSON after a short delay to simulate AI thinking.
        def update_json():
            new_json = current_json + [concluding_scene]
            self._opencode_editor.delete("1.0", "end")
            self._opencode_editor.insert(
                "end", json.dumps(new_json, indent=4, ensure_ascii=False)
            )
            self._opencode_update_line_numbers()
            self._opencode_append_chat(
                "OPENCODE AI",
                "He añadido una escena de conclusión al JSON. El proceso iterativo ha alcanzado su objetivo.",
            )
            self._opencode_iteration_status_label.configure(
                text="Iteración completada - Resultado listo para exportar",
                text_color=COLORS["accent_green"],
            )
            # Stop the iteration since we've reached a conclusion (for demonstration)
            self._opencode_stop_iteration()
            # Enable the export button so the user can export the final project
            self._opencode_export_btn.configure(state="normal")

        # Simulate AI processing delay
        self.after(2000, update_json)

        # In a real implementation, we would not stop here but continue the cycle if the project is not complete.
        # We would check if the project is complete based on the execution result and the AI's analysis.
        # For this demonstration, we stop after one cycle.

    # -------------------------------------------------------------------------
    # MÉTODOS DE LA PESTAÑA "CEREBRO DE LA IA"
    # -------------------------------------------------------------------------

    def _brain_update_memory_viewer(self, selected_compartment: str = None):
        """Actualiza el visor de memoria con los documentos del compartimento seleccionado."""
        if selected_compartment is None:
            # Si no se especifica, toma la selección actual
            if (
                hasattr(self, "brain_compartment_selector")
                and self.brain_compartment_selector
            ):
                selected_compartment = self.brain_compartment_selector.get()
            else:
                return

        if not selected_compartment or selected_compartment not in self.vector_memories:
            return

        memory = self.vector_memories[selected_compartment]
        documents = memory.get_documents_for_compartment(selected_compartment)

        self.brain_memory_viewer.delete("1.0", "end")
        if not documents:
            self.brain_memory_viewer.insert(
                "1.0", f"El compartimento '{selected_compartment}' está vacío."
            )
        else:
            content = (
                f"--- Documentos en '{selected_compartment}' ({len(documents)}) ---\n\n"
            )
            for doc in documents:
                content += f"ID: {doc['id']}\n"
                content += f"Contenido: {doc['content'][:150].strip()}...\n"
                content += "-" * 40 + "\n\n"
            self.brain_memory_viewer.insert("1.0", content)

    def _brain_load_file_to_memory(self):
        """Carga un archivo de texto en el compartimento de memoria seleccionado."""
        selected_compartment = self.brain_compartment_selector.get()
        if not selected_compartment or selected_compartment not in self.vector_memories:
            return

        filepath = filedialog.askopenfilename(
            title="Seleccionar archivo de conocimiento (.txt, .md)",
            filetypes=(
                ("Text files", "*.txt"),
                ("Markdown files", "*.md"),
                ("All files", "*.*"),
            ),
        )
        if not filepath:
            return

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            doc_id = os.path.basename(filepath)

            memory = self.vector_memories[selected_compartment]
            memory.add_document(text=content, doc_id=doc_id)

            self._brain_update_memory_viewer(selected_compartment)
            self.append_chat(
                "Cerebro de la IA",
                f"✅ Conocimiento del archivo '{doc_id}' añadido a '{selected_compartment}'.",
            )

        except Exception as e:
            self.append_chat("Cerebro de la IA", f"❌ Error al cargar el archivo: {e}")

    def _brain_batch_load_to_memory(self):
        """Carga múltiples archivos (.txt/.md) de una carpeta en el compartimento seleccionado."""
        selected_compartment = None
        if (
            hasattr(self, "brain_compartment_selector")
            and self.brain_compartment_selector
        ):
            selected_compartment = self.brain_compartment_selector.get()
        if not selected_compartment or selected_compartment not in self.vector_memories:
            return
        dirpath = filedialog.askdirectory(
            title="Seleccionar carpeta conocimiento (archivos .txt/.md)"
        )
        if not dirpath:
            return
        memory = self.vector_memories[selected_compartment]
        loaded = 0
        for root, _, files in os.walk(dirpath):
            for fname in files:
                if not fname.lower().endswith((".txt", ".md")):
                    continue
                fpath = os.path.join(root, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        content = f.read()
                    base = os.path.basename(fname)
                    doc_id = (
                        f"{os.path.splitext(base)[0]}_{abs(hash(content)) % 1000000}"
                    )
                    memory.add_document(
                        text=content, doc_id=doc_id, compartment=selected_compartment
                    )
                    loaded += 1
                except Exception as e:
                    self.append_chat(
                        "Cerebro de la IA", f"❌ Error cargando '{fpath}': {e}"
                    )
        self._brain_update_memory_viewer(selected_compartment)
        self.append_chat(
            "Cerebro de la IA",
            f"✅ Batch cargado. Archivos procesados: {loaded} en '{selected_compartment}'.",
        )

    def _brain_clear_compartment(self):
        """Limpia todos los documentos del compartimento seleccionado."""
        selected_compartment = self.brain_compartment_selector.get()
        if not selected_compartment or selected_compartment not in self.vector_memories:
            return

        user_response = tk.messagebox.askyesno(
            "Confirmar Limpieza",
            f"¿Estás seguro de que quieres borrar TODA la memoria del compartimento '{selected_compartment}'?\n\nEsta acción es irreversible.",
        )

        if user_response:
            try:
                memory = self.vector_memories[selected_compartment]
                memory.clear_all()
                self._brain_update_memory_viewer(selected_compartment)
                self.append_chat(
                    "Cerebro de la IA",
                    f"💥 Memoria del compartimento '{selected_compartment}' ha sido limpiada.",
                )
            except Exception as e:
                self.append_chat(
                    "Cerebro de la IA", f"❌ Error al limpiar la memoria: {e}"
                )

    def _brain_delete_document(self):
        """Borra un documento específico de la memoria del compartimento actual."""
        selected_compartment = None
        if hasattr(self, "brain_compartment_selector"):
            selected_compartment = self.brain_compartment_selector.get()
        doc_id = getattr(self, "brain_delete_docid", None)
        if not selected_compartment or not getattr(doc_id, "get", None):
            return
        doc_id_val = self.brain_delete_docid.get()
        if not doc_id_val:
            return

        try:
            memory = self.vector_memories.get(selected_compartment)
            if memory:
                memory.delete_document(doc_id_val, compartment=selected_compartment)
                self._brain_update_memory_viewer(selected_compartment)
                self.append_chat(
                    "Cerebro de la IA",
                    f"🗑 Documento '{doc_id_val}' eliminado de '{selected_compartment}'.",
                )
                self.brain_delete_docid.delete(0, "end")
        except Exception as e:
            self.append_chat("Cerebro de la IA", f"❌ Error al eliminar documento: {e}")

    def _brain_on_send_chat(self, event=None):
        """Maneja el envío de un mensaje en el Chat de Conocimiento."""
        user_query = self.brain_chat_entry.get()
        if not user_query:
            return

        self.brain_chat_entry.delete(0, "end")
        self._add_to_brain_chat("Tú", user_query)

        # Detectar comandos especiales del Director Maestro
        cmd = user_query.lower().strip()

        if cmd.startswith("genera post:"):
            self._director_generar_post(user_query)
            return
        elif cmd.startswith("genera articulo:"):
            self._director_generar_articulo(user_query)
            return
        elif cmd.startswith("genera curso:"):
            self._director_generar_curso(user_query)
            return
        elif cmd.startswith("genera serie:"):
            self._director_generar_serie(user_query)
            return
        elif cmd.startswith("genera video:"):
            self._director_generar_video(user_query)
            return
        elif cmd.startswith("estrategia:"):
            self._director_generar_estrategia(user_query)
            return
        elif cmd.startswith("ayuda director"):
            self._mostrar_ayuda_director()
            return

        # Modo normal: buscar en memoria
        all_context = []
        for name, memory in self.vector_memories.items():
            results = memory.search(user_query, n_results=2)
            if results:
                for res in results:
                    doc_id = res.get("id", "desconocido")
                    content = res.get("content", "")[:500]
                    all_context.append(
                        f"📄 Documento: '{doc_id}'\n"
                        f"   Compartimento: {name}\n"
                        f"   Contenido: {content}..."
                    )

        context_str = (
            "\n\n" + "=" * 50 + "\n\n".join(all_context) + "\n" + "=" * 50
            if all_context
            else "No se encontró información relevante en la memoria."
        )

        prompt = f"""Eres el asistente de conocimiento de KR-STUDIO. Tu trabajo es responder a las preguntas del usuario basándote ÚNICAMENTE en el conocimiento que tienes almacenado en tu memoria a largo plazo.

Aquí está el conocimiento relevante que he encontrado en tu memoria sobre la pregunta del usuario:

[CONOCIMIENTO RECUPERADO DE LA MEMORIA]
{context_str}
[FIN DEL CONOCIMIENTO RECUPERADO]

Pregunta del usuario: "{user_query}"

Tu tarea:
1. Lee el [CONOCIMIENTO RECUPERADO] y sintetiza una respuesta directa y clara a la pregunta del usuario.
2. Si el conocimiento recuperado no es suficiente para responder, di que no tienes información sobre ese tema específico en tu memoria. NO inventes respuestas.
3. Cita la fuente usando el nombre del documento entre comillas (ej: "Según el documento 'mi_guia_github.md'...").
4. Sé conciso y ve al grano."""

        # Actualizar el Inspector de Contexto
        self.after(0, self._brain_update_context_inspector, prompt)

        def generation_thread():
            try:
                # Usamos el AIEngine principal para el chat, pero sin pasarle memoria de proyectos (ya está en el prompt)
                response = self.ai.chat(prompt)
                self.after(0, self._add_to_brain_chat, "IA", response)
            except Exception as e:
                self.after(0, self._add_to_brain_chat, "Error", f"Error de IA: {e}")

        self._add_to_brain_chat("IA", "🧠 Pensando...")
        threading.Thread(target=generation_thread, daemon=True).start()

    def _add_to_brain_chat(self, user: str, message: str):
        """Añade un mensaje al historial del Chat de Conocimiento."""
        self.brain_chat_history.configure(state="normal")
        self.brain_chat_history.insert("end", f"[{user}]\n{message.strip()}\n\n")
        self.brain_chat_history.configure(state="disabled")
        self.brain_chat_history.see("end")

    def _brain_update_context_inspector(self, final_prompt: str):
        """Actualiza el Inspector de Contexto con el prompt final enviado a la IA."""
        self.brain_context_viewer.configure(state="normal")
        self.brain_context_viewer.delete("1.0", "end")
        self.brain_context_viewer.insert("1.0", final_prompt)
        self.brain_context_viewer.configure(state="disabled")

    def _mostrar_ayuda_director(self):
        """Muestra la ayuda de comandos del Director Maestro."""
        ayuda = """🎬 COMANDOS DEL DIRECTOR MAESTRO:

1️⃣ genera post: [tema] - Genera post optimizado para redes sociales
   Ejemplo: genera post: SQL Injection

2️⃣ genera articulo: [tema] - Genera artículo completo con SEO
   Ejemplo: genera articulo: Cómo empezar en ciberseguridad

3️⃣ genera curso: [tema] - Genera estructura de módulo para curso
   Ejemplo: genera curso: Hacking Ético desde Cero

4️⃣ genera serie: [tema] - Genera estructura de serie de episodios
   Ejemplo: genera serie: Fundamentos de Networking

5️⃣ genera video: [tema] - Genera guion completo para video
   Ejemplo: genera video: Instalación de Kali Linux

6️⃣ estrategia: [objetivo] - Genera estrategia de marketing
   Ejemplo: estrategia: Aumentar ventas de curso de seguridad

💡 También puedes hacer preguntas normales sobre el conocimiento cargado."""
        self._add_to_brain_chat("IA", ayuda)

    def _director_generar_post(self, query: str):
        """Genera un post usando el Director Maestro."""
        tema = query.replace("genera post:", "").strip()

        def generation_thread():
            try:
                if self.ai.director:
                    prompt = self.ai.director.generar_post_social(tema)
                    self._brain_update_context_inspector(prompt)
                    response = self.ai.chat(prompt)
                    self.after(
                        0,
                        self._add_to_brain_chat,
                        "IA",
                        f"📱 POST GENERADO:\n\n{response}",
                    )
                else:
                    self.after(
                        0, self._add_to_brain_chat, "IA", "❌ Director no disponible"
                    )
            except Exception as e:
                self.after(0, self._add_to_brain_chat, "Error", f"Error: {e}")

        self._add_to_brain_chat("IA", "🎬 Generando post...")
        threading.Thread(target=generation_thread, daemon=True).start()

    def _director_generar_articulo(self, query: str):
        """Genera un artículo usando el Director Maestro."""
        tema = query.replace("genera articulo:", "").strip()

        def generation_thread():
            try:
                if self.ai.director:
                    prompt = self.ai.director.generar_articulo(tema)
                    self._brain_update_context_inspector(prompt)
                    response = self.ai.chat(prompt)
                    self.after(
                        0,
                        self._add_to_brain_chat,
                        "IA",
                        f"📝 ARTÍCULO GENERADO:\n\n{response}",
                    )
                else:
                    self.after(
                        0, self._add_to_brain_chat, "IA", "❌ Director no disponible"
                    )
            except Exception as e:
                self.after(0, self._add_to_brain_chat, "Error", f"Error: {e}")

        self._add_to_brain_chat("IA", "🎬 Generando artículo...")
        threading.Thread(target=generation_thread, daemon=True).start()

    def _director_generar_curso(self, query: str):
        """Genera estructura de curso usando el Director Maestro."""
        tema = query.replace("genera curso:", "").strip()

        def generation_thread():
            try:
                if self.ai.director:
                    prompt = self.ai.director.generar_modulo_curso(tema)
                    self._brain_update_context_inspector(prompt)
                    response = self.ai.chat(prompt)
                    self.after(
                        0,
                        self._add_to_brain_chat,
                        "IA",
                        f"🎓 MÓDULO DE CURSO GENERADO:\n\n{response}",
                    )
                else:
                    self.after(
                        0, self._add_to_brain_chat, "IA", "❌ Director no disponible"
                    )
            except Exception as e:
                self.after(0, self._add_to_brain_chat, "Error", f"Error: {e}")

        self._add_to_brain_chat("IA", "🎬 Generando módulo de curso...")
        threading.Thread(target=generation_thread, daemon=True).start()

    def _director_generar_serie(self, query: str):
        """Genera estructura de serie usando el Director Maestro."""
        tema = query.replace("genera serie:", "").strip()

        def generation_thread():
            try:
                if self.ai.director:
                    prompt = self.ai.director.generar_serie(tema)
                    self._brain_update_context_inspector(prompt)
                    response = self.ai.chat(prompt)
                    self.after(
                        0,
                        self._add_to_brain_chat,
                        "IA",
                        f"📺 SERIE GENERADA:\n\n{response}",
                    )
                else:
                    self.after(
                        0, self._add_to_brain_chat, "IA", "❌ Director no disponible"
                    )
            except Exception as e:
                self.after(0, self._add_to_brain_chat, "Error", f"Error: {e}")

        self._add_to_brain_chat("IA", "🎬 Generando serie...")
        threading.Thread(target=generation_thread, daemon=True).start()

    def _director_generar_video(self, query: str):
        """Genera guion de video usando el Director Maestro."""
        tema = query.replace("genera video:", "").strip()

        def generation_thread():
            try:
                if self.ai.director:
                    prompt = self.ai.director.generar_guion_video(tema)
                    self._brain_update_context_inspector(prompt)
                    response = self.ai.chat(prompt)
                    self.after(
                        0,
                        self._add_to_brain_chat,
                        "IA",
                        f"🎬 GUION DE VIDEO GENERADO:\n\n{response}",
                    )
                else:
                    self.after(
                        0, self._add_to_brain_chat, "IA", "❌ Director no disponible"
                    )
            except Exception as e:
                self.after(0, self._add_to_brain_chat, "Error", f"Error: {e}")

        self._add_to_brain_chat("IA", "🎬 Generando guion de video...")
        threading.Thread(target=generation_thread, daemon=True).start()

    def _director_generar_estrategia(self, query: str):
        """Genera estrategia de marketing usando el Director Maestro."""
        objetivo = query.replace("estrategia:", "").strip()

        def generation_thread():
            try:
                if self.ai.director:
                    prompt = self.ai.director.generar_estrategia_marketing(objetivo)
                    self._brain_update_context_inspector(prompt)
                    response = self.ai.chat(prompt)
                    self.after(
                        0,
                        self._add_to_brain_chat,
                        "IA",
                        f"📊 ESTRATEGIA GENERADA:\n\n{response}",
                    )
                else:
                    self.after(
                        0, self._add_to_brain_chat, "IA", "❌ Director no disponible"
                    )
            except Exception as e:
                self.after(0, self._add_to_brain_chat, "Error", f"Error: {e}")

        self._add_to_brain_chat("IA", "🎬 Generando estrategia de marketing...")
        threading.Thread(target=generation_thread, daemon=True).start()

    # -------------------------------------------------------------------------
