"""
configuration_panel.py - Panel de Configuración Centralizado
Contiene todas las opciones de configuración de KR-STUDIO en una sola ubicación.
"""

import customtkinter as ctk  # type: ignore
import json
import os
import typing
from typing import cast  # type: ignore

from kr_studio.core.video_templates import (
    get_template_list,
    get_presenter_list,
    get_audience_list,
)  # type: ignore
from kr_studio.ui.theme import COLORS, get_module_color  # type: ignore


class ConfigurationPanel(ctk.CTkFrame):
    """Panel centralizado para todas las configuraciones de KR-STUDIO."""

    def __init__(self, master, app_instance: typing.Any):
        super().__init__(
            master,
            fg_color=COLORS["bg_panel"],
            corner_radius=12,
            border_width=1,
            border_color=COLORS["border"],
        )
        self.app = app_instance
        self._setup_variables()
        self._build_ui()
        self._load_saved_configuration()

    def _setup_variables(self):
        """Inicializa todas las variables de configuración."""
        # Configuración de video
        self._video_type_var = ctk.StringVar(value="Tutorial Profundo")
        self._presenter_style_var = ctk.StringVar(value="Experto Técnico")
        self._audience_var = ctk.StringVar(value="Intermedio (1-3 años)")

        # Parámetros de ejecución
        self.typing_speed_pct = 80
        self.video_duration_min = 5
        self.use_wrapper_var = ctk.BooleanVar(value=False)

        # Selección de objetivo
        self.target_combo_var = ctk.StringVar(value="scanme.nmap.org")

        # Formato de video
        self.format_combo_var = ctk.StringVar(value="9:16 (Vertical)")

        # Contenido de tercero
        self.third_party_content_var = ctk.BooleanVar(value=False)

        # Notas adicionales
        self._extra_notes = ""

    def _build_ui(self):
        """Construye la interfaz del panel de configuración."""
        # Grid layout: 2 columnas
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=0)  # Header
        self.grid_rowconfigure(1, weight=1)  # Contenido scrollable
        self.grid_rowconfigure(2, weight=0)  # Botones de acción

        # Header
        self._build_header()

        # Contenido principal (scrollable)
        self._build_main_content()

        # Botones de acción
        self._build_action_buttons()

    def _build_header(self):
        """Construye el header del panel."""
        header_frame = ctk.CTkFrame(
            self, fg_color=COLORS["header_bg"], height=50, corner_radius=0
        )
        header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=0, pady=0)
        header_frame.grid_propagate(False)

        icon_label = ctk.CTkLabel(
            header_frame, text="⚙️", font=("Arial", 20), text_color=COLORS["accent_cyan"]
        )
        icon_label.grid(row=0, column=0, padx=(15, 8), pady=10)

        title_label = ctk.CTkLabel(
            header_frame,
            text="CONFIGURACIÓN CENTRALIZADA",
            font=("JetBrains Mono", 16, "bold"),
            text_color=COLORS["accent_cyan"],
        )
        title_label.grid(row=0, column=1, padx=8, pady=10)

        # Botón de restablecer
        reset_btn = ctk.CTkButton(
            header_frame,
            text="🔄 Restablecer",
            width=100,
            height=28,
            font=("JetBrains Mono", 10),
            fg_color="#1a1b2e",
            hover_color="#252640",
            command=self._reset_to_defaults,
        )
        reset_btn.grid(row=0, column=2, padx=(8, 15), pady=10)

    def _build_main_content(self):
        """Construye el contenido principal scrollable."""
        # Frame scrollable
        self.scrollable_frame = ctk.CTkScrollableFrame(
            self, fg_color="transparent", corner_radius=0
        )
        self.scrollable_frame.grid(
            row=1, column=0, columnspan=2, sticky="nsew", padx=10, pady=(0, 10)
        )
        self.scrollable_frame.grid_columnconfigure(0, weight=1)
        self.scrollable_frame.grid_columnconfigure(1, weight=1)

        # Sección: Configuración de Video
        self._build_video_config_section()

        # Sección: Parámetros de Ejecución
        self._build_execution_params_section()

        # Sección: Objetivo y Target
        self._build_target_section()

        # Sección: Formato y Opciones
        self._build_format_options_section()

        # Sección: Notas y Contenido
        self._build_notes_content_section()

    def _build_video_config_section(self):
        """Construye la sección de configuración de video."""
        # Header de sección
        section_header = ctk.CTkFrame(
            self.scrollable_frame, fg_color="#1a1b2e", height=28, corner_radius=0
        )
        section_header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        section_header.grid_propagate(False)

        ctk.CTkLabel(
            section_header,
            text="🎬 CONFIGURACIÓN DE VIDEO",
            font=("JetBrains Mono", 11, "bold"),
            text_color=COLORS["accent_cyan"],
        ).grid(row=0, column=0, padx=10, pady=4, sticky="w")

        row = 1

        # Tipo de video
        ctk.CTkLabel(
            self.scrollable_frame,
            text="Tipo de Video:",
            font=("JetBrains Mono", 10, "bold"),
            text_color=COLORS["text_dim"],
        ).grid(row=row, column=0, sticky="e", padx=(10, 5), pady=5)

        templates = get_template_list()
        template_labels = [f"{t['icono']} {t['nombre']}" for t in templates]
        self.video_type_menu = ctk.CTkOptionMenu(
            self.scrollable_frame,
            variable=self._video_type_var,
            values=template_labels,
            width=200,
            font=("JetBrains Mono", 10),
            fg_color="#1a1b2e",
            button_color=COLORS["accent_cyan"],
        )
        self.video_type_menu.grid(row=row, column=1, sticky="w", padx=(5, 10), pady=5)
        row += 1

        # Estilo de presentador
        ctk.CTkLabel(
            self.scrollable_frame,
            text="Estilo Presentador:",
            font=("JetBrains Mono", 10, "bold"),
            text_color=COLORS["text_dim"],
        ).grid(row=row, column=0, sticky="e", padx=(10, 5), pady=5)

        presenters = get_presenter_list()
        presenter_labels = [p["nombre"] for p in presenters]
        self.presenter_style_menu = ctk.CTkOptionMenu(
            self.scrollable_frame,
            variable=self._presenter_style_var,
            values=presenter_labels,
            width=200,
            font=("JetBrains Mono", 10),
            fg_color="#1a1b2e",
            button_color="#FF8F00",
        )
        self.presenter_style_menu.grid(
            row=row, column=1, sticky="w", padx=(5, 10), pady=5
        )
        row += 1

        # Nivel de audiencia
        ctk.CTkLabel(
            self.scrollable_frame,
            text="Nivel de Audiencia:",
            font=("JetBrains Mono", 10, "bold"),
            text_color=COLORS["text_dim"],
        ).grid(row=row, column=0, sticky="e", padx=(10, 5), pady=5)

        audiences = get_audience_list()
        audience_labels = [a["nombre"] for a in audiences]
        self.audience_menu = ctk.CTkOptionMenu(
            self.scrollable_frame,
            variable=self._audience_var,
            values=audience_labels,
            width=200,
            font=("JetBrains Mono", 10),
            fg_color="#1a1b2e",
            button_color="#ff3333",
        )
        self.audience_menu.grid(row=row, column=1, sticky="w", padx=(5, 10), pady=5)
        row += 2  # Espacio extra

    def _build_execution_params_section(self):
        """Construye la sección de parámetros de ejecución."""
        # Header de sección
        section_header = ctk.CTkFrame(
            self.scrollable_frame, fg_color="#1a1b2e", height=28, corner_radius=0
        )
        section_header.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 10))
        section_header.grid_propagate(False)

        ctk.CTkLabel(
            section_header,
            text="⚙️ PARÁMETROS DE EJECUCIÓN",
            font=("JetBrains Mono", 11, "bold"),
            text_color=COLORS["accent_cyan"],
        ).grid(row=0, column=0, padx=10, pady=4, sticky="w")

        row = 3

        # Velocidad de tipeo
        ctk.CTkLabel(
            self.scrollable_frame,
            text="Velocidad de Tipeo:",
            font=("JetBrains Mono", 10, "bold"),
            text_color=COLORS["text_dim"],
        ).grid(row=row, column=0, sticky="e", padx=(10, 5), pady=5)

        speed_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
        speed_frame.grid(row=row, column=1, sticky="w", padx=(5, 10), pady=5)

        self.speed_slider = ctk.CTkSlider(
            speed_frame,
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
        self.speed_slider.pack(side="left", padx=(0, 5))

        self.speed_label = ctk.CTkLabel(
            speed_frame,
            text="80%",
            font=("JetBrains Mono", 10, "bold"),
            text_color=COLORS["accent_cyan"],
        )
        self.speed_label.pack(side="left")
        row += 1

        # Duración del video
        ctk.CTkLabel(
            self.scrollable_frame,
            text="Duración Video:",
            font=("JetBrains Mono", 10, "bold"),
            text_color=COLORS["text_dim"],
        ).grid(row=row, column=0, sticky="e", padx=(10, 5), pady=5)

        dur_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
        dur_frame.grid(row=row, column=1, sticky="w", padx=(5, 10), pady=5)

        self.duration_slider = ctk.CTkSlider(
            dur_frame,
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
        self.duration_slider.pack(side="left", padx=(0, 5))

        self.duration_label = ctk.CTkLabel(
            dur_frame,
            text="5 min",
            font=("JetBrains Mono", 10, "bold"),
            text_color="#FF8F00",
        )
        self.duration_label.pack(side="left")
        row += 1

        # Wrapper KR-CLI
        self.wrapper_check = ctk.CTkCheckBox(
            self.scrollable_frame,
            text="🔲 KR-CLI Wrapper (Terminal B)",
            variable=self.use_wrapper_var,
            font=("JetBrains Mono", 10),
            text_color=COLORS["text_dim"],
            fg_color=COLORS["accent_red"],
            hover_color="#9c27b0",
            checkbox_width=18,
            checkbox_height=18,
        )
        self.wrapper_check.grid(
            row=row, column=0, columnspan=2, sticky="w", padx=10, pady=(10, 5)
        )
        row += 1

        # Contenido de Tercero
        self.third_party_check = ctk.CTkCheckBox(
            self.scrollable_frame,
            text="🎬 Contenido de Tercero",
            variable=self.third_party_content_var,
            font=("JetBrains Mono", 10),
            text_color=COLORS["text_dim"],
            fg_color=COLORS["accent_yellow"],
            hover_color="#e6b800",
            checkbox_width=18,
            checkbox_height=18,
        )
        self.third_party_check.grid(
            row=row, column=0, columnspan=2, sticky="w", padx=10, pady=5
        )
        row += 2  # Espacio extra

    def _build_target_section(self):
        """Construye la sección de objetivo y target."""
        # Header de sección
        section_header = ctk.CTkFrame(
            self.scrollable_frame, fg_color="#1a1b2e", height=28, corner_radius=0
        )
        section_header.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(10, 10))
        section_header.grid_propagate(False)

        ctk.CTkLabel(
            section_header,
            text="🎯 OBJETIVO Y TARGET",
            font=("JetBrains Mono", 11, "bold"),
            text_color=COLORS["accent_cyan"],
        ).grid(row=0, column=0, padx=10, pady=4, sticky="w")

        row = 6

        # Selector de IP/Target
        ctk.CTkLabel(
            self.scrollable_frame,
            text="IP/Target:",
            font=("JetBrains Mono", 10, "bold"),
            text_color=COLORS["text_dim"],
        ).grid(row=row, column=0, sticky="e", padx=(10, 5), pady=5)

        self.target_combo = ctk.CTkComboBox(
            self.scrollable_frame,
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
        self.target_combo.grid(row=row, column=1, sticky="w", padx=(5, 10), pady=5)
        row += 2  # Espacio extra

    def _build_format_options_section(self):
        """Construye la sección de formato y opciones."""
        # Header de sección
        section_header = ctk.CTkFrame(
            self.scrollable_frame, fg_color="#1a1b2e", height=28, corner_radius=0
        )
        section_header.grid(row=8, column=0, columnspan=2, sticky="ew", pady=(10, 10))
        section_header.grid_propagate(False)

        ctk.CTkLabel(
            section_header,
            text="📐 FORMATO Y OPCIONES",
            font=("JetBrains Mono", 11, "bold"),
            text_color=COLORS["accent_cyan"],
        ).grid(row=0, column=0, padx=10, pady=4, sticky="w")

        row = 9

        # Formato de video
        ctk.CTkLabel(
            self.scrollable_frame,
            text="Formato de Video:",
            font=("JetBrains Mono", 10, "bold"),
            text_color=COLORS["text_dim"],
        ).grid(row=row, column=0, sticky="e", padx=(10, 5), pady=5)

        self.format_combo = ctk.CTkOptionMenu(
            self.scrollable_frame,
            variable=self.format_combo_var,
            values=["9:16 (Vertical)", "16:9 (Horizontal)"],
            width=200,
            font=("JetBrains Mono", 11),
            fg_color=COLORS["border"],
            button_color=COLORS["accent_red"],
            button_hover_color="#9c27b0",
        )
        self.format_combo.grid(row=row, column=1, sticky="w", padx=(5, 10), pady=5)
        row += 2  # Espacio extra

    def _build_notes_content_section(self):
        """Construye la sección de notas y contenido."""
        # Header de sección
        section_header = ctk.CTkFrame(
            self.scrollable_frame, fg_color="#1a1b2e", height=28, corner_radius=0
        )
        section_header.grid(row=11, column=0, columnspan=2, sticky="ew", pady=(10, 10))
        section_header.grid_propagate(False)

        ctk.CTkLabel(
            section_header,
            text="📝 NOTAS Y CONTENIDO",
            font=("JetBrains Mono", 11, "bold"),
            text_color=COLORS["accent_cyan"],
        ).grid(row=0, column=0, padx=10, pady=4, sticky="w")

        row = 12

        # Tipo de contenido
        ctk.CTkLabel(
            self.scrollable_frame,
            text="Tipo de Contenido:",
            font=("JetBrains Mono", 10, "bold"),
            text_color=COLORS["text_dim"],
        ).grid(row=row, column=0, sticky="e", padx=(10, 5), pady=5)

        content_types = ["Por defecto"] + [t["key"] for t in get_template_list()]
        self.content_combo = ctk.CTkOptionMenu(
            self.scrollable_frame,
            values=content_types,
            width=200,
            font=("JetBrains Mono", 11),
            fg_color=COLORS["border"],
            button_color=COLORS["accent_yellow"],
            button_hover_color="#e6b800",
        )
        self.content_combo.set("Por defecto")
        self.content_combo.grid(row=row, column=1, sticky="w", padx=(5, 10), pady=5)
        row += 1

        # Notas adicionales
        ctk.CTkLabel(
            self.scrollable_frame,
            text="Notas para la IA:",
            font=("JetBrains Mono", 9),
            text_color="#555577",
        ).grid(row=row, column=0, sticky="nw", padx=(10, 5), pady=(10, 5))

        self._extra_notes_text = ctk.CTkTextbox(
            self.scrollable_frame,
            height=60,
            font=("JetBrains Mono", 10),
            fg_color="#080810",
            border_color=COLORS["border"],
            border_width=1,
        )
        self._extra_notes_text.grid(
            row=row, column=1, sticky="ew", padx=(5, 10), pady=(10, 5)
        )
        self._extra_notes_text.bind("<FocusOut>", lambda e: self._save_extra_notes())
        row += 2

    def _build_action_buttons(self):
        """Construye los botones de acción."""
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)

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
        save_config_btn.grid(row=0, column=0, padx=(0, 5), pady=0, sticky="ew")

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
        apply_btn.grid(row=0, column=1, padx=(5, 0), pady=0, sticky="ew")

    def _on_speed_change(self, value):
        """Maneja cambios en el slider de velocidad."""
        self.typing_speed_pct = int(float(value))
        self.speed_label.configure(text=f"{self.typing_speed_pct}%")
        # Notificar a la app principal si tiene el método
        if hasattr(self.app, "_on_configuration_changed"):
            self.app._on_configuration_changed()

    def _on_duration_change(self, value):
        """Maneja cambios en el slider de duración."""
        self.video_duration_min = int(float(value))
        self.duration_label.configure(text=f"{self.video_duration_min} min")
        # Notificar a la app principal si tiene el método
        if hasattr(self.app, "_on_configuration_changed"):
            self.app._on_configuration_changed()

    def _save_extra_notes(self):
        """Guarda las notas adicionales."""
        self._extra_notes = self._extra_notes_text.get("1.0", "end-1c")
        # Notificar a la app principal si tiene el método
        if hasattr(self.app, "_on_configuration_changed"):
            self.app._on_configuration_changed()

    def _reset_to_defaults(self):
        """Restablece todos los valores a sus valores predeterminados."""
        # Configuración de video
        templates = get_template_list()
        template_labels = [f"{t['icono']} {t['nombre']}" for t in templates]
        self._video_type_var.set(
            template_labels[1] if len(template_labels) > 1 else template_labels[0]
        )

        presenters = get_presenter_list()
        presenter_labels = [p["nombre"] for p in presenters]
        self._presenter_style_var.set(presenter_labels[0] if presenter_labels else "")

        audiences = get_audience_list()
        audience_labels = [a["nombre"] for a in audiences]
        self._audience_var.set(
            audience_labels[1] if len(audience_labels) > 1 else audience_labels[0]
        )

        # Parámetros de ejecución
        self.typing_speed_pct = 80
        self.speed_slider.set(80)
        self.speed_label.configure(text="80%")

        self.video_duration_min = 5
        self.duration_slider.set(5)
        self.duration_label.configure(text="5 min")

        self.use_wrapper_var.set(False)
        self.third_party_content_var.set(False)

        # Selección de objetivo
        self.target_combo_var.set("scanme.nmap.org")

        # Formato de video
        self.format_combo_var.set("9:16 (Vertical)")

        # Tipo de contenido
        content_types = ["Por defecto"] + [t["key"] for t in get_template_list()]
        self.content_combo.set("Por defecto")

        # Notas adicionales
        self._extra_notes_text.delete("1.0", "end")
        self._extra_notes = ""

        # Notificar cambios
        if hasattr(self.app, "_on_configuration_changed"):
            self.app._on_configuration_changed()

    def _save_configuration(self):
        """Guarda la configuración actual en un archivo."""
        config_data = {
            # Configuración de video
            "video_type": self._video_type_var.get(),
            "presenter_style": self._presenter_style_var.get(),
            "audience": self._audience_var.get(),
            # Parámetros de ejecución
            "typing_speed_pct": self.typing_speed_pct,
            "video_duration_min": self.video_duration_min,
            "use_wrapper": self.use_wrapper_var.get(),
            "third_party_content": self.third_party_content_var.get(),
            # Selección de objetivo
            "target": self.target_combo_var.get(),
            # Formato de video
            "format": self.format_combo_var.get(),
            # Tipo de contenido
            "content_type": self.content_combo.get(),
            # Notas adicionales
            "extra_notes": self._extra_notes,
        }

        try:
            config_path = os.path.join(self.app.workspace_dir, "configuration.json")
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)

            # Mostrar feedback visual
            self._show_temporary_message("✅ Configuración guardada", "success")
        except Exception as e:
            self._show_temporary_message(f"❌ Error al guardar: {str(e)}", "error")

    def _load_saved_configuration(self):
        """Carga la configuración guardada desde archivo."""
        try:
            config_path = os.path.join(self.app.workspace_dir, "configuration.json")
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    config_data = json.load(f)

                # Aplicar valores cargados
                if "video_type" in config_data:
                    self._video_type_var.set(config_data["video_type"])
                if "presenter_style" in config_data:
                    self._presenter_style_var.set(config_data["presenter_style"])
                if "audience" in config_data:
                    self._audience_var.set(config_data["audience"])

                if "typing_speed_pct" in config_data:
                    self.typing_speed_pct = config_data["typing_speed_pct"]
                    self.speed_slider.set(self.typing_speed_pct)
                    self.speed_label.configure(text=f"{self.typing_speed_pct}%")

                if "video_duration_min" in config_data:
                    self.video_duration_min = config_data["video_duration_min"]
                    self.duration_slider.set(self.video_duration_min)
                    self.duration_label.configure(text=f"{self.video_duration_min} min")

                if "use_wrapper" in config_data:
                    self.use_wrapper_var.set(config_data["use_wrapper"])
                if "third_party_content" in config_data:
                    self.third_party_content_var.set(config_data["third_party_content"])

                if "target" in config_data:
                    self.target_combo_var.set(config_data["target"])

                if "format" in config_data:
                    self.format_combo_var.set(config_data["format"])

                if "content_type" in config_data:
                    self.content_combo.set(config_data["content_type"])

                if "extra_notes" in config_data:
                    self._extra_notes = config_data["extra_notes"]
                    self._extra_notes_text.delete("1.0", "end")
                    self._extra_notes_text.insert("1.0", self._extra_notes)

        except Exception as e:
            print(f"Advertencia: No se pudo cargar configuración guardada: {e}")
            # Continuar con valores predeterminados

    def _apply_configuration(self):
        """Aplica la configuración actual a la instancia principal de la aplicación."""
        try:
            # Notificar a la app principal
            if hasattr(self.app, "_on_configuration_changed"):
                self.app._on_configuration_changed()

            self._show_temporary_message("✅ Configuración aplicada", "success")
        except Exception as e:
            self._show_temporary_message(f"❌ Error al aplicar: {str(e)}", "error")

    def _show_temporary_message(self, message, msg_type="info"):
        """Muestra un mensaje temporal en el panel."""
        # Implementación simple - en una versión completa podría usar toast notifications
        print(f"[ConfigPanel] {message}")

    def get_current_configuration(self):
        """Retorna la configuración actual como diccionario."""
        return {
            # Configuración de video
            "video_type": self._video_type_var.get(),
            "presenter_style": self._presenter_style_var.get(),
            "audience": self._audience_var.get(),
            # Parámetros de ejecución
            "typing_speed_pct": self.typing_speed_pct,
            "video_duration_min": self.video_duration_min,
            "use_wrapper": self.use_wrapper_var.get(),
            "third_party_content": self.third_party_content_var.get(),
            # Selección de objetivo
            "target": self.target_combo_var.get(),
            # Formato de video
            "format": self.format_combo_var.get(),
            # Tipo de contenido
            "content_type": self.content_combo.get(),
            # Notas adicionales
            "extra_notes": self._extra_notes,
        }
