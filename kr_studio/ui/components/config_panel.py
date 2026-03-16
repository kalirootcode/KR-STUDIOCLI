"""
config_panel.py - Componente de UI para el Panel de Configuración de KR-Studio
"""
import customtkinter as ctk
from typing import TYPE_CHECKING

from kr_studio.ui.theme import COLORS
from kr_studio.core.master_director import DirectorMode
from kr_studio.core.video_templates import get_template_list as get_content_types

if TYPE_CHECKING:
    from kr_studio.ui.main_window import MainWindow


class ConfigPanel(ctk.CTkScrollableFrame):
    """
    Panel derecho de la UI que contiene todos los controles de configuración,
    como los botones de acción, sliders, y selectores.
    """
    def __init__(self, master: 'MainWindow', **kwargs):
        super().__init__(master, fg_color=COLORS["bg_panel"], corner_radius=12,
                         border_width=1, border_color=COLORS["border"], **kwargs)
        
        self.main_window = master
        self._build_widgets()

    def _build_widgets(self):
        """Construye todos los widgets dentro de este panel."""
        # Header
        header = ctk.CTkFrame(self, fg_color=COLORS["header_bg"], height=42, corner_radius=0)
        header.pack(fill="x", pady=(0, 6))
        header.pack_propagate(False)
        ctk.CTkLabel(header, text="⚙️", font=("Arial", 18)).pack(side="left", padx=(12, 4))
        ctk.CTkLabel(header, text="CONFIGURACIÓN",
                     font=("JetBrains Mono", 13, "bold"),
                     text_color=COLORS["accent_magenta"]).pack(side="left")

        # Botón OBS
        self.main_window.obs_btn = ctk.CTkButton(self, text="📺 Conectar OBS",
                                                 command=self.main_window.connect_obs,
                                                 font=("JetBrains Mono", 10, "bold"),
                                                 fg_color="#6c3483", text_color="#ffffff",
                                                 hover_color="#8e44ad", height=30)
        self.main_window.obs_btn.pack(fill="x", padx=4, pady=(0, 6))

        # Toolbar de proyectos
        toolbar = ctk.CTkFrame(self, fg_color=COLORS["header_bg"], height=34)
        toolbar.pack(fill="x", pady=4, padx=4)
        ctk.CTkButton(toolbar, text="💾 Guardar", command=self.main_window.save_project,
                      font=("JetBrains Mono", 10, "bold"), fg_color="#1a1b2e", hover_color="#252640",
                      border_width=1, border_color=COLORS["border"]).pack(side="left", padx=(6, 2), fill="x", expand=True)
        ctk.CTkButton(toolbar, text="📂 Cargar", command=self.main_window.load_project,
                      font=("JetBrains Mono", 10, "bold"), fg_color="#1a1b2e", hover_color="#252640",
                      border_width=1, border_color=COLORS["border"]).pack(side="left", padx=2, fill="x", expand=True)
        self.main_window.project_name_label = ctk.CTkLabel(toolbar, text="Sin título",
                                                           font=("JetBrains Mono", 9),
                                                           text_color=COLORS["text_dim"])
        self.main_window.project_name_label.pack(side="right", padx=6)

        # Controles
        controls = ctk.CTkFrame(self, fg_color="transparent")
        controls.pack(fill="both", expand=True, padx=4, pady=4)

        # Target IP selector
        ctk.CTkLabel(controls, text="🎯 IP/Target:", font=("JetBrains Mono", 10, "bold"), text_color=COLORS["text_dim"]).pack(anchor="w", padx=4, pady=(2, 0))
        self.main_window.target_combo = ctk.CTkComboBox(
            controls, width=190, height=28,
            values=["scanme.nmap.org", "testphp.vulnweb.com", "httpbin.org", "badssl.com", "rest.vulnweb.com", "IP Personalizada"],
            font=("JetBrains Mono", 11), fg_color=COLORS["bg_dark"], border_color=COLORS["border"], dropdown_fg_color=COLORS["bg_dark"])
        self.main_window.target_combo.set("scanme.nmap.org")
        self.main_window.target_combo.pack(fill="x", padx=4, pady=(2, 6))

        # Sliders (Velocidad y Duración)
        self._build_sliders(controls)

        # Selector de tipo de contenido
        self._build_content_selector(controls)

        # Botones de acción
        self._build_action_buttons(controls)

    def _build_sliders(self, parent):
        """Construye los sliders de velocidad y duración."""
        # Velocidad
        speed_row = ctk.CTkFrame(parent, fg_color="transparent")
        speed_row.pack(fill="x", padx=4, pady=(6, 2))
        ctk.CTkLabel(speed_row, text="⌨ Velocidad:", font=("JetBrains Mono", 10, "bold"), text_color=COLORS["text_dim"]).pack(side="left")
        slider = ctk.CTkSlider(speed_row, from_=50, to=200, number_of_steps=15, command=self.main_window.on_speed_change,
                               width=140, fg_color=COLORS["border"], progress_color=COLORS["accent_cyan"], button_color=COLORS["accent_cyan"])
        slider.set(80)
        slider.pack(side="left", padx=6)
        self.main_window.speed_label = ctk.CTkLabel(speed_row, text="80%", font=("JetBrains Mono", 10, "bold"), text_color=COLORS["accent_cyan"])
        self.main_window.speed_label.pack(side="left")

        # Duración
        dur_row = ctk.CTkFrame(parent, fg_color="transparent")
        dur_row.pack(fill="x", padx=4, pady=(6, 2))
        ctk.CTkLabel(dur_row, text="🎬 Duración:", font=("JetBrains Mono", 10, "bold"), text_color=COLORS["text_dim"]).pack(side="left")
        dur_slider = ctk.CTkSlider(dur_row, from_=1, to=30, number_of_steps=29, command=self.main_window.on_duration_change,
                                     width=140, fg_color=COLORS["border"], progress_color="#FF8F00", button_color="#FF8F00")
        dur_slider.set(5)
        dur_slider.pack(side="left", padx=6)
        self.main_window.duration_label = ctk.CTkLabel(dur_row, text="5 min", font=("JetBrains Mono", 10, "bold"), text_color="#FF8F00")
        self.main_window.duration_label.pack(side="left")

    def _build_content_selector(self, parent):
        """Construye el selector de memoria de contenido."""
        content_row = ctk.CTkFrame(parent, fg_color="transparent")
        content_row.pack(fill="x", padx=4, pady=(6, 2))
        ctk.CTkLabel(content_row, text="🧠 Memoria:", font=("JetBrains Mono", 10, "bold"), text_color=COLORS["text_dim"]).pack(side="left")
        content_types = ["Por defecto"] + get_content_types()
        self.main_window.content_combo = ctk.CTkOptionMenu(content_row, values=content_types,
                                                           font=("JetBrains Mono", 11),
                                                           fg_color=COLORS["border"], button_color=COLORS["accent_yellow"],
                                                           button_hover_color="#e6b800", width=140)
        self.main_window.content_combo.set("Por defecto")
        self.main_window.content_combo.pack(side="left", padx=6)

    def _build_action_buttons(self, parent):
        """Construye los botones de acción principales."""
        handler = self.main_window.action_handler
        btn_row = ctk.CTkFrame(parent, fg_color="transparent")
        btn_row.pack(fill="x", padx=4, pady=(15, 3))

        ctk.CTkButton(btn_row, text="🔊 TTS", command=self.main_window.generate_audios,
                      font=("JetBrains Mono", 11, "bold"), fg_color="#1a1b2e", hover_color="#252640",
                      border_width=1, border_color=COLORS["accent_cyan"], height=34).pack(fill="x", pady=(0, 6))

        ctk.CTkButton(btn_row, text="🎬 Lanzar", command=self.main_window.launch_konsole,
                      fg_color=COLORS["accent_green"], hover_color="#00A23D", text_color="#000000",
                      font=("JetBrains Mono", 11, "bold"), height=34).pack(fill="x", pady=2)

        ctk.CTkButton(btn_row, text="🚀 DUAL AI", command=lambda: handler.launch_director(DirectorMode.DUAL_AI),
                      fg_color="#7B1FA2", hover_color="#6A1B9A", text_color="#ffffff",
                      font=("JetBrains Mono", 11, "bold"), height=34).pack(fill="x", pady=2)

        ctk.CTkButton(btn_row, text="🔴 Grabar", command=self.main_window.launch_and_record,
                      fg_color="#D32F2F", hover_color="#B71C1C", text_color="#ffffff",
                      font=("JetBrains Mono", 11, "bold"), height=34).pack(fill="x", pady=2)

        self.main_window.btn_stop = ctk.CTkButton(btn_row, text="⏹ Detener", command=handler.stop_director,
                                                  fg_color="#424242", hover_color="#616161", text_color="#ffffff",
                                                  font=("JetBrains Mono", 11, "bold"), height=34, state="disabled")
        self.main_window.btn_stop.pack(fill="x", pady=(2, 10))
        
        ctk.CTkButton(parent, text="⚡ SOLO TERM", command=lambda: handler.launch_director(DirectorMode.SOLO_TERM),
                      fg_color="#E65100", hover_color="#BF360C", text_color="#ffffff",
                      font=("JetBrains Mono", 11, "bold"), height=34).pack(fill="x", padx=4, pady=(0, 4))
