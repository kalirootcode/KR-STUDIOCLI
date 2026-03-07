"""
main_window.py — Interfaz Principal Profesional de KR-STUDIO
Panel dividido: Chat AI DOMINION (izquierda) + Editor JSON Pro (derecha)
Con sistema de proyectos, slider de velocidad, y UI elegante.
"""
import customtkinter as ctk
import json
import threading
import os
import re
import time
import tkinter as tk
from tkinter import filedialog
from kr_studio.core.ai_engine import AIEngine
from kr_studio.core.audio_engine import AudioEngine
from kr_studio.core.director import DirectorEngine
from kr_studio.core.dynamic_director import DynamicDirectorEngine
from kr_studio.ui.floating_control import FloatingControl


# ═══════════════════════════════════════════════
# COLORES DEL TEMA
# ═══════════════════════════════════════════════
COLORS = {
    "bg_dark": "#000000",
    "bg_panel": "#000000",
    "bg_editor": "#000000",
    "bg_chat": "#000000",
    "accent_cyan": "#00D9FF",
    "accent_green": "#00CA4E",
    "accent_magenta": "#FF2D78",
    "accent_yellow": "#FFCC00",
    "text_primary": "#e8e8e8",
    "text_dim": "#6a6a7a",
    "border": "#1a1b2e",
    "header_bg": "#0f1015",
}


class MainWindow(ctk.CTkFrame):
    def __init__(self, master_app):
        super().__init__(master_app, fg_color=COLORS["bg_dark"])
        self.master_app = master_app
        self.pack(fill="both", expand=True)

        self._base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self._env_path = os.path.join(os.path.dirname(self._base_dir), ".env")

        self.ai = AIEngine("")
        self.workspace_dir = os.path.join(self._base_dir, "workspace")
        self.projects_dir = os.path.join(self._base_dir, "projects")
        os.makedirs(self.workspace_dir, exist_ok=True)
        os.makedirs(self.projects_dir, exist_ok=True)

        self._active_director = None
        self.typing_speed_pct = 80
        self.wid_a = None
        self.wid_b = None
        self._anim_id = None
        self._floating_ctrl = None

        self.video_duration_min = 5
        self.use_wrapper_var = None  # Se crea en _build_editor_panel
        self.timestamps = {}
        self.pre_mode_var = None  # Se crea en _build_chat_panel
        self._raw_video_path = None

        # ─── LAYOUT: API Bar + Tabview ───
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_api_bar()

        # ── CTkTabview ──
        self.tabview = ctk.CTkTabview(
            self,
            fg_color=COLORS["bg_dark"],
            segmented_button_fg_color=COLORS["bg_panel"],
            segmented_button_selected_color=COLORS["accent_cyan"],
            segmented_button_selected_hover_color="#00b8d4",
            segmented_button_unselected_color=COLORS["bg_dark"],
            segmented_button_unselected_hover_color="#2a2b3e",
            text_color="#000000",
            corner_radius=8
        )
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=6, pady=(0, 6))

        self.tab1 = self.tabview.add("🎬 Guion y Director")
        self.tab2 = self.tabview.add("🎞️ Post-Producción")

        # Tab 1 layout
        self.tab1.grid_columnconfigure(0, weight=1)
        self.tab1.grid_columnconfigure(1, weight=1)
        self.tab1.grid_columnconfigure(2, weight=1)
        self.tab1.grid_rowconfigure(0, weight=1)

        self._build_chat_panel()
        self._build_editor_panel()
        self._build_config_panel()

        # Tab 2 layout
        self._build_postprod_tab()

        # ─── POSICIONAR VENTANA ───
        self.master_app.update_idletasks()
        sw = self.master_app.winfo_screenwidth()
        sh = self.master_app.winfo_screenheight()
        x = int((sw - 1300) / 2)
        y = int((sh - 800) / 2)
        self.master_app.geometry(f"1300x800+{x}+{y}")

        # Auto-cargar API Key desde .env
        saved_key = self._load_env_key()
        if saved_key:
            try:
                self.ai = AIEngine(saved_key)
                self.api_entry.insert(0, saved_key)
                self.append_chat("Sistema", "Bienvenido a KR-STUDIO 🎬\nAPI Key cargada desde .env — DOMINION listo.")
                # Ocultar barra de API al cargar después de un pequeño delay visual
                self.after(800, lambda: self._api_bar.grid_forget())
            except Exception:
                self.append_chat("Sistema", "Bienvenido a KR-STUDIO 🎬\n⚠ API Key en .env inválida. Ingresa una nueva.")
        else:
            self.append_chat("Sistema", "Bienvenido a KR-STUDIO 🎬\nIDE de Producción de Videos — DOMINION Edition\nIngresa tu API Key para comenzar.")

        # Deferimos el lanzamiento de Konsole a la interaccion del usuario.

        # Crear widget flotante
        self.after(500, self._create_floating_control)

    def _create_floating_control(self):
        """Crea el mini control flotante."""
        self._floating_ctrl = FloatingControl(self)

    # ═══════════════════════════════════════════════
    # CONSTRUCCIÓN DE PANELES
    # ═══════════════════════════════════════════════

    def _build_api_bar(self):
        """Barra superior de API Key (se oculta tras guardar)."""
        self._api_bar = ctk.CTkFrame(self, fg_color=COLORS["header_bg"], height=50, corner_radius=0)
        self._api_bar.grid(row=0, column=0, columnspan=2, sticky="ew")
        self._api_bar.grid_propagate(False)

        lbl = ctk.CTkLabel(self._api_bar, text="🔑 API KEY", font=("JetBrains Mono", 12, "bold"),
                           text_color=COLORS["accent_cyan"])
        lbl.pack(side="left", padx=(15, 8))

        self.api_entry = ctk.CTkEntry(self._api_bar, width=350, show="*",
                                       placeholder_text="Gemini API Key...",
                                       font=("JetBrains Mono", 12),
                                       fg_color=COLORS["bg_dark"],
                                       border_color=COLORS["border"])
        self.api_entry.pack(side="left", padx=5, fill="x", expand=True)

        self.api_btn = ctk.CTkButton(self._api_bar, text="Conectar", width=90,
                                      command=self.save_api_key,
                                      font=("JetBrains Mono", 12, "bold"),
                                      fg_color=COLORS["accent_cyan"],
                                      text_color="#000000",
                                      hover_color="#00b8d4")
        self.api_btn.pack(side="left", padx=(5, 15))

    def _build_chat_panel(self):
        """Panel izquierdo — Chat AI DOMINION."""
        panel = ctk.CTkFrame(self.tab1, fg_color=COLORS["bg_panel"], corner_radius=12,
                              border_width=1, border_color=COLORS["border"])
        panel.grid(row=0, column=0, sticky="nsew", padx=(8, 4), pady=8)

        # Header estilizado
        header = ctk.CTkFrame(panel, fg_color=COLORS["header_bg"], height=48, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(header, text="🧠", font=("Arial", 20)).pack(side="left", padx=(12, 4))
        ctk.CTkLabel(header, text="DOMINION AI",
                     font=("JetBrains Mono", 14, "bold"),
                     text_color=COLORS["accent_cyan"]).pack(side="left")

        # Indicador de estado
        self.status_label = ctk.CTkLabel(header, text="● EN LÍNEA",
                                          font=("JetBrains Mono", 10),
                                          text_color=COLORS["accent_green"])
        self.status_label.pack(side="right", padx=12)

        # Botón OSINT Radar
        self.btn_osint = ctk.CTkButton(header, text="🌐 Radar OSINT",
                                        command=self.osint_search,
                                        font=("JetBrains Mono", 10, "bold"),
                                        fg_color="#FF6D00", hover_color="#E65100",
                                        text_color="#000000",
                                        width=120, height=30)
        self.btn_osint.pack(side="right", padx=(0, 6))

        # ─── METADATA SECTION ───
        meta_frame = ctk.CTkFrame(panel, fg_color="transparent")
        meta_frame.pack(fill="x", padx=6, pady=4)

        # Título
        ctk.CTkLabel(meta_frame, text="Título:", font=("JetBrains Mono", 10, "bold"), text_color=COLORS["text_dim"]).grid(row=0, column=0, sticky="w", pady=2)
        self.meta_title = ctk.CTkEntry(meta_frame, font=("JetBrains Mono", 11), fg_color=COLORS["bg_dark"], border_color=COLORS["border"], height=28)
        self.meta_title.grid(row=0, column=1, sticky="ew", padx=4, pady=2)

        # Descripción
        ctk.CTkLabel(meta_frame, text="Desc:", font=("JetBrains Mono", 10, "bold"), text_color=COLORS["text_dim"]).grid(row=1, column=0, sticky="nw", pady=2)
        self.meta_desc = ctk.CTkTextbox(meta_frame, font=("JetBrains Mono", 11), fg_color=COLORS["bg_dark"], border_color=COLORS["border"], border_width=1, height=50)
        self.meta_desc.grid(row=1, column=1, sticky="ew", padx=4, pady=2)

        # Hashtags
        ctk.CTkLabel(meta_frame, text="Tags:", font=("JetBrains Mono", 10, "bold"), text_color=COLORS["text_dim"]).grid(row=2, column=0, sticky="w", pady=2)
        self.meta_tags = ctk.CTkEntry(meta_frame, font=("JetBrains Mono", 11), fg_color=COLORS["bg_dark"], border_color=COLORS["border"], height=28, text_color=COLORS["accent_cyan"])
        self.meta_tags.grid(row=2, column=1, sticky="ew", padx=4, pady=2)
        
        meta_frame.grid_columnconfigure(1, weight=1)

        # Chat display
        self.chat_display = ctk.CTkTextbox(panel, wrap="word",
                                            font=("JetBrains Mono", 12),
                                            fg_color=COLORS["bg_chat"],
                                            text_color=COLORS["text_primary"],
                                            state="disabled",
                                            border_width=0)
        self.chat_display.pack(fill="both", expand=True, padx=6, pady=(4, 4))

        # Configurar tags de colores para mensajes
        self.chat_display._textbox.tag_config("sender_system", foreground=COLORS["accent_yellow"])
        self.chat_display._textbox.tag_config("sender_user", foreground=COLORS["accent_cyan"])
        self.chat_display._textbox.tag_config("sender_ai", foreground=COLORS["accent_green"])
        self.chat_display._textbox.tag_config("sender_error", foreground=COLORS["accent_magenta"])
        self.chat_display._textbox.tag_config("sender_director", foreground="#AB47BC")
        self.chat_display._textbox.tag_config("sender_osint", foreground="#FF6D00")
        self.chat_display._textbox.tag_config("msg_body", foreground=COLORS["text_primary"])

        # Selector de Modo Pre-Generación
        mode_frame = ctk.CTkFrame(panel, fg_color="transparent")
        mode_frame.pack(fill="x", padx=6, pady=(4, 2))
        
        ctk.CTkLabel(mode_frame, text="Formato:", 
                     font=("JetBrains Mono", 10, "bold"), 
                     text_color=COLORS["text_dim"]).pack(side="left", padx=(4, 8))
        
        self.pre_mode_var = ctk.StringVar(value="DUAL AI")
        self.pre_mode_selector = ctk.CTkSegmentedButton(
            mode_frame, values=["DUAL AI", "SOLO TERM"], variable=self.pre_mode_var,
            font=("JetBrains Mono", 10, "bold"), height=24,
            fg_color=COLORS["bg_dark"], selected_color=COLORS["accent_cyan"],
            selected_hover_color="#00b8d4"
        )
        self.pre_mode_selector.pack(side="left", fill="x", expand=True, padx=(0, 4))

        # Input
        input_frame = ctk.CTkFrame(panel, fg_color="transparent")
        input_frame.pack(fill="x", padx=6, pady=(0, 6))

        self.chat_entry = ctk.CTkEntry(input_frame,
                                        placeholder_text="Pide un guion de video...",
                                        font=("JetBrains Mono", 12),
                                        fg_color=COLORS["bg_dark"],
                                        border_color=COLORS["border"])
        self.chat_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.chat_entry.bind("<Return>", lambda e: self.send_chat())

        self.chat_btn = ctk.CTkButton(input_frame, text="⚡", width=45,
                                       command=self.send_chat,
                                       font=("Arial", 18),
                                       fg_color=COLORS["accent_cyan"],
                                       text_color="#000000",
                                       hover_color="#00b8d4")
        self.chat_btn.pack(side="right")

    def _build_editor_panel(self):
        """Panel central — Editor JSON Profesional (solo editor + tabs)."""
        panel = ctk.CTkFrame(self.tab1, fg_color=COLORS["bg_panel"], corner_radius=12,
                              border_width=1, border_color=COLORS["border"])
        panel.grid(row=0, column=1, sticky="nsew", padx=(4, 4), pady=8)

        # Grid: Header(0) + Editor(1) — editor se expande
        panel.grid_rowconfigure(1, weight=1)
        panel.grid_columnconfigure(0, weight=1)

        # ── Header (row 0) ──
        header = ctk.CTkFrame(panel, fg_color=COLORS["header_bg"], height=42, corner_radius=0)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)

        ctk.CTkLabel(header, text="📝", font=("Arial", 18)).pack(side="left", padx=(12, 4))
        ctk.CTkLabel(header, text="EDITOR DE GUION",
                     font=("JetBrains Mono", 13, "bold"),
                     text_color=COLORS["accent_cyan"]).pack(side="left")

        # ── Editor DUAL con pestañas (row 1 — SE EXPANDE) ──
        editor_tabs_frame = ctk.CTkFrame(panel, fg_color="transparent")
        editor_tabs_frame.grid(row=1, column=0, sticky="nsew", padx=6, pady=(2, 6))
        editor_tabs_frame.grid_rowconfigure(1, weight=1)
        editor_tabs_frame.grid_columnconfigure(0, weight=1)

        # Tab buttons
        tab_bar = ctk.CTkFrame(editor_tabs_frame, fg_color=COLORS["header_bg"], height=30)
        tab_bar.grid(row=0, column=0, sticky="ew")
        tab_bar.grid_propagate(False)

        self._active_tab = "a"
        self.tab_btn_a = ctk.CTkButton(tab_bar, text="📝 Terminal A (Chat)",
                                        command=lambda: self._switch_editor_tab("a"),
                                        font=("JetBrains Mono", 10, "bold"),
                                        fg_color=COLORS["accent_cyan"],
                                        text_color="#000000",
                                        hover_color="#00b8d4",
                                        width=140, height=24)
        self.tab_btn_a.pack(side="left", padx=(4, 2), pady=3)

        self.tab_btn_b = ctk.CTkButton(tab_bar, text="⚡ Terminal B (Cmds)",
                                        command=lambda: self._switch_editor_tab("b"),
                                        font=("JetBrains Mono", 10, "bold"),
                                        fg_color="#1a1b2e",
                                        text_color=COLORS["text_dim"],
                                        hover_color="#252640",
                                        width=140, height=24)
        self.tab_btn_b.pack(side="left", padx=2, pady=3)

        # Editor container (switchable)
        editor_stack = ctk.CTkFrame(editor_tabs_frame, fg_color="transparent")
        editor_stack.grid(row=1, column=0, sticky="nsew")

        # ── Editor A (Terminal A / Chat) ──
        self.editor_container_a = ctk.CTkFrame(editor_stack, fg_color="transparent")
        self.editor_container_a.pack(fill="both", expand=True)

        self.line_numbers = tk.Text(self.editor_container_a, width=4,
                                     bg="#08090a", fg="#3a3a5a",
                                     font=("JetBrains Mono", 10),
                                     state="disabled",
                                     relief="flat", bd=0,
                                     selectbackground="#08090a",
                                     highlightthickness=0,
                                     padx=6, pady=4)
        self.line_numbers.pack(side="left", fill="y")

        self.editor = tk.Text(self.editor_container_a,
                               bg=COLORS["bg_editor"],
                               fg=COLORS["text_primary"],
                               font=("JetBrains Mono", 10),
                               insertbackground=COLORS["accent_cyan"],
                               selectbackground="#1a2a4a",
                               relief="flat", bd=0,
                               wrap="word",
                               highlightthickness=0,
                               padx=8, pady=4,
                               undo=True)
        self.editor.pack(side="left", fill="both", expand=True)

        scrollbar_a = ctk.CTkScrollbar(self.editor_container_a, command=self.editor.yview)
        scrollbar_a.pack(side="right", fill="y")
        self.editor.configure(yscrollcommand=self._sync_scroll)

        # ── Editor B (Terminal B / Comandos) ──
        self.editor_container_b = ctk.CTkFrame(editor_stack, fg_color="transparent")
        # Inicialmente oculto

        self.line_numbers_b = tk.Text(self.editor_container_b, width=4,
                                       bg="#08090a", fg="#3a3a5a",
                                       font=("JetBrains Mono", 10),
                                       state="disabled",
                                       relief="flat", bd=0,
                                       selectbackground="#08090a",
                                       highlightthickness=0,
                                       padx=6, pady=4)
        self.line_numbers_b.pack(side="left", fill="y")

        self.editor_b = tk.Text(self.editor_container_b,
                                 bg="#0a0d0a",
                                 fg="#a0ffa0",
                                 font=("JetBrains Mono", 10),
                                 insertbackground=COLORS["accent_green"],
                                 selectbackground="#1a3a1a",
                                 relief="flat", bd=0,
                                 wrap="word",
                                 highlightthickness=0,
                                 padx=8, pady=4,
                                 undo=True)
        self.editor_b.pack(side="left", fill="both", expand=True)

        scrollbar_b = ctk.CTkScrollbar(self.editor_container_b, command=self.editor_b.yview)
        scrollbar_b.pack(side="right", fill="y")
        self.editor_b.configure(yscrollcommand=lambda *a: None)

        # Syntax highlighting tags para ambos editores (VSCode Dark Style)
        for ed in [self.editor, self.editor_b]:
            ed.tag_config("json_key", foreground="#9CDCFE")     # Azul claro (VSCode keys)
            ed.tag_config("json_string", foreground="#CE9178")  # Naranja (VSCode strings)
            ed.tag_config("json_bracket", foreground="#FFD700") # Amarillo (brackets)
            ed.tag_config("json_keyword", foreground="#C586C0") # Magenta (keywords/booleans)
            ed.tag_config("json_colon", foreground="#D4D4D4")   # Gris (puntuación)
            ed.tag_config("json_number", foreground="#B5CEA8")  # Verde olivo (numbers)

        self.editor.bind("<KeyRelease>", lambda e: self.after(100, self._update_editor))
        self.editor.bind("<ButtonRelease-1>", lambda e: self._update_line_numbers())

    def _build_config_panel(self):
        """Panel derecho (Columna 2) — Botones, sliders y config (Scrollable)."""
        panel = ctk.CTkScrollableFrame(self.tab1, fg_color=COLORS["bg_panel"], corner_radius=12,
                                       border_width=1, border_color=COLORS["border"])
        panel.grid(row=0, column=2, sticky="nsew", padx=(4, 8), pady=8)

        # ── Header ──
        header = ctk.CTkFrame(panel, fg_color=COLORS["header_bg"], height=42, corner_radius=0)
        header.pack(fill="x", pady=(0, 6))
        header.pack_propagate(False)

        ctk.CTkLabel(header, text="⚙️", font=("Arial", 18)).pack(side="left", padx=(12, 4))
        ctk.CTkLabel(header, text="CONFIGURACIÓN",
                     font=("JetBrains Mono", 13, "bold"),
                     text_color=COLORS["accent_magenta"]).pack(side="left")

        # Botón OBS (movido desde la barra de API)
        self.obs_btn = ctk.CTkButton(panel, text="📺 Conectar OBS",
                                      command=self._connect_obs,
                                      font=("JetBrains Mono", 10, "bold"),
                                      fg_color="#6c3483",
                                      text_color="#ffffff",
                                      hover_color="#8e44ad",
                                      height=30)
        self.obs_btn.pack(fill="x", padx=4, pady=(0, 6))

        # ── Toolbar proyectos (movido del editor) ──
        toolbar = ctk.CTkFrame(panel, fg_color=COLORS["header_bg"], height=34)
        toolbar.pack(fill="x", pady=4, padx=4)

        ctk.CTkButton(toolbar, text="💾 Guardar",
                       command=self.save_project,
                       font=("JetBrains Mono", 10, "bold"),
                       fg_color="#1a1b2e", hover_color="#252640",
                       border_width=1, border_color=COLORS["border"]).pack(side="left", padx=(6, 2), fill="x", expand=True)

        ctk.CTkButton(toolbar, text="📂 Cargar",
                       command=self.load_project,
                       font=("JetBrains Mono", 10, "bold"),
                       fg_color="#1a1b2e", hover_color="#252640",
                       border_width=1, border_color=COLORS["border"]).pack(side="left", padx=2, fill="x", expand=True)

        self.project_name_label = ctk.CTkLabel(toolbar, text="Sin título",
                                                font=("JetBrains Mono", 9),
                                                text_color=COLORS["text_dim"])
        self.project_name_label.pack(side="right", padx=6)

        # Controles
        controls = ctk.CTkFrame(panel, fg_color="transparent")
        controls.pack(fill="both", expand=True, padx=4, pady=4)

        # Target IP selector
        ctk.CTkLabel(controls, text="🎯 IP/Target:", font=("JetBrains Mono", 10, "bold"), text_color=COLORS["text_dim"]).pack(anchor="w", padx=4, pady=(2, 0))
        self.target_combo = ctk.CTkComboBox(
            controls, width=190, height=28,
            values=[
                "scanme.nmap.org",
                "testphp.vulnweb.com",
                "httpbin.org",
                "badssl.com",
                "rest.vulnweb.com",
                "IP Personalizada"
            ],
            font=("JetBrains Mono", 11),
            fg_color=COLORS["bg_dark"],
            border_color=COLORS["border"],
            dropdown_fg_color=COLORS["bg_dark"]
        )
        self.target_combo.set("scanme.nmap.org")
        self.target_combo.pack(fill="x", padx=4, pady=(2, 6))

        # Slider de velocidad
        speed_row = ctk.CTkFrame(controls, fg_color="transparent")
        speed_row.pack(fill="x", padx=4, pady=(6, 2))

        ctk.CTkLabel(speed_row, text="⌨ Velocidad:",
                     font=("JetBrains Mono", 10, "bold"),
                     text_color=COLORS["text_dim"]).pack(side="left")

        self.speed_slider = ctk.CTkSlider(speed_row, from_=50, to=200,
                                           number_of_steps=15,
                                           command=self._on_speed_change,
                                           width=140,
                                           fg_color=COLORS["border"],
                                           progress_color=COLORS["accent_cyan"],
                                           button_color=COLORS["accent_cyan"])
        self.speed_slider.set(80) # Default to 80% (slower than normal)
        self.speed_slider.pack(side="left", padx=6)

        self.speed_label = ctk.CTkLabel(speed_row, text="80%",
                                         font=("JetBrains Mono", 10, "bold"),
                                         text_color=COLORS["accent_cyan"])
        self.speed_label.pack(side="left")

        # Selector de formato
        format_row = ctk.CTkFrame(controls, fg_color="transparent")
        format_row.pack(fill="x", padx=4, pady=(6, 2))

        ctk.CTkLabel(format_row, text="📐 Formato:",
                     font=("JetBrains Mono", 10, "bold"),
                     text_color=COLORS["text_dim"]).pack(side="left")

        self.format_combo = ctk.CTkOptionMenu(format_row, values=["9:16 (Vertical)", "16:9 (Horizontal)"], 
                                             font=("JetBrains Mono", 11),
                                             fg_color=COLORS["border"], button_color=COLORS["accent_magenta"], 
                                             button_hover_color="#9c27b0", width=140)
        self.format_combo.set("9:16 (Vertical)")
        self.format_combo.pack(side="left", padx=6)

        # Slider de duración de video
        dur_row = ctk.CTkFrame(controls, fg_color="transparent")
        dur_row.pack(fill="x", padx=4, pady=(6, 2))

        ctk.CTkLabel(dur_row, text="🎬 Duración:",
                     font=("JetBrains Mono", 10, "bold"),
                     text_color=COLORS["text_dim"]).pack(side="left")

        self.duration_slider = ctk.CTkSlider(dur_row, from_=1, to=30,
                                              number_of_steps=29,
                                              command=self._on_duration_change,
                                              width=140,
                                              fg_color=COLORS["border"],
                                              progress_color="#FF8F00",
                                              button_color="#FF8F00")
        self.duration_slider.set(5)
        self.duration_slider.pack(side="left", padx=6)

        self.duration_label = ctk.CTkLabel(dur_row, text="5 min",
                                            font=("JetBrains Mono", 10, "bold"),
                                            text_color="#FF8F00")
        self.duration_label.pack(side="left")
        self.video_duration_min = 5

        # Botones de acción
        btn_row = ctk.CTkFrame(controls, fg_color="transparent")
        btn_row.pack(fill="x", padx=4, pady=(15, 3))

        self.btn_tts = ctk.CTkButton(btn_row, text="🔊 TTS",
                                      command=self.generate_audios,
                                      font=("JetBrains Mono", 11, "bold"),
                                      fg_color="#1a1b2e",
                                      hover_color="#252640",
                                      border_width=1,
                                      border_color=COLORS["accent_cyan"],
                                      height=34)
        self.btn_tts.pack(fill="x", pady=(0, 6))

        self.btn_launch = ctk.CTkButton(btn_row, text="🎬 Lanzar",
                                         command=self.launch_konsole,
                                         fg_color=COLORS["accent_green"],
                                         hover_color="#00A23D",
                                         text_color="#000000",
                                         font=("JetBrains Mono", 11, "bold"),
                                         height=34)
        self.btn_launch.pack(fill="x", pady=2)

        self.btn_record = ctk.CTkButton(btn_row, text="🔴 Grabar",
                                         command=self.launch_and_record,
                                         fg_color="#D32F2F",
                                         hover_color="#B71C1C",
                                         text_color="#ffffff",
                                         font=("JetBrains Mono", 11, "bold"),
                                         height=34)
        self.btn_record.pack(fill="x", pady=2)

        self.btn_stop = ctk.CTkButton(btn_row, text="⏹ Detener",
                                       command=self.stop_director,
                                       fg_color="#424242",
                                       hover_color="#616161",
                                       text_color="#ffffff",
                                       font=("JetBrains Mono", 11, "bold"),
                                       height=34,
                                       state="disabled")
        self.btn_stop.pack(fill="x", pady=(2, 10))

        # Fila 2: Modos de video + Wrapper toggle
        self.btn_dynamic = ctk.CTkButton(controls, text="🚀 DUAL AI",
                                          command=self.launch_dynamic,
                                          fg_color="#7B1FA2",
                                          hover_color="#6A1B9A",
                                          text_color="#ffffff",
                                          font=("JetBrains Mono", 11, "bold"),
                                          height=34)
        self.btn_dynamic.pack(fill="x", padx=4, pady=(0, 4))

        self.btn_solo = ctk.CTkButton(controls, text="⚡ SOLO TERM",
                                       command=self.launch_solo,
                                       fg_color="#E65100",
                                       hover_color="#BF360C",
                                       text_color="#ffffff",
                                       font=("JetBrains Mono", 11, "bold"),
                                       height=34)
        self.btn_solo.pack(fill="x", padx=4, pady=(0, 10))

        self.use_wrapper_var = ctk.BooleanVar(value=False)
        self.wrapper_check = ctk.CTkCheckBox(
            controls, text="🔲 KR-CLI Wrapper (Terminal B)",
            variable=self.use_wrapper_var,
            font=("JetBrains Mono", 10),
            text_color=COLORS["text_dim"],
            fg_color=COLORS["accent_magenta"],
            hover_color="#9c27b0",
            checkbox_width=18, checkbox_height=18
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
            self.editor_container_a.pack(fill="both", expand=True)
            self.tab_btn_a.configure(fg_color=COLORS["accent_cyan"], text_color="#000000")
            self.tab_btn_b.configure(fg_color="#1a1b2e", text_color=COLORS["text_dim"])
        else:
            self.editor_container_a.pack_forget()
            self.editor_container_b.pack(fill="both", expand=True)
            self.tab_btn_b.configure(fg_color=COLORS["accent_green"], text_color="#000000")
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

    def _build_postprod_tab(self):
        """Pestaña 2: Editor de Video Profesional con Previsualizador y Timeline Interactivo."""
        from kr_studio.core.timeline_engine import TimelineEngine
        self.tl_engine = TimelineEngine(self.workspace_dir)
        self._selected_clip_id = None
        self._playhead_pos = 0.0
        self._tl_zoom = 1.0
        self._dragging_playhead = False
        self._dragging_clip_id = None       # Clip que se está arrastrando
        self._drag_offset_x = 0.0           # Offset del click dentro del clip
        self._preview_playing = False
        self._vlc_current_video_path = None # Para compatibilidad con drag-drop
        self._media_pool_items = []         # Lista de rutas importadas al Media Pool
        self._fullscreen_win = None
        self._video_muted = False          # Mute del audio del video
        self._previewer = None              # Se inicializa después de crear los widgets

        self.tab2.grid_rowconfigure(0, weight=3)   # Top: Media + Preview + Settings
        self.tab2.grid_rowconfigure(1, weight=0)   # Toolbar
        self.tab2.grid_rowconfigure(2, weight=2)   # Timeline
        self.tab2.grid_columnconfigure(0, weight=1)

        # ════════════════════════════════════════════
        # ZONA SUPERIOR: Media Pool | Previsualizador | Export Settings
        # ════════════════════════════════════════════
        top_frame = ctk.CTkFrame(self.tab2, fg_color="transparent")
        top_frame.grid(row=0, column=0, sticky="nsew", padx=6, pady=(6, 2))
        top_frame.grid_rowconfigure(0, weight=1)
        top_frame.grid_columnconfigure(0, weight=1)  # Media Pool
        top_frame.grid_columnconfigure(1, weight=2)  # Previsualizador (más ancho)
        top_frame.grid_columnconfigure(2, weight=1)  # Export Settings

        # ── 1. MEDIA POOL (con Drag & Drop al Timeline) ──
        media_frame = ctk.CTkFrame(top_frame, fg_color=COLORS["bg_panel"],
                                   corner_radius=10, border_width=1, border_color=COLORS["border"])
        media_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 3))

        mh = ctk.CTkFrame(media_frame, fg_color=COLORS["header_bg"], height=30, corner_radius=0)
        mh.pack(fill="x"); mh.pack_propagate(False)
        ctk.CTkLabel(mh, text="📂 MEDIA POOL", font=("JetBrains Mono", 10, "bold"),
                     text_color=COLORS["accent_cyan"]).pack(side="left", padx=8)

        # Botones pequeños en la cabecera
        tb = {"width": 60, "height": 22, "font": ("JetBrains Mono", 8), "corner_radius": 4}
        ctk.CTkButton(mh, text="+ Import", fg_color="#27ae60", hover_color="#2ecc71",
                      command=self._import_media, **tb).pack(side="right", padx=(2, 6))
        ctk.CTkButton(mh, text="💾 Save", fg_color="#2980b9", hover_color="#3498db",
                      command=self._save_project, **tb).pack(side="right", padx=2)
        ctk.CTkButton(mh, text="📂 Load", fg_color="#8e44ad", hover_color="#9b59b6",
                      command=self._load_project, **tb).pack(side="right", padx=2)

        # Instrucciones
        ctk.CTkLabel(media_frame, text="Arrastra un archivo al Timeline ↓",
                     font=("JetBrains Mono", 8), text_color="#4a4b5e").pack(padx=6, pady=(4, 0))

        # Listbox nativo (soporta drag)
        self.media_listbox = tk.Listbox(media_frame, bg="#07080e", fg="#8a8b9e",
                                         selectbackground="#1a3a5c", selectforeground="#00D9FF",
                                         font=("JetBrains Mono", 9), borderwidth=0,
                                         highlightthickness=0, activestyle="none")
        self.media_listbox.pack(fill="both", expand=True, padx=6, pady=(2, 6))
        self.media_listbox.bind("<ButtonPress-1>", self._media_drag_start)
        self.media_listbox.bind("<B1-Motion>", self._media_drag_motion)
        self.media_listbox.bind("<ButtonRelease-1>", self._media_drag_drop)

        # ── 2. PREVISUALIZADOR ──
        preview_frame = ctk.CTkFrame(top_frame, fg_color=COLORS["bg_panel"],
                                     corner_radius=10, border_width=1, border_color=COLORS["border"])
        preview_frame.grid(row=0, column=1, sticky="nsew", padx=3)

        ph = ctk.CTkFrame(preview_frame, fg_color=COLORS["header_bg"], height=30, corner_radius=0)
        ph.pack(fill="x"); ph.pack_propagate(False)
        ctk.CTkLabel(ph, text="🖥️ PREVISUALIZADOR", font=("JetBrains Mono", 10, "bold"),
                     text_color=COLORS["accent_cyan"]).pack(side="left", padx=8)
        # Botón pantalla completa
        ctk.CTkButton(ph, text="⛶", width=28, height=22, font=("JetBrains Mono", 14),
                      fg_color="transparent", hover_color="#2a2b3e",
                      command=self._toggle_fullscreen).pack(side="right", padx=2)
        self.preview_timecode = ctk.CTkLabel(ph, text="00:00:00.000", font=("JetBrains Mono", 10),
                                              text_color=COLORS["accent_green"])
        self.preview_timecode.pack(side="right", padx=8)

        # Canvas/Frame de preview — VLC se embebe aquí
        self.preview_video_frame = tk.Frame(preview_frame, bg="#000000")
        self.preview_video_frame.pack(fill="both", expand=True, padx=6, pady=(6, 2))
        # Placeholder text (se borra al cargar video)
        self._preview_placeholder = tk.Label(self.preview_video_frame, text="Importa un video para reproducir",
                                              bg="#000000", fg="#4a4b5e", font=("JetBrains Mono", 11))
        self._preview_placeholder.place(relx=0.5, rely=0.5, anchor="center")

        # Controles de reproducción
        ctrl_bar = ctk.CTkFrame(preview_frame, fg_color="transparent", height=38)
        ctrl_bar.pack(fill="x", padx=6, pady=(0, 4))
        ctrl_bar.pack_propagate(False)

        btn_style = {"width": 34, "height": 30, "font": ("JetBrains Mono", 15),
                     "fg_color": "#1a1b2e", "hover_color": "#2a2b3e", "corner_radius": 6}
        ctk.CTkButton(ctrl_bar, text="⏮", command=self._preview_goto_start, **btn_style).pack(side="left", padx=2)
        self.btn_play = ctk.CTkButton(ctrl_bar, text="▶", command=self._preview_play_pause, **btn_style)
        self.btn_play.pack(side="left", padx=2)
        ctk.CTkButton(ctrl_bar, text="⏹", command=self._preview_stop, **btn_style).pack(side="left", padx=2)
        ctk.CTkButton(ctrl_bar, text="⏭", command=self._preview_goto_end, **btn_style).pack(side="left", padx=2)

        # Volume slider
        self._vlc_volume = tk.IntVar(value=80)
        vol_lbl = ctk.CTkLabel(ctrl_bar, text="🔊", font=("JetBrains Mono", 12))
        vol_lbl.pack(side="right", padx=(0, 2))
        self.vol_slider = ctk.CTkSlider(ctrl_bar, from_=0, to=100, number_of_steps=100,
                                         command=self._on_volume, width=60, height=12,
                                         button_color="#2ecc71", progress_color="#2ecc71")
        self.vol_slider.pack(side="right", padx=(4, 0))
        self.vol_slider.set(80)

        # Botón Mute Video Audio
        self.btn_mute_video = ctk.CTkButton(ctrl_bar, text="📹🔊", width=40, height=28,
                                             font=("JetBrains Mono", 11),
                                             fg_color="#1a1b2e", hover_color="#2a2b3e",
                                             corner_radius=6, command=self._toggle_video_mute)
        self.btn_mute_video.pack(side="right", padx=(4, 0))

        # Slider scrubbing (progreso del video)
        self.preview_slider = ctk.CTkSlider(ctrl_bar, from_=0, to=1000, number_of_steps=1000,
                                             command=self._on_scrub, height=14,
                                             button_color=COLORS["accent_cyan"],
                                             progress_color=COLORS["accent_cyan"])
        self.preview_slider.pack(side="left", fill="x", expand=True, padx=(8, 8))
        self.preview_slider.set(0)

        # ── Inicializar el Previsualizer (Motor VLC desacoplado) ──
        from kr_studio.ui.previsualizer import Previsualizer
        self._previewer = Previsualizer(
            tl_engine=self.tl_engine,
            video_frame=self.preview_video_frame,
            root=self,
            callbacks={
                "on_timecode": lambda text: self.preview_timecode.configure(text=text),
                "on_slider": lambda val: self.preview_slider.set(val),
                "on_playhead": lambda pos: self._sync_playhead(pos),
                "on_play_state": lambda playing: self.btn_play.configure(text="⏸" if playing else "▶"),
                "on_draw_timeline": lambda: self._draw_timeline(),
                "on_chat": lambda role, msg: self.append_chat(role, msg),
            }
        )

        # ── 3. EXPORT SETTINGS ──
        export_frame = ctk.CTkFrame(top_frame, fg_color=COLORS["bg_panel"],
                                    corner_radius=10, border_width=1, border_color=COLORS["border"])
        export_frame.grid(row=0, column=2, sticky="nsew", padx=(3, 0))

        eh = ctk.CTkFrame(export_frame, fg_color=COLORS["header_bg"], height=30, corner_radius=0)
        eh.pack(fill="x"); eh.pack_propagate(False)
        ctk.CTkLabel(eh, text="⚙️ EXPORTAR", font=("JetBrains Mono", 10, "bold"),
                     text_color=COLORS["accent_green"]).pack(side="left", padx=8)

        si = ctk.CTkFrame(export_frame, fg_color="transparent")
        si.pack(fill="both", expand=True, padx=10, pady=8)

        for lbl_text, attr_name, values in [
            ("Resolución:", "res_combo", ["9:16 Vertical (1080x1920)", "1080p (1920x1080)", "4K (3840x2160)", "720p (1280x720)"]),
            ("Preset:", "quality_combo", ["fast", "medium", "slow (Máxima)"]),
            ("Audio:", "audio_mix_combo", ["Auto-Sync (JSON)", "Solo Video"]),
        ]:
            r = ctk.CTkFrame(si, fg_color="transparent")
            r.pack(fill="x", pady=(0, 5))
            ctk.CTkLabel(r, text=lbl_text, font=("JetBrains Mono", 10)).pack(side="left")
            combo = ctk.CTkComboBox(r, values=values, width=130, font=("JetBrains Mono", 9))
            combo.pack(side="right")
            setattr(self, attr_name, combo)

        self.btn_manual_render = ctk.CTkButton(si, text="🎞️ Exportar MP4", command=self._manual_render,
                                                fg_color="#1565c0", hover_color="#0d47a1", height=30,
                                                font=("JetBrains Mono", 10, "bold"))
        self.btn_manual_render.pack(fill="x", pady=(8, 4))

        self.post_mode_var = ctk.StringVar(value="SOLO TERM")
        self.btn_auto_render = ctk.CTkButton(si, text="🤖 Auto-Grabar", command=self._auto_record_and_render,
                                              fg_color="#e65100", hover_color="#bf360c", height=30,
                                              font=("JetBrains Mono", 10, "bold"))
        self.btn_auto_render.pack(fill="x", pady=(0, 4))

        self.render_status = ctk.CTkLabel(si, text="Lista.", font=("JetBrains Mono", 9),
                                          text_color=COLORS["text_dim"])
        self.render_status.pack()

        # ════════════════════════════════════════════
        # BARRA DE HERRAMIENTAS DE EDICIÓN (Toolbar)
        # ════════════════════════════════════════════
        toolbar = ctk.CTkFrame(self.tab2, fg_color=COLORS["header_bg"], height=36, corner_radius=0)
        toolbar.grid(row=1, column=0, sticky="ew", padx=6, pady=2)
        toolbar.pack_propagate(False)

        tb = {"width": 100, "height": 26, "font": ("JetBrains Mono", 10), "corner_radius": 6}
        ctk.CTkButton(toolbar, text="✂ Cortar", command=self._tool_cut,
                      fg_color="#c0392b", hover_color="#e74c3c", **tb).pack(side="left", padx=4, pady=4)
        ctk.CTkButton(toolbar, text="🗑 Eliminar", command=self._tool_delete,
                      fg_color="#7f8c8d", hover_color="#95a5a6", **tb).pack(side="left", padx=4, pady=4)
        ctk.CTkButton(toolbar, text="🔇 Silenciar", command=self._tool_mute,
                      fg_color="#8e44ad", hover_color="#9b59b6", **tb).pack(side="left", padx=4, pady=4)
        ctk.CTkButton(toolbar, text="↩ Deshacer", command=self._tool_undo,
                      fg_color="#2c3e50", hover_color="#34495e", **tb).pack(side="left", padx=4, pady=4)

        self.selected_clip_lbl = ctk.CTkLabel(toolbar, text="Sin selección",
                                               font=("JetBrains Mono", 9), text_color=COLORS["text_dim"])
        self.selected_clip_lbl.pack(side="right", padx=12)

        # ════════════════════════════════════════════
        # TIMELINE MULTICANAL INTERACTIVO
        # ════════════════════════════════════════════
        tl_frame = ctk.CTkFrame(self.tab2, fg_color=COLORS["bg_panel"],
                                corner_radius=10, border_width=1, border_color=COLORS["border"])
        tl_frame.grid(row=2, column=0, sticky="nsew", padx=6, pady=(2, 6))

        tlh = ctk.CTkFrame(tl_frame, fg_color=COLORS["header_bg"], height=30, corner_radius=0)
        tlh.pack(fill="x"); tlh.pack_propagate(False)
        ctk.CTkLabel(tlh, text="🎬 TIMELINE", font=("JetBrains Mono", 10, "bold"),
                     text_color=COLORS["accent_yellow"]).pack(side="left", padx=8)
        self.timeline_duration_lbl = ctk.CTkLabel(tlh, text="⏱ 00:00.0s",
                                                   font=("JetBrains Mono", 10), text_color=COLORS["text_dim"])
        self.timeline_duration_lbl.pack(side="right", padx=8)

        # Zoom slider
        ctk.CTkLabel(tlh, text="🔍", font=("JetBrains Mono", 10)).pack(side="right")
        self.zoom_slider = ctk.CTkSlider(tlh, from_=0.5, to=5.0, number_of_steps=45,
                                          command=self._on_zoom, width=80, height=12,
                                          button_color="#f1c40f", progress_color="#f1c40f")
        self.zoom_slider.pack(side="right", padx=4)
        self.zoom_slider.set(1.0)

        # Canvas Principal del Timeline
        self.timeline_canvas = tk.Canvas(tl_frame, bg="#0a0b12", highlightthickness=0)
        self.timeline_canvas.pack(fill="both", expand=True, padx=6, pady=(4, 2))

        # Scrollbar horizontal
        self.tl_scrollbar = tk.Scrollbar(tl_frame, orient="horizontal", command=self.timeline_canvas.xview)
        self.tl_scrollbar.pack(fill="x", padx=6, pady=(0, 2))
        self.timeline_canvas.configure(xscrollcommand=self.tl_scrollbar.set)

        # Leyenda
        leg = ctk.CTkFrame(tl_frame, fg_color="transparent", height=22)
        leg.pack(fill="x", padx=6, pady=(0, 4))
        for txt, clr in [("[V1] Video", "#2ecc71"), ("[A1] Voz TTS", "#3498db"),
                          ("[A2] Música", "#9b59b6"), ("▶ Playhead", "#e74c3c")]:
            ctk.CTkLabel(leg, text=txt, font=("JetBrains Mono", 8), text_color=clr).pack(side="left", padx=6)

        # Bindings para interactividad del timeline
        self.timeline_canvas.bind("<Button-1>", self._tl_on_click)
        self.timeline_canvas.bind("<B1-Motion>", self._tl_on_drag)
        self.timeline_canvas.bind("<ButtonRelease-1>", self._tl_on_release)
        self.timeline_canvas.bind("<Double-Button-1>", self._tl_on_double_click)

    # ─── Constantes del Timeline ───
    _TL_PADDING_X = 90
    _TL_RULER_H = 18
    _TL_TRACKS = [
        {"id": "V3", "name": "📹 V3 Top",  "color": "#1abc9c", "y_offset": 0, "height": 28},
        {"id": "V2", "name": "📹 V2 Mid",  "color": "#2ecc71", "y_offset": 1, "height": 28},
        {"id": "V1", "name": "📹 V1 Base", "color": "#27ae60", "y_offset": 2, "height": 28},
        {"id": "A1", "name": "🔊 TTS  ",  "color": "#3498db", "y_offset": 3, "height": 28},
        {"id": "A2", "name": "🎵 Fondo",   "color": "#9b59b6", "y_offset": 4, "height": 28},
    ]
    _IMAGE_DURATION = 5.0  # Duración por defecto para imágenes en la pista de video

    def _tl_get_track_at_y(self, cy):
        """Detecta qué pista (V1/A1/A2) está bajo la coordenada Y del canvas."""
        track_gap = 4
        for tidx, track in enumerate(self._TL_TRACKS):
            ty = self._TL_RULER_H + 8 + tidx * (track["height"] + track_gap)
            if ty <= cy <= ty + track["height"]:
                return track["id"]
        return None

    def _get_tl_scale(self):
        """Calcula píxeles-por-segundo del timeline."""
        w = self.timeline_canvas.winfo_width() or 800
        total_dur = max(self.tl_engine.total_duration + 10, 30)
        usable = w - self._TL_PADDING_X - 20
        return (usable / total_dur) * self._tl_zoom

    def _draw_timeline(self, timestamps: dict = None):
        """Dibuja el timeline completo desde el TimelineEngine."""
        if timestamps:
            self.timestamps = timestamps
        canvas = self.timeline_canvas
        canvas.delete("all")

        w = canvas.winfo_width() or 800
        h = canvas.winfo_height() or 180
        px = self._TL_PADDING_X
        scale = self._get_tl_scale()
        total_dur = max(self.tl_engine.total_duration + 10, 30)

        # Scroll region
        total_px = int(px + total_dur * scale + 50)
        canvas.configure(scrollregion=(0, 0, total_px, h))

        m, s = divmod(int(total_dur), 60)
        self.timeline_duration_lbl.configure(text=f"⏱ {m:02d}:{s:02d}.0s")

        # ── Regla de tiempo ──
        ry = self._TL_RULER_H
        canvas.create_line(px, ry, total_px, ry, fill="#2a2b3e", width=1)
        step = max(1, int(5 / self._tl_zoom))
        for t in range(0, int(total_dur) + step, step):
            x = px + t * scale
            canvas.create_line(x, ry - 4, x, ry + 4, fill="#4a4b5e")
            canvas.create_text(x, ry - 9, text=f"{t}s", fill="#5a5b6e", font=("JetBrains Mono", 7))

        # ── Pistas ──
        track_gap = 4
        for tidx, track in enumerate(self._TL_TRACKS):
            ty = self._TL_RULER_H + 8 + tidx * (track["height"] + track_gap)
            # Label del track
            canvas.create_text(6, ty + track["height"]//2, text=track["name"],
                               fill="#6a6b7e", font=("JetBrains Mono", 8), anchor="w")
            # Fondo de la pista
            canvas.create_rectangle(px, ty, total_px, ty + track["height"],
                                    fill="#0d0e16", outline="#1a1b26")
            track["_render_y"] = ty  # Guardar posición calculada

        # ── Función Hash Color ──
        def _get_clip_color(source_path: str, base_color: str) -> str:
            """Genera un color único y consistente por archivo, basado en el color original de la pista."""
            import hashlib
            filename = os.path.basename(source_path)
            hash_val = int(hashlib.md5(filename.encode()).hexdigest(), 16)
            
            # Extraer RGB del color base (hex #RRGGBB)
            r = int(base_color[1:3], 16)
            g = int(base_color[3:5], 16)
            b = int(base_color[5:7], 16)
            
            # Variar ligeramente el HUE/Luminancia según el hash (+- 30 puntos)
            offset_r = (hash_val % 60) - 30
            offset_g = ((hash_val // 60) % 60) - 30
            offset_b = ((hash_val // 3600) % 60) - 30
            
            new_r = max(0, min(255, r + offset_r))
            new_g = max(0, min(255, g + offset_g))
            new_b = max(0, min(255, b + offset_b))
            
            return f"#{new_r:02x}{new_g:02x}{new_b:02x}"

        # ── Clips reales ──
        for clip in self.tl_engine.clips:
            tr = next((t for t in self._TL_TRACKS if t["id"] == clip.track), None)
            if not tr:
                continue
            ty = tr["_render_y"]
            x1 = px + clip.start * scale
            x2 = px + clip.end * scale
            clip_w = max(x2 - x1, 4)

            # Usar color único por clip
            base_track_color = tr["color"]
            color = _get_clip_color(clip.source_path, base_track_color)
            fill_color = color if not clip.muted else "#3a3b4e"
            outline = "#ffffff" if clip.clip_id == self._selected_clip_id else ""
            outline_w = 2 if clip.clip_id == self._selected_clip_id else 0

            # Bloque del clip
            canvas.create_rectangle(x1, ty + 1, x1 + clip_w, ty + tr["height"] - 1,
                                    fill=fill_color, outline=outline, width=outline_w,
                                    tags=f"clip_{clip.clip_id}")
            # Label
            lbl = clip.label[:20]
            if clip.muted:
                lbl = f"🔇 {lbl}"
            # Asegurar contraste de texto
            canvas.create_text(x1 + 4, ty + tr["height"]//2, text=lbl,
                               fill="#ffffff", font=("JetBrains Mono", 7), anchor="w",
                               tags=f"clip_{clip.clip_id}")

        # ── Playhead (línea roja vertical) ──
        ph_x = px + self._playhead_pos * scale
        canvas.create_line(ph_x, 0, ph_x, h, fill="#e74c3c", width=2, tags="playhead")
        canvas.create_polygon(ph_x - 5, 0, ph_x + 5, 0, ph_x, 8,
                              fill="#e74c3c", tags="playhead")

    # ─── Interactividad del Timeline (Drag & Drop de clips) ───

    def _tl_find_clip_at(self, cx, cy):
        """Busca un clip en las coordenadas del canvas."""
        items = self.timeline_canvas.find_overlapping(cx - 2, cy - 2, cx + 2, cy + 2)
        for item in items:
            for tag in self.timeline_canvas.gettags(item):
                if tag.startswith("clip_"):
                    try:
                        return int(tag.split("_")[1])
                    except ValueError:
                        pass
        return None

    def _tl_on_click(self, event):
        """Click en el timeline: seleccionar clip (preparar drag) o mover playhead."""
        canvas = self.timeline_canvas
        cx = canvas.canvasx(event.x)
        cy = canvas.canvasy(event.y)
        px = self._TL_PADDING_X
        scale = self._get_tl_scale()

        # ¿Click en zona del playhead (regla superior)?
        if cy < self._TL_RULER_H + 8:
            self._dragging_playhead = True
            self._dragging_clip_id = None
            self._playhead_pos = max(0, (cx - px) / scale)
            if self._previewer:
                self._previewer.playhead_pos = self._playhead_pos
            self._update_preview_from_playhead()
            self._show_preview_frame(self._playhead_pos)
            self._hide_placeholder()
            self._draw_timeline()
            return

        # ¿Click en un clip? → preparar para drag
        clicked_clip = self._tl_find_clip_at(cx, cy)
        if clicked_clip:
            self._selected_clip_id = clicked_clip
            self._dragging_clip_id = clicked_clip
            clip = self.tl_engine.get_clip_by_id(clicked_clip)
            if clip:
                self._drag_offset_x = (cx - px) / scale - clip.start
                self.selected_clip_lbl.configure(text=f"📌 {clip.label} ({clip.track} | {clip.duration:.1f}s)")
        else:
            self._selected_clip_id = None
            self._dragging_clip_id = None
            self._dragging_playhead = True   # ← Permite hacer scrub arrastrando desde el fondo vacío
            self.selected_clip_lbl.configure(text="Sin selección")
            # Mover playhead al click
            self._playhead_pos = max(0, (cx - px) / scale)
            if self._previewer:
                self._previewer.playhead_pos = self._playhead_pos
            self._update_preview_from_playhead()
            self._show_preview_frame(self._playhead_pos)
            self._hide_placeholder()

        self._draw_timeline()

    def _tl_on_drag(self, event):
        """Arrastrar: mover playhead O mover un clip suavemente."""
        cx = self.timeline_canvas.canvasx(event.x)
        px = self._TL_PADDING_X
        scale = self._get_tl_scale()

        if self._dragging_playhead:
            self._playhead_pos = max(0, (cx - px) / scale)
            if self._previewer:
                self._previewer.playhead_pos = self._playhead_pos
            self._update_preview_from_playhead()
            self._show_preview_frame(self._playhead_pos)
            self._draw_timeline()
        elif self._dragging_clip_id:
            # Mover clip en tiempo real con el ratón
            new_start = max(0, (cx - px) / scale - self._drag_offset_x)
            clip = self.tl_engine.get_clip_by_id(self._dragging_clip_id)
            if clip:
                clip.start = new_start  # Movimiento directo sin undo per-frame
                self._draw_timeline()

    def _tl_on_release(self, event):
        """Al soltar el mouse: guardar undo si se arrastró un clip."""
        if self._dragging_clip_id:
            # Guardar undo ahora que el arrastre terminó
            self.tl_engine._save_undo()
            self._dragging_clip_id = None
        self._dragging_playhead = False

    def _tl_on_double_click(self, event):
        """Doble-click: mover clip seleccionado a la posición del playhead."""
        if self._selected_clip_id:
            self.tl_engine.move_clip(self._selected_clip_id, self._playhead_pos)
            self._draw_timeline()

    # ─── Herramientas de Edición (Toolbar) ───

    def _tool_cut(self):
        """Corta el clip seleccionado en la posición del playhead, creando un gap de 3s para inserción."""
        if not self._selected_clip_id:
            self.append_chat("Editor", "⚠ Selecciona un clip primero para cortar.")
            return
        gap_duration = 3.0  # Segundos de gap para insertar contenido
        clip = self.tl_engine.get_clip_by_id(self._selected_clip_id)
        if not clip:
            return

        # Primero dividir
        ok = self.tl_engine.split_clip_at(self._selected_clip_id, self._playhead_pos)
        if not ok:
            self.append_chat("Editor", "⚠ El playhead no está dentro del clip seleccionado.")
            return

        # Mover la parte derecha (el último clip añadido) para crear el gap
        right_clips = [c for c in self.tl_engine.clips
                       if c.track == clip.track and c.start >= self._playhead_pos]
        right_clips.sort(key=lambda c: c.start)
        for rc in right_clips:
            rc.start += gap_duration

        self.append_chat("Editor", f"✂ Cortado en {self._playhead_pos:.1f}s — gap de {gap_duration}s creado. "
                                    f"Arrastra un video/imagen del Media Pool al gap.")
        self._draw_timeline()

    def _tool_delete(self):
        """Elimina el clip seleccionado del timeline."""
        if not self._selected_clip_id:
            self.append_chat("Editor", "⚠ Selecciona un clip primero para eliminar.")
            return
        self.tl_engine.remove_clip(self._selected_clip_id)
        self._selected_clip_id = None
        self.selected_clip_lbl.configure(text="Sin selección")
        self.append_chat("Editor", "🗑 Clip eliminado.")
        self._draw_timeline()

    def _tool_mute(self):
        """Silencia o reactiva el clip de audio seleccionado."""
        if not self._selected_clip_id:
            self.append_chat("Editor", "⚠ Selecciona un clip de audio para silenciar.")
            return
        self.tl_engine.toggle_mute(self._selected_clip_id)
        self._draw_timeline()

    def _tool_undo(self):
        """Deshace la última acción."""
        if self.tl_engine.undo():
            self.append_chat("Editor", "↩ Acción deshecha.")
            self._draw_timeline()
        else:
            self.append_chat("Editor", "⚠ No hay acciones para deshacer.")

    # ─── Previsualizador VLC (delegado a Previsualizer) ───
    # Toda la lógica de VLC vive ahora en kr_studio/ui/previsualizer.py
    # Estos métodos son wrappers finos para mantener compatibilidad con el resto del código.

    def _sync_playhead(self, pos: float):
        """Callback del previsualizador para mantener sincronizada la línea roja."""
        self._playhead_pos = pos

    def _hide_placeholder(self):
        """Oculta el placeholder 'Importa un video' del previsualizador."""
        if hasattr(self, '_preview_placeholder') and self._preview_placeholder:
            try:
                self._preview_placeholder.place_forget()
                self._preview_placeholder.destroy()
            except Exception:
                pass
            self._preview_placeholder = None

    def _init_vlc(self):
        """Delegado: inicializa VLC a través del Previsualizer."""
        if self._previewer:
            return self._previewer._init_vlc()
        return False

    def _embed_vlc_player(self):
        """Delegado: embebe VLC en el frame."""
        if self._previewer:
            self._previewer._embed_player()

    def _load_video_vlc(self, path: str):
        """Delegado: carga un video en VLC."""
        if self._previewer:
            self._previewer.load_video(path)
            self._vlc_current_video_path = path
            # Borrar placeholder
            if hasattr(self, '_preview_placeholder') and self._preview_placeholder:
                self._preview_placeholder.place_forget()
                self._preview_placeholder = None

    def _update_preview_from_playhead(self):
        """Delegado: actualiza timecode/slider desde el playhead."""
        if self._previewer:
            self._playhead_pos = self._previewer.playhead_pos
            self._previewer._update_ui_from_playhead()

    def _show_preview_frame(self, time_pos: float):
        """Delegado: mueve VLC al frame correcto."""
        if self._previewer:
            self._previewer.show_frame_at(time_pos)

    def _on_scrub(self, value):
        """Delegado: callback del slider de scrubbing."""
        if self._previewer:
            self._previewer.scrub(value)
            self._playhead_pos = self._previewer.playhead_pos

    def _on_volume(self, value):
        """Delegado: ajusta el volumen."""
        vol = int(value)
        if self._previewer:
            self._previewer.set_volume(vol)

    def _toggle_video_mute(self):
        """Delegado: silencia o reactiva el audio del video."""
        if self._previewer:
            muted = self._previewer.toggle_video_mute()
            self._video_muted = muted
            if muted:
                self.btn_mute_video.configure(text="📹🔇", fg_color="#c0392b")
                self.append_chat("Editor", "🔇 Audio del video silenciado.")
            else:
                self.btn_mute_video.configure(text="📹🔊", fg_color="#1a1b2e")
                self.append_chat("Editor", "🔊 Audio del video reactivado.")

    def _preview_play_pause(self):
        """Delegado: alterna reproducción timeline-driven."""
        if self._previewer:
            self._hide_placeholder()
            self._previewer.play_pause()
            self._preview_playing = self._previewer.is_playing
            self._playhead_pos = self._previewer.playhead_pos

    def _vlc_poll_position(self):
        """Delegado: loop de polling (ya no se llama desde aquí, vive en Previsualizer)."""
        pass  # El polling vive ahora dentro de Previsualizer._poll_position

    def _get_or_create_audio_player(self, track: str):
        """Delegado: crea/obtiene reproductor de audio."""
        if self._previewer:
            return self._previewer._get_or_create_audio_player(track)
        return None

    def _sync_audio_tracks(self, timeline_pos: float, force_start: bool = False):
        """Delegado: sincroniza pistas de audio."""
        if self._previewer:
            self._previewer._sync_audio(timeline_pos, force_start)

    def _preview_stop(self):
        """Delegado: detiene la reproducción."""
        if self._previewer:
            self._previewer.stop()
            self._preview_playing = False
            self._playhead_pos = 0.0

    def _preview_goto_start(self):
        """Delegado: salta al inicio."""
        if self._previewer:
            self._previewer.goto_start()
            self._playhead_pos = 0.0

    def _preview_goto_end(self):
        """Delegado: salta al final."""
        if self._previewer:
            self._previewer.goto_end()
            self._playhead_pos = self._previewer.playhead_pos

    def _on_zoom(self, value):
        self._tl_zoom = value
        self._draw_timeline()

    # ─── Guardar / Cargar Proyecto ───

    def _save_project(self):
        """Guarda el estado del timeline y el pool en un archivo .krproj (JSON)."""
        import json
        
        if not self.tl_engine.clips and not self._media_pool_items:
            self.append_chat("Sistema", "⚠ No hay nada que guardar.")
            return

        path = filedialog.asksaveasfilename(
            title="Guardar Proyecto KR-STUDIO",
            defaultextension=".krproj",
            filetypes=[("KR-STUDIO Project", "*.krproj"), ("Archivos JSON", "*.json")],
            initialdir=self.workspace_dir
        )
        if not path:
            return

        data = {
            "media_pool": self._media_pool_items,
            "timeline": self.tl_engine.to_dict()
        }

        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            self.append_chat("Sistema", f"💾 Proyecto guardado:\n{os.path.basename(path)}")
        except Exception as e:
            self.append_chat("Error", f"❌ Error guardando: {e}")

    def _load_project(self):
        """Carga un estado del timeline desde un archivo .krproj (JSON)."""
        import json

        path = filedialog.askopenfilename(
            title="Cargar Proyecto KR-STUDIO",
            filetypes=[("KR-STUDIO Project", "*.krproj"), ("Archivos JSON", "*.json")],
            initialdir=self.workspace_dir
        )
        if not path:
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Limpiar estado actual
            self._preview_stop()
            self._media_pool_items.clear()
            self.media_listbox.delete(0, tk.END)
            self._vlc_current_video_path = None
            self._raw_video_path = None
            
            # Restaurar Media Pool
            pool = data.get("media_pool", [])
            for p in pool:
                if os.path.exists(p):
                    self._media_pool_items.append(p)
                    name = os.path.basename(p)
                    icon = "🎬" if p.lower().endswith(('.mp4', '.mkv', '.avi', '.png', '.jpg')) else "🔊"
                    self.media_listbox.insert(tk.END, f"{icon} {name}")
            
            # Restaurar Timeline
            self.tl_engine.from_dict(data.get("timeline", {}))
            
            # Recargar ventana
            self._playhead_pos = 0.0
            self._show_preview_frame(0.0)
            self._draw_timeline()
            
            self.append_chat("Sistema", f"📂 Proyecto cargado:\n{os.path.basename(path)}")

        except Exception as e:
            self.append_chat("Error", f"❌ Error cargando proyecto: {e}")

    # ─── Importar Media ───

    def _import_media(self):
        """Abre file dialog para importar video o audio solo al Media Pool."""
        path = filedialog.askopenfilename(
            title="Importar Media",
            filetypes=[("Video & Imágenes", "*.mp4 *.mkv *.avi *.png *.jpg *.jpeg"),
                       ("Audio", "*.mp3 *.wav *.ogg"), ("Todos", "*.*")],
            initialdir=os.path.expanduser("~/Videos")
        )
        if not path:
            return
        name = os.path.basename(path)
        is_video = path.lower().endswith(('.mp4', '.mkv', '.avi', '.png', '.jpg', '.jpeg'))

        if is_video:
            icon = "🎬"
            self.append_chat("Editor", f"📹 Media añadido al pool: {name}")
        else:
            icon = "🔊"
            self.append_chat("Editor", f"🎵 Audio añadido al pool: {name}")

        # Añadir al pool (sin duplicados y sin insertar al timeline)
        if path not in self._media_pool_items:
            self._media_pool_items.append(path)
            self.media_listbox.insert(tk.END, f"{icon} {name}")

    def _select_raw_video(self):
        self._import_media()

    # ─── Media Pool Drag → Timeline ───

    def _media_drag_start(self, event):
        """Inicia el drag desde el Media Pool."""
        idx = self.media_listbox.nearest(event.y)
        if idx < 0 or idx >= len(self._media_pool_items):
            self._drag_media_idx = None
            return
        self._drag_media_idx = idx
        self.media_listbox.selection_clear(0, tk.END)
        self.media_listbox.selection_set(idx)

    def _media_drag_motion(self, event):
        """Muestra cursor de arrastre y dibuja preview 'ghost' en el timeline."""
        if getattr(self, '_drag_media_idx', None) is not None:
            self.media_listbox.configure(cursor="hand2")
            
            # Obtener coordenadas relativas al timeline
            tl_x_root = self.timeline_canvas.winfo_rootx()
            tl_y_root = self.timeline_canvas.winfo_rooty()
            tl_w = self.timeline_canvas.winfo_width()
            tl_h = self.timeline_canvas.winfo_height()

            # Limpiar ghost previo
            self.timeline_canvas.delete("drag_ghost")

            # Si el ratón está sobre el timeline, dibujar preview
            if tl_x_root <= event.x_root <= tl_x_root + tl_w and tl_y_root <= event.y_root <= tl_y_root + tl_h:
                cx = self.timeline_canvas.canvasx(event.x_root - tl_x_root)
                cy = self.timeline_canvas.canvasy(event.y_root - tl_y_root)
                track_id = self._tl_get_track_at_y(cy)

                if track_id:
                    # Encontrar los datos de la pista
                    tr = next((t for t in self._TL_TRACKS if t["id"] == track_id), None)
                    if tr:
                        ty = tr.get("_render_y", 0)
                        if ty > 0:
                            # Dibujar bloque transparente indicando dónde caerá
                            width = 100  # un ancho aproximado genérico
                            self.timeline_canvas.create_rectangle(
                                cx, ty + 1, cx + width, ty + tr["height"] - 1,
                                fill="", outline="#f1c40f", dash=(4, 2), width=2,
                                tags="drag_ghost"
                            )

    def _media_drag_drop(self, event):
        """Suelta el archivo del Media Pool. Si cae en el timeline, añade el clip."""
        self.media_listbox.configure(cursor="")
        self.timeline_canvas.delete("drag_ghost")  # Limpiar ghost

        idx = getattr(self, '_drag_media_idx', None)
        if idx is None or idx >= len(self._media_pool_items):
            return
        path = self._media_pool_items[idx]
        name = os.path.basename(path)
        is_video = path.lower().endswith(('.mp4', '.mkv', '.avi'))
        is_image = path.lower().endswith(('.png', '.jpg', '.jpeg'))

        # Detectar si el mouse soltó sobre el frame del timeline
        tl_x_root = self.timeline_canvas.winfo_rootx()
        tl_y_root = self.timeline_canvas.winfo_rooty()
        tl_w = self.timeline_canvas.winfo_width()
        tl_h = self.timeline_canvas.winfo_height()

        if tl_x_root <= event.x_root <= tl_x_root + tl_w and tl_y_root <= event.y_root <= tl_y_root + tl_h:
            # Calcular en qué track y posición temporal se soltó
            cx = self.timeline_canvas.canvasx(event.x_root - tl_x_root)
            cy = self.timeline_canvas.canvasy(event.y_root - tl_y_root)
            scale = self._get_tl_scale()
            drop_time = max(0.0, (cx - self._TL_PADDING_X) / scale)
            target_track = self._tl_get_track_at_y(cy)

            is_video_type = is_video or is_image

            if target_track:
                # Validar tipo de track
                if is_video_type and not target_track.startswith("V"):
                    target_track = "V2"  # V2 es buen default para arrastrar encima de la base
                elif not is_video_type and target_track.startswith("V"):
                    target_track = "A2"
            else:
                target_track = "V2" if is_video_type else ("A1" if "tts" in name.lower() or "audio_" in name.lower() else "A2")

            if is_video_type:
                dur = self.tl_engine._get_video_duration(path)
                self.tl_engine.add_clip(source_path=path, track=target_track, start=drop_time,
                                         duration=dur, label=name)
                # Si es el primer video en el proyecto
                if self._vlc_current_video_path is None and drop_time == 0:
                    self._vlc_current_video_path = path
                    self._load_video_vlc(path)
            else:
                dur = self.tl_engine._get_audio_duration(path)
                self.tl_engine.add_clip(source_path=path, track=target_track, start=drop_time,
                                         duration=dur, label=name)

            self.append_chat("Editor", f"📥 Añadido '{name}' a la pista {target_track} en {drop_time:.1f}s")
            self._draw_timeline()
        else:
            # Drop fuera del timeline pero fuera del Media Pool -> comportamiento legacy
            widget_y = event.y_root - self.media_listbox.winfo_rooty()
            widget_x = event.x_root - self.media_listbox.winfo_rootx()
            if widget_y > self.media_listbox.winfo_height() or widget_x > self.media_listbox.winfo_width() or widget_y < 0:
                is_video_type = is_video or is_image
                if is_video_type:
                    self._raw_video_path = path
                    self.tl_engine.auto_load_video(path)
                    self._load_video_vlc(path)
                    self.append_chat("Editor", f"📹 Video base reemplazado: {name}")
                else:
                    track = "A1" if "tts" in name.lower() or "audio_" in name.lower() else "A2"
                    start = self.tl_engine.total_duration
                    dur = self.tl_engine._get_audio_duration(path)
                    self.tl_engine.add_clip(source_path=path, track=track, start=start,
                                             duration=dur, label=name)
                    self.append_chat("Editor", f"🎵 Audio añadido a {track}: {name}")
                self._draw_timeline()

        self._drag_media_idx = None

    # ─── Fullscreen Video ───

    def _toggle_fullscreen(self):
        """Abre o cierra una ventana de pantalla completa con VLC."""
        if self._fullscreen_win and self._fullscreen_win.winfo_exists():
            # Sacar de fullscreen y re-embeber en el preview principal
            self._fullscreen_win.destroy()
            self._fullscreen_win = None
            if self._vlc_player:
                self._embed_vlc_player()
            return

        if not self._vlc_player or not self._raw_video_path:
            self.append_chat("Editor", "⚠ Importa un video primero.")
            return

        self._fullscreen_win = tk.Toplevel(self)
        self._fullscreen_win.title("KR-STUDIO — Preview")
        self._fullscreen_win.configure(bg="#000000")
        self._fullscreen_win.attributes("-fullscreen", True)
        self._fullscreen_win.bind("<Escape>", lambda e: self._toggle_fullscreen())

        fs_frame = tk.Frame(self._fullscreen_win, bg="#000000")
        fs_frame.pack(fill="both", expand=True)
        self._fullscreen_win.update_idletasks()

        # Re-embeber VLC en la ventana fullscreen
        wid = fs_frame.winfo_id()
        if wid and self._vlc_player:
            self._vlc_player.set_xwindow(wid)

    def _manual_render(self):
        """Modo Manual: exportar proyecto timeline completo."""
        self._do_render()

    def _auto_record_and_render(self):
        """Modo Auto: graba pantalla + ejecuta director + renderiza."""
        json_data = self._parse_editor_json()
        if json_data is None:
            return

        if not self.wid_b:
            self.append_chat("Error", "❌ No hay Terminal B.")
            return

        self.render_status.configure(text="🤖 Auto-grabando...")
        self.btn_auto_render.configure(state="disabled")

        import threading
        threading.Thread(target=self._auto_thread, args=(json_data,), daemon=True).start()

    def _auto_thread(self, json_data):
        """Thread de grabación automática + renderizado."""
        try:
            from kr_studio.core.record_engine import ScreenRecorder

            recorder = ScreenRecorder(self.workspace_dir)
            wid = self.wid_b

            self.after(0, self.render_status.configure, {"text": "🔴 Grabando..."})

            # Iniciar grabación
            recorder.start(wid)
            time.sleep(1.0)

            # Ejecutar director según modo seleccionado
            mode = self.post_mode_var.get()
            
            if mode == "SOLO TERM":
                from kr_studio.core.solo_director import SoloDirectorEngine
                topic = self._get_last_user_topic() or "Test"
                director = SoloDirectorEngine(self.master_app, topic, self.video_duration_min, self.workspace_dir)
                director.wid_b = self.wid_b
            else:
                from kr_studio.core.director import DirectorEngine
                director = DirectorEngine(self, json_data, self.workspace_dir)
                director.wid_a = self.wid_a
                director.wid_b = self.wid_b
                
            director.typing_delay = self.typing_speed_pct
            director.floating_ctrl = self._floating_ctrl

            director._start_wall = time.monotonic()
            
            if mode == "SOLO TERM":
                # En SOLO, inyectamos JSON en tiempo real a Terminal B
                director.on_json_terminal_b = self._inject_json_editor_b
                director._run_solo_sequence()
            else:
                director._run_sequence()

            # Detener grabación
            video_path = recorder.stop()
            time.sleep(0.5)

            # Guardar timestamps
            self.timestamps = director.timestamps
            self.after(0, self._draw_timeline, self.timestamps)

            # Renderizar
            self.after(0, self.render_status.configure, {"text": "🎬 Renderizando..."})
            self._do_render(video_path)

        except Exception as e:
            self.after(0, self.render_status.configure, {"text": f"❌ Error: {e}"})
        finally:
            self.after(0, self.btn_auto_render.configure, {"state": "normal"})

    def _show_render_progress_ui(self):
        """Muestra una ventana modal flotante para el progreso de renderizado."""
        if hasattr(self, "_render_win") and self._render_win and self._render_win.winfo_exists():
            return self._render_win, self._render_lbl, self._render_bar

        self._render_win = ctk.CTkToplevel(self)
        self._render_win.title("Exportando Video...")
        # Hacer la ventana más alta para acomodar el log
        self._render_win.geometry("500x350")
        self._render_win.resizable(False, False)
        self._render_win.transient(self)
        
        self.after(100, lambda: self._render_win.grab_set() if self._render_win.winfo_exists() else None)

        self.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() // 2) - 250
        y = self.winfo_rooty() + (self.winfo_height() // 2) - 175
        self._render_win.geometry(f"+{x}+{y}")

        title_lbl = ctk.CTkLabel(self._render_win, text="🎬 Renderizando Composición Final", 
                                font=("JetBrains Mono", 14, "bold"), text_color="#1abc9c")
        title_lbl.pack(pady=(15, 5))

        self._render_lbl = ctk.CTkLabel(self._render_win, text="Preparando recursos...", 
                                      font=("JetBrains Mono", 11), text_color="#a9b1d6")
        self._render_lbl.pack(pady=5)

        self._render_bar = ctk.CTkProgressBar(self._render_win, width=450, 
                                            progress_color="#2ecc71", fg_color="#1a1b26")
        self._render_bar.pack(pady=10)
        self._render_bar.set(0)

        # Consola de logs integrada
        self._render_log_txt = ctk.CTkTextbox(self._render_win, width=450, height=180,
                                            font=("JetBrains Mono", 10),
                                            fg_color="#0f0f14", text_color="#a9b1d6",
                                            state="disabled")
        self._render_log_txt.pack(pady=(0, 10))

        # Prevenir cierre manual (forzar esperar)
        self._render_win.protocol("WM_DELETE_WINDOW", lambda: None)
        
        self._render_win.update_idletasks()
        self._render_win.update()
        
        return self._render_win, self._render_lbl, self._render_bar

    def _update_render_progress(self, pct, msg):
        """Callback llamado por VideoEngine desde otro thread."""
        try:
            if hasattr(self, "_render_lbl") and self._render_lbl.winfo_exists():
                if pct is not None:
                    self.after(0, self._render_bar.set, float(pct) / 100.0)
                    self.after(0, self._render_lbl.configure, {"text": f"Progreso: {pct:.1f}%"})
                
                # Si hay mensaje, agregarlo al textbox (ignorar los mensajes repetitivos de TqdmCapture en el log principal si pct existe)
                if msg is not None and hasattr(self, "_render_log_txt") and self._render_log_txt.winfo_exists():
                    def append_log():
                        self._render_log_txt.configure(state="normal")
                        self._render_log_txt.insert("end", str(msg) + "\n")
                        self._render_log_txt.see("end")
                        self._render_log_txt.configure(state="disabled")
                    self.after(0, append_log)
        except Exception:
            pass

    def _do_render(self, source_path_not_used=None):
        """Renderiza la composición final desde TImelineEngine directamente."""
        # Validar si hay clips
        if not self.tl_engine.clips:
            self.append_chat("Error", "❌ El Timeline está vacío. Agrega medios antes de exportar.")
            return

        self.btn_manual_render.configure(state="disabled")
        self._show_render_progress_ui()

        # Extraer UI values en MAiN THREAD para evitar deadlocks de Tkinter en threads
        resolution = self.res_combo.get() if hasattr(self, 'res_combo') else "1080p"
        preset = self.quality_combo.get() if hasattr(self, 'quality_combo') else "medium"

        # Lanzar en thread con un pequeño delay para asegurar pintar la UI
        import threading
        self.after(500, lambda: threading.Thread(target=self._render_thread_worker, args=(resolution, preset), daemon=True).start())

    def _render_thread_worker(self, resolution, preset):
        try:
            from kr_studio.core.video_engine import VideoEngine

            engine = VideoEngine(self.workspace_dir)
            
            # Crear nombre único con timestamp para no sobreescribir
            import time as _time
            ts = _time.strftime("%Y%m%d_%H%M%S")
            exports_dir = os.path.join(self.workspace_dir, "exports")
            os.makedirs(exports_dir, exist_ok=True)
            output_path = os.path.join(exports_dir, f"VIRAL_REEL_{ts}.mp4")

            # Enviar los clips y duración al VideoEngine multipista
            total_dur = self.tl_engine.total_duration
            if total_dur <= 0:
                raise Exception("Duración del timeline es 0s.")

            self.after(0, self.append_chat, "Editor", f"🚀 Iniciando exportación Multipista a {resolution} ({preset})...")

            result = engine.render_timeline(
                clips_data=self.tl_engine.clips,
                total_duration=total_dur,
                output_path=output_path,
                resolution=resolution,
                preset=preset,
                progress_callback=self._update_render_progress
            )

            # Destruir ventana modal
            self._safe_destroy_render_win()

            if result:
                size_mb = os.path.getsize(result) / (1024 * 1024)
                self.after(0, self.render_status.configure,
                          {"text": f"✅ {os.path.basename(result)} ({size_mb:.1f} MB)"})
                self.after(0, self.append_chat, "Sistema",
                          f"✅ Video exportado exitosamente:\n{result}\nTamaño: {size_mb:.1f} MB")
            else:
                self.after(0, self.render_status.configure, {"text": "❌ Error en renderizado"})
                self.after(0, self.append_chat, "Error", "Fallo durante la exportación. Revisa la consola.")

        except Exception as e:
            import traceback
            traceback.print_exc()
            self._safe_destroy_render_win()
            self.after(0, self.render_status.configure, {"text": f"❌ Error: {str(e)[:50]}"})
            self.after(0, self.append_chat, "Error", f"Fallo Crítico Render: {e}")
        finally:
            # SIEMPRE re-habilitar el botón de exportar
            try:
                self.after(0, self._re_enable_render_btn)
            except Exception:
                pass

    def _safe_destroy_render_win(self):
        """Destruye la ventana de progreso de render de forma segura."""
        try:
            if hasattr(self, "_render_win") and self._render_win and self._render_win.winfo_exists():
                self.after(0, self._render_win.destroy)
        except Exception:
            pass

    def _re_enable_render_btn(self):
        """Re-habilita el botón de exportar (llamado desde el main thread)."""
        try:
            self.btn_manual_render.configure(state="normal")
        except Exception:
            pass

    def _on_speed_change(self, value):
        self.typing_speed_pct = int(value)
        self.speed_label.configure(text=f"{self.typing_speed_pct}%")

    def _on_duration_change(self, value):
        self.video_duration_min = int(value)
        self.duration_label.configure(text=f"{self.video_duration_min} min")

    # ═══════════════════════════════════════════════
    # OSINT RADAR — Búsqueda de Tendencias en Vivo
    # ═══════════════════════════════════════════════

    def osint_search(self):
        """Busca tendencias de ciberseguridad en vivo."""
        if not self.ai:
            self.append_chat("Error", "❌ Conecta la API Key primero.")
            return
        self.append_chat("Sistema", "🌐 Buscando tendencias de ciberseguridad en vivo...")
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
                    titulo = t.get("titulo", "Sin título")
                    desc = t.get("descripcion", "")
                    fuente = t.get("fuente", "")
                    msg += f"  {i}. {titulo}\n     {desc}\n     📌 {fuente}\n\n"
                msg += "💡 Escribe el número o el tema en el chat para generar un guion."
                self.after(0, self.append_chat, "OSINT", msg)
            else:
                self.after(0, self.append_chat, "OSINT", "⚠ No se encontraron tendencias. Intenta de nuevo.")
        except Exception as e:
            self.after(0, self._stop_processing_animation)
            self.after(0, self.btn_osint.configure, {"state": "normal"})
            self.after(0, self.append_chat, "Error", f"❌ Error OSINT: {e}")

    # ═══════════════════════════════════════════════
    # MODO DINÁMICO
    # ═══════════════════════════════════════════════

    def launch_dynamic(self):
        """Lanza el Director Dinámico — ciclos alternos Terminal A ↔ B."""
        self.ensure_terminals_open(self._launch_dynamic_internal, mode="dual")

    def _launch_dynamic_internal(self):
        if not self.wid_a or not self.wid_b:
            self.append_chat("Error", "❌ No hay terminales detectadas u ocurrió un error al abrirlas.")
            return

        if not self.ai or not self.ai.chat_session:
            self.append_chat("Error", "❌ Conecta la API Key primero.")
            return

        # Obtener el tema del último mensaje del chat o usar default
        topic = self._get_last_user_topic()
        if not topic:
            topic = "Modo Dinámico"

        duration = self.video_duration_min
        self.append_chat("Sistema",
                         f"🚀 MODO DINÁMICO\n"
                         f"  Tema: {topic}\n"
                         f"  Duración: {duration} min\n"
                         f"  Ciclos: {max(2, duration // 3)}\n"
                         f"  Terminal A: kr-clidn chat\n"
                         f"  Terminal B: ejecución de comandos")

        self._active_director = DynamicDirectorEngine(
            self, topic, duration, self.workspace_dir
        )
        self._active_director.wid_a = self.wid_a
        self._active_director.wid_b = self.wid_b
        self._active_director.typing_delay = self.typing_speed_pct
        self._active_director.obs.password = self._load_env_value("OBS_PASSWORD", "")
        self._active_director.ai_engine = self.ai
        self._active_director.floating_ctrl = self._floating_ctrl
        # Conectar callbacks de editores duales
        self._active_director.on_json_terminal_a = self._inject_json_editor_a
        self._active_director.on_json_terminal_b = self._inject_json_editor_b

        self.btn_stop.configure(state="normal")
        self.btn_launch.configure(state="disabled")
        self.btn_record.configure(state="disabled")
        self.btn_dynamic.configure(state="disabled")
        self.btn_solo.configure(state="disabled")

        self._active_director.start()

        # Re-habilitar después de un timeout largo
        self.after(duration * 60 * 1000 + 30000, lambda: self.btn_dynamic.configure(state="normal"))
        self.after(duration * 60 * 1000 + 30000, lambda: self.btn_solo.configure(state="normal"))

    def launch_solo(self):
        """Lanza el Director Solo — solo Terminal B para testeo de herramientas."""
        self.ensure_terminals_open(self._launch_solo_internal, mode="solo")

    def _launch_solo_internal(self):
        from kr_studio.core.solo_director import SoloDirectorEngine

        if not self.wid_b:
            self.append_chat("Error", "❌ No hay Terminal B. Ocurrió un error al abrirla.")
            return

        if not self.ai or not self.ai.chat_session:
            self.append_chat("Error", "❌ Conecta la API Key primero.")
            return

        topic = self._get_last_user_topic()
        if not topic:
            topic = "Modo Solo"

        duration = self.video_duration_min
        wrapper = self.use_wrapper_var.get()
        mode = "KR-CLI Wrapper" if wrapper else "Comandos Limpios"
        target = self.target_combo.get() if hasattr(self, 'target_combo') else "scanme.nmap.org"

        self.append_chat("Sistema",
                         f"⚡ MODO SOLO TERMINAL\n"
                         f"  Tema: {topic}\n"
                         f"  Target: {target}\n"
                         f"  Duración: {duration} min\n"
                         f"  Modo: {mode}\n"
                         f"  Solo Terminal B — sin kr-clidn")

        self._active_director = SoloDirectorEngine(
            self, topic, duration, self.workspace_dir
        )
        self._active_director.wid_b = self.wid_b
        self._active_director.typing_delay = self.typing_speed_pct
        self._active_director.obs.password = self._load_env_value("OBS_PASSWORD", "")
        self._active_director.ai_engine = self.ai
        self._active_director.floating_ctrl = self._floating_ctrl
        self._active_director.use_wrapper = wrapper
        self._active_director.on_json_terminal_b = self._inject_json_editor_b

        # ── Inyectar JSON si hay contenido válido en Editor B ──
        self._active_tab = "b"  # Forzar parseo de laTerminal B
        json_data = self._parse_editor_json()
        if not json_data:
            self.append_chat("Error", "❌ Debes generar un guion o pegar un JSON válido en Editor B primero.")
            return

        self._active_director.json_data = json_data
        self.append_chat("Sistema", f"📌 JSON inyectado: {len(json_data)} escenas")

        self.btn_stop.configure(state="normal")
        self.btn_launch.configure(state="disabled")
        self.btn_record.configure(state="disabled")
        self.btn_dynamic.configure(state="disabled")
        self.btn_solo.configure(state="disabled")

        self._active_director.start()

        timeout_ms = int(duration * 60 * 1000 + 30000)
        self.after(timeout_ms, lambda: self.btn_solo.configure(state="normal"))
        self.after(timeout_ms, lambda: self.btn_dynamic.configure(state="normal"))
        self.after(timeout_ms, lambda: self.btn_launch.configure(state="normal"))
        self.after(timeout_ms, lambda: self.btn_record.configure(state="normal"))

    def _get_last_user_topic(self) -> str:
        """Extrae el tema del último mensaje del usuario en el chat."""
        if hasattr(self, '_last_user_message') and self._last_user_message:
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
        for tag in ("json_key", "json_string", "json_bracket", "json_keyword",
                     "json_colon", "json_number"):
            self.editor.tag_remove(tag, "1.0", "end")

        # Brackets
        for match in re.finditer(r'[\[\]\{\}]', content):
            start_idx = f"1.0+{match.start()}c"
            end_idx = f"1.0+{match.end()}c"
            self.editor.tag_add("json_bracket", start_idx, end_idx)

        # Colons and commas
        for match in re.finditer(r'[:,]', content):
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
        for match in re.finditer(r'\b\d+\b', content):
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

        threading.Thread(target=self._startup_konsole_thread, args=(callback, mode), daemon=True).start()

    def _startup_konsole_thread(self, callback=None, mode="dual"):
        import subprocess as sp

        is_solo = (mode == "solo")
        
        if is_solo:
            self.after(0, self.append_chat, "Sistema",
                       "🖥 Abriendo 1 terminal Konsole...\n"
                       "  Terminal B → Ejecución de comandos (Modo Solo)")
        else:
            self.after(0, self.append_chat, "Sistema",
                       "🖥 Abriendo 2 terminales Konsole...\n"
                       "  Terminal A → KR-CLIDN (dashboard/AI) [KaliRootCLI + venv]\n"
                       "  Terminal B → Ejecución de comandos")
        try:
            if not is_solo:
                # Terminal A: inicia en KaliRootCLI (mantiene shell del usuario)
                sp.Popen([
                    'konsole', '--workdir', '/home/rk13/RK13CODE/KaliRootCLI'
                ], stdout=sp.DEVNULL, stderr=sp.DEVNULL)
                time.sleep(1.5)

            # Terminal B: normal
            sp.Popen(['konsole'], stdout=sp.DEVNULL, stderr=sp.DEVNULL)
            time.sleep(1.5)
        except FileNotFoundError:
            self.after(0, self.append_chat, "Error", "❌ Konsole no encontrado.")
            return

        time.sleep(2.0)
        try:
            result = sp.run(['xdotool', 'search', '--class', 'konsole'],
                            capture_output=True, text=True, timeout=5)
            wids = [w.strip() for w in result.stdout.strip().split('\n') if w.strip()]
            
            if is_solo and len(wids) >= 1:
                self.wid_b = wids[-1]
                self.wid_a = None
            elif not is_solo and len(wids) >= 2:
                self.wid_a = wids[-2]  # Terminal A
                self.wid_b = wids[-1]  # Terminal B
            elif not is_solo and len(wids) == 1:
                self.wid_a = wids[0]
                self.wid_b = wids[0]
                self.after(0, self.append_chat, "Sistema",
                           f"⚠ Solo 1 Konsole encontrada (WID: {self.wid_a}).\nUsando misma terminal para A y B.")
            elif len(wids) == 0:
                self.after(0, self.append_chat, "Sistema", "⚠ Konsoles abiertas pero sin WID detectado.")
                return

            # Obtener formato seleccionado
            formato = self.format_combo.get()
            if "16:9" in formato:
                # 16:9 Horizontal
                geometry = "0,-1,-1,960,540"
                desc_formato = "960x540 (16:9)"
            else:
                # 9:16 Vertical
                geometry = "0,-1,-1,450,800"
                desc_formato = "450x800 (9:16)"

            # Redimensionar y posicionar
            wids_to_resize = [self.wid_b] if is_solo else ([self.wid_a, self.wid_b] if self.wid_a != self.wid_b else [self.wid_a])
            for wid in wids_to_resize:
                if wid:
                    hex_wid = hex(int(wid))
                    sp.run(['wmctrl', '-i', '-r', hex_wid, '-e', geometry],
                           capture_output=True, timeout=5)

            if is_solo:
                self.after(0, self.append_chat, "Sistema",
                           f"✅ Terminal B (WID: {self.wid_b}) — Ejecución\n"
                           f"Ajustada a {desc_formato}. Configura OBS con 'Terminal-B'")
            else:
                self.after(0, self.append_chat, "Sistema",
                           f"✅ Terminal A (WID: {self.wid_a}) — KR-CLIDN\n"
                           f"✅ Terminal B (WID: {self.wid_b}) — Ejecución\n"
                           f"Ambas a {desc_formato}. Configura OBS con 2 escenas:\n"
                           f"  Scene 'Terminal-A' → captura Terminal A\n"
                           f"  Scene 'Terminal-B' → captura Terminal B")

            if callback:
                self.after(1000, callback)
        except Exception as e:
            self.after(0, self.append_chat, "Error", f"⚠ {e}")

    # ═══════════════════════════════════════════════
    # CHAT AI — MENSAJES ELEGANTES
    # ═══════════════════════════════════════════════

    def _connect_obs(self):
        """Conecta a OBS, crea escenas Terminal-A y Terminal-B si no existen."""
        from kr_studio.core.obs_controller import OBSController

        self.append_chat("Sistema", "📺 Conectando a OBS Studio...")
        self._obs = OBSController()
        self._obs.password = self._load_env_value("OBS_PASSWORD", "")

        if not self._obs.connect():
            self.append_chat("Error",
                "❌ No se pudo conectar a OBS.\n"
                "Verifica:\n"
                "  1. OBS está abierto\n"
                "  2. Tools → WebSocket Server Settings → Enable\n"
                "  3. Puerto: 4455\n"
                f"  4. Password: {self._obs.password or '(sin password)'}")
            self.obs_btn.configure(fg_color="#e74c3c")
            return

        # Auto-setup de escenas
        scenes = self._obs._get_scene_names()
        result = self._obs.setup_dual_scenes(
            self.wid_a or "0", self.wid_b or "0"
        )

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
            self.append_chat("Sistema", "✅ API Key conectada y guardada en .env — DOMINION listo.")
            # Ocultar la barra de API tras guardar exitosamente
            if hasattr(self, '_api_bar'):
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
                        lines.append(f'GEMINI_API_KEY={key}\n')
                        found = True
                    else:
                        lines.append(line)
        if not found:
            lines.append(f'GEMINI_API_KEY={key}\n')
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

        threading.Thread(target=self._process_chat, args=(user_text,), daemon=True).start()

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
        self.status_label.configure(text="● EN LÍNEA", text_color=COLORS["accent_green"])

    def _process_chat(self, prompt: str):
        try:
            mode = self.pre_mode_var.get() if self.pre_mode_var else "DUAL AI"
            target_editor = "Editor B" if mode == "SOLO TERM" else "Editor A"
            self._active_tab = "b" if mode == "SOLO TERM" else "a"
            
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
                    "  {\"tipo\": \"narracion\", \"voz\": \"Texto a hablar\"},\n"
                    "  {\"tipo\": \"ejecucion\", \"comando_visual\": \"nmap -sV target\", \"voz\": \"Explicación en audio...\"}\n"
                    "]\n"
                    "El JSON debe contener toda la interacción técnica directa con la terminal."
                )

            # Inyectar el target legal seleccionado
            target = self.target_combo.get() if hasattr(self, 'target_combo') else "scanme.nmap.org"
            
            # Detectar si el usuario pide modificar o quiere un tema nuevo
            mod_keywords = ["modifica", "cambia", "agrega", "elimina", "quita", "pon", "ajusta", "corrige", "actualiza", "en la escena", "reemplaza"]
            is_modification = any(k in prompt.lower() for k in mod_keywords)

            # Si es un tema completamente nuevo, limpiar el directorio de audios viejos para evitar superposiciones
            if not is_modification and mode == "SOLO TERM":
                import shutil
                audio_dir = os.path.join(self.workspace_dir, "audio_solo")
                if os.path.exists(audio_dir):
                    shutil.rmtree(audio_dir, ignore_errors=True)
                os.makedirs(audio_dir, exist_ok=True)

            # Leer parámetros de duración y velocidad (Delay) de la UI
            dur_mins = int(self.duration_slider.get()) if hasattr(self, 'duration_slider') else 5
            speed_delay = int(self.speed_slider.get()) if hasattr(self, 'speed_slider') else 80
            
            # Dinamismo de tamaño basado en duración solicitada
            escenas_aprox = dur_mins * 6 # Estimación ruda de escenas por minuto
            dur_instruction = (
                f"\n\n[PARAMETROS DE DURACION Y VELOCIDAD]\n"
                f"- El usuario ha solicitado que este video dure aproximadamente {dur_mins} minuto(s).\n"
                f"- Genera un JSON profundo y desarrollado que abarque este tiempo (aprox {escenas_aprox} escenas ricas en contenido y narración). Si es 1 minuto, hazlo directo y rápido (tipo TikTok/Reel, 5-8 escenas). Si son 5-10 minutos o más, profundiza con múltiples comandos, análisis exhaustivo, y ejemplos prácticos variados.\n"
                f"- La velocidad de tipeo actual (Delay) está configurada a {speed_delay}ms por tecla.\n"
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
                resumen_voces = " | ".join(voces[:5])  # Primeras 5 narraciones

                seo_prompt = (
                    f"Eres un experto en SEO y marketing viral para redes sociales (TikTok, YouTube Shorts, Instagram Reels).\n"
                    f"El usuario creó un video de ciberseguridad/hacking ético sobre: {prompt}\n"
                    f"Contexto del guion: {resumen_voces[:500]}\n\n"
                    f"Genera EXACTAMENTE este JSON (sin markdown, sin explicaciones):\n"
                    f'{{"titulo": "Título viral SEO (máx 60 chars, con emoji, que retenga y genere curiosidad)", '
                    f'"descripcion": "Descripción optimizada para SEO (máx 150 chars, con keywords naturales y CTA)", '
                    f'"hashtags": "#tag1 #tag2 #tag3 ... (15-20 hashtags relevantes para ciberseguridad, trending, en español e inglés)"}}\n'
                    f"IMPORTANTE: El título DEBE ser clickbait profesional que retenga. Los hashtags DEBEN incluir keywords de búsqueda populares."
                )

                response = self.ai.chat(seo_prompt)
                text = response.strip()
                # Limpiar markdown
                text = re.sub(r'```json\s*', '', text)
                text = re.sub(r'```\s*', '', text)
                text = text.strip()

                seo_data = json.loads(text)

                def _apply():
                    self.meta_title.delete(0, "end")
                    self.meta_title.insert(0, seo_data.get("titulo", prompt[:60]))
                    
                    self.meta_desc.delete("1.0", "end")
                    self.meta_desc.insert("end", seo_data.get("descripcion", ""))

                    self.meta_tags.delete(0, "end")
                    self.meta_tags.insert(0, seo_data.get("hashtags", "#cybersecurity #hacking"))

                    self.append_chat("Sistema", "🔍 Metadatos SEO generados por IA — listos para copiar.")

                self.after(0, _apply)

            except Exception as e:
                # Fallback básico
                def _fallback():
                    self.meta_title.delete(0, "end")
                    self.meta_title.insert(0, f"🔒 {prompt[:55].title()}")
                    self.meta_desc.delete("1.0", "end")
                    first_voz = next((s.get("voz", "") for s in json_data if s.get("voz")), "")
                    self.meta_desc.insert("end", first_voz[:150])
                    self.meta_tags.delete(0, "end")
                    self.meta_tags.insert(0, "#cybersecurity #kalilinux #hacking #ethicalhacking #DOMINION #infosec")
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
        threading.Thread(target=self._generate_audios_thread,
                         args=(json_data,), daemon=True).start()

    def _generate_audios_thread(self, json_data: list):
        audio_engine = AudioEngine()
        total = len(json_data)
        errores = 0
        
        mode = self.pre_mode_var.get() if self.pre_mode_var else "DUAL AI"
        is_solo = (mode == "SOLO TERM")
        if is_solo:
            os.makedirs(os.path.join(self.workspace_dir, "audio_solo"), exist_ok=True)

        import hashlib

        for idx, escena in enumerate(json_data):
            voz = escena.get("voz", "")
            if not voz:
                continue
                
            text_hash = hashlib.md5(voz.encode('utf-8')).hexdigest()[:8]
            
            if is_solo:
                path = os.path.join(self.workspace_dir, "audio_solo", f"audio_{idx}_{text_hash}.mp3")
            else:
                path = os.path.join(self.workspace_dir, f"audio_{idx}_{text_hash}.mp3")
                
            if os.path.exists(path):
                self.after(0, self.append_chat, "TTS", f"Audio {idx+1}/{total} — Cache [OK]")
                continue

            try:
                dur = audio_engine.generar_audio(voz, path)
                self.after(0, self.append_chat, "TTS", f"Audio {idx+1}/{total} — {dur:.1f}s")
            except Exception as e:
                errores += 1
                self.after(0, self.append_chat, "Error", f"❌ Info TTS {idx+1}: {e}")

        msg = "✅ Todos los audios listos." if errores == 0 else f"⚠ {errores} error(es)."
        self.after(0, self.append_chat, "Sistema", msg)
        self.after(0, lambda: self.btn_tts.configure(state="normal"))

    # ═══════════════════════════════════════════════
    # LANZAR KONSOLE + XDOTOOL
    # ═══════════════════════════════════════════════

    def launch_konsole(self):
        """Lanza la secuencia dual SIN grabación OBS."""
        self.ensure_terminals_open(lambda: self._launch_director(auto_record=False), mode="dual")

    def launch_and_record(self):
        """Lanza la secuencia dual CON grabación OBS automática."""
        self.ensure_terminals_open(lambda: self._launch_director(auto_record=True), mode="dual")

    def _launch_director(self, auto_record=False):
        json_data = self._parse_editor_json()
        if json_data is None:
            return

        is_solo = getattr(self, "_active_tab", "a") == "b"
        mode_name = "SOLO" if is_solo else "DUAL"
        mode_txt = "+ OBS GRABANDO" if auto_record else "sin grabación"
        
        self.append_chat("Sistema", f"🎬 Lanzando secuencia {mode_name} ({mode_txt}, tipeo: {self.typing_speed_pct}%)...")
        self.btn_launch.configure(state="disabled")
        self.btn_record.configure(state="disabled")
        self.btn_solo.configure(state="disabled")
        self.btn_dynamic.configure(state="disabled")

        if is_solo:
            from kr_studio.core.solo_director import SoloDirectorEngine
            topic = self._get_last_user_topic() or "Modo Solo"
            self._active_director = SoloDirectorEngine(self.master_app, topic, self.video_duration_min, self.workspace_dir)
            
            self._active_director.json_data = json_data
            self._active_director.wid_b = self.wid_b
            self._active_director.typing_delay = self.typing_speed_pct
            self._active_director.obs.password = self._load_env_value("OBS_PASSWORD", "")
            if not auto_record:
                self._active_director.obs = type('MockOBS', (), {'connect': lambda s: False, 'connected': False})()
            self._active_director.floating_ctrl = self._floating_ctrl
            
        else:
            self._active_director = DirectorEngine(self, json_data, self.workspace_dir)
            self._active_director.wid_a = self.wid_a
            self._active_director.wid_b = self.wid_b
            self._active_director.typing_delay = self.typing_speed_pct
            self._active_director.obs.password = self._load_env_value("OBS_PASSWORD", "")

            if not auto_record:
                # Desactivar OBS para modo sin grabación
                self._active_director.obs = type('MockOBS', (), {'connect': lambda s: False, 'connected': False})()

            # Pasar referencia del widget flotante ANTES de iniciar
            self._active_director.floating_ctrl = self._floating_ctrl

        self._active_director.start()

        # Activar botón Detener, desactivar Lanzar/Grabar
        self.btn_stop.configure(state="normal")
        
        # Calcular timeout de bloqueo basado en la duración solicitada + 30 seg de gracia
        timeout_ms = int(self.video_duration_min * 60 * 1000 + 30000)
        self.after(timeout_ms, lambda: self.btn_launch.configure(state="normal"))
        self.after(timeout_ms, lambda: self.btn_record.configure(state="normal"))
        self.after(timeout_ms, lambda: self.btn_solo.configure(state="normal"))
        self.after(timeout_ms, lambda: self.btn_dynamic.configure(state="normal"))

    def stop_director(self):
        """Detiene la secuencia del Director inmediatamente."""
        if self._active_director and self._active_director.is_running:
            self._active_director.stop()
            self.append_chat("Sistema", "⏹ Secuencia detenida por el usuario.")
        self.btn_stop.configure(state="disabled")
        self.btn_launch.configure(state="normal")
        self.btn_record.configure(state="normal")
        self.btn_solo.configure(state="normal")
        self.btn_dynamic.configure(state="normal")

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

        self.project_name_label.configure(text=f"📁 {title}", text_color=COLORS["accent_cyan"])
        self.append_chat("Sistema", f"💾 Proyecto guardado: {title}/guion.json")

    def load_project(self):
        """Abre un diálogo para cargar un proyecto existente."""
        filepath = filedialog.askopenfilename(
            initialdir=self.projects_dir,
            title="Cargar Guion",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if not filepath:
            return

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, list):
                self.append_chat("Error", "⚠ El archivo no contiene un arreglo JSON válido.")
                return

            json_str = json.dumps(data, indent=4, ensure_ascii=False)
            self.editor.delete("1.0", "end")
            self.editor.insert("end", json_str)
            self._update_editor()

            # Actualizar label del proyecto
            folder_name = os.path.basename(os.path.dirname(filepath))
            self.project_name_label.configure(text=f"📁 {folder_name}",
                                               text_color=COLORS["accent_cyan"])
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
            self.project_name_label.configure(text=f"📁 {title}",
                                               text_color=COLORS["accent_cyan"])
        except Exception:
            pass

    def _extract_project_title(self, json_data: list) -> str:
        """Extrae un título legible del contenido del guion."""
        for scene in json_data:
            text = scene.get("comando_visual", "") or scene.get("voz", "")
            if text:
                # Limpiar y truncar
                clean = re.sub(r'[^\w\s\-]', '', text).strip()
                clean = clean[:40].strip()
                if clean:
                    return clean.replace(" ", "_")
        return f"guion_{int(time.time())}"

    # ═══════════════════════════════════════════════
    # UTILIDADES
    # ═══════════════════════════════════════════════

    def _parse_editor_json(self):
        # El tab activo se guarda en self._active_tab ("a" o "b")
        if getattr(self, "_active_tab", "a") == "b":
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
