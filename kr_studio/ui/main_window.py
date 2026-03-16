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
from kr_studio.ui.components.config_panel import ConfigPanel  # type: ignore
from kr_studio.ui.theme import COLORS  # type: ignore
from kr_studio.core.master_director import MasterDirector, DirectorMode  # type: ignore
from kr_studio.core.video_templates import (
    get_template_list,
    get_presenter_list,
    get_audience_list,
)  # type: ignore


class MainWindow(ctk.CTkFrame):  # type: ignore
    def __init__(self, master_app):
        super().__init__(master_app, fg_color=COLORS["bg_dark"])  # type: ignore
        self.master_app = master_app
        self.pack(fill="both", expand=True)

        self._base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self._env_path = os.path.join(os.path.dirname(self._base_dir), ".env")

        # Inicializar los motores y gestores principales
        self.task_manager = TaskManager()
        self.ai = AIEngine("")
        self.action_handler = ActionHandler(self)
        self.workspace_dir = os.path.join(self._base_dir, "workspace")
        self.projects_dir = os.path.join(self._base_dir, "projects")
        os.makedirs(self.workspace_dir, exist_ok=True)
        os.makedirs(self.projects_dir, exist_ok=True)

        # Cargar preferencias guardadas
        self.typing_speed_pct = 80
        self.video_duration_min = 5
        self._load_ui_preferences()
        self.wid_a: typing.Optional[str] = None
        self.wid_b: typing.Optional[str] = None
        self._anim_id = None
        self._floating_ctrl: typing.Optional[FloatingControl] = None

        from kr_studio.core.series_orchestrator import SeriesOrchestrator  # type: ignore

        self.series_orchestrator = SeriesOrchestrator(self.ai, self.workspace_dir)  # type: ignore

        self.video_duration_min = 5
        self.use_wrapper_var: typing.Optional[ctk.BooleanVar] = (
            None  # Se crea en _build_editor_panel
        )
        self.timestamps: typing.Dict[str, typing.Any] = {}
        self.pre_mode_var: typing.Optional[ctk.StringVar] = (
            None  # Se crea en _build_chat_panel
        )
        self._raw_video_path: typing.Optional[str] = None

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
            corner_radius=8,
        )
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=6, pady=(0, 6))

        self.tab1 = self.tabview.add("🎬 Guion y Director")
        self.tab2 = self.tabview.add("🎬 Orquestador de Series")
        self.tab3 = self.tabview.add("🎙 Estudio TTS")

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

        # Tab 3 — Estudio TTS
        self.tab3.grid_rowconfigure(1, weight=1)
        self.tab3.grid_columnconfigure(0, weight=1)
        self.tab3.grid_columnconfigure(1, weight=2)
        self._build_tts_studio()

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
                self.append_chat(
                    "Sistema",
                    "Bienvenido a KR-STUDIO 🎬\nAPI Key cargada desde .env — DOMINION listo.",
                )
                # Ocultar barra de API al cargar después de un pequeño delay visual
                self.after(800, lambda: self._api_bar.grid_forget())
            except Exception:
                self.append_chat(
                    "Sistema",
                    "Bienvenido a KR-STUDIO 🎬\n⚠ API Key en .env inválida. Ingresa una nueva.",
                )
        else:
            self.append_chat(
                "Sistema",
                "Bienvenido a KR-STUDIO 🎬\nIDE de Producción de Videos — DOMINION Edition\nIngresa tu API Key para comenzar.",
            )

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

        # Botón OSINT Radar
        self.btn_osint = ctk.CTkButton(
            header,
            text="🌐 Radar OSINT",
            command=self.osint_search,
            font=("JetBrains Mono", 10, "bold"),
            fg_color="#FF6D00",
            hover_color="#E65100",
            text_color="#000000",
            width=120,
            height=30,
        )
        self.btn_osint.pack(side="right", padx=(0, 6))

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

        # Chat display
        self.chat_display = ctk.CTkTextbox(
            panel,
            wrap="word",
            font=("JetBrains Mono", 12),
            fg_color=COLORS["bg_chat"],
            text_color=COLORS["text_primary"],
            state="disabled",
            border_width=0,
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
            "sender_error", foreground=COLORS["accent_magenta"]
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
            panel, fg_color=COLORS["header_bg"], height=42, corner_radius=0
        )
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)

        ctk.CTkLabel(header, text="📝", font=("Arial", 18)).pack(
            side="left", padx=(12, 4)
        )
        ctk.CTkLabel(
            header,
            text="EDITOR DE GUION",
            font=("JetBrains Mono", 13, "bold"),
            text_color=COLORS["accent_cyan"],
        ).pack(side="left")

        # ── Editor DUAL con pestañas (row 1 — SE EXPANDE) ──
        editor_tabs_frame = ctk.CTkFrame(panel, fg_color="transparent")
        editor_tabs_frame.grid(row=1, column=0, sticky="nsew", padx=6, pady=(2, 6))
        editor_tabs_frame.grid_rowconfigure(1, weight=1)
        editor_tabs_frame.grid_columnconfigure(0, weight=1)

        # Tab buttons
        tab_bar = ctk.CTkFrame(
            editor_tabs_frame, fg_color=COLORS["header_bg"], height=30
        )
        tab_bar.grid(row=0, column=0, sticky="ew")
        tab_bar.grid_propagate(False)

        self._active_tab = "a"
        self.tab_btn_a = ctk.CTkButton(
            tab_bar,
            text="📝 Terminal A (Chat)",
            command=lambda: self._switch_editor_tab("a"),
            font=("JetBrains Mono", 10, "bold"),
            fg_color=COLORS["accent_cyan"],
            text_color="#000000",
            hover_color="#00b8d4",
            width=140,
            height=24,
        )
        self.tab_btn_a.pack(side="left", padx=(4, 2), pady=3)

        self.tab_btn_b = ctk.CTkButton(
            tab_bar,
            text="⚡ Terminal B (Cmds)",
            command=lambda: self._switch_editor_tab("b"),
            font=("JetBrains Mono", 10, "bold"),
            fg_color="#1a1b2e",
            text_color=COLORS["text_dim"],
            hover_color="#252640",
            width=140,
            height=24,
        )
        self.tab_btn_b.pack(side="left", padx=2, pady=3)

        # Editor container (switchable)
        editor_stack = ctk.CTkFrame(editor_tabs_frame, fg_color="transparent")
        editor_stack.grid(row=1, column=0, sticky="nsew")

        # ── Editor A (Terminal A / Chat) ──
        self.editor_container_a = ctk.CTkFrame(editor_stack, fg_color="transparent")
        self.editor_container_a.pack(fill="both", expand=True)

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

        self.editor.bind("<KeyRelease>", lambda e: self.after(100, self._update_editor))
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
            text_color=COLORS["accent_magenta"],
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

        ctk.CTkLabel(
            format_row,
            text="📐 Formato:",
            font=("JetBrains Mono", 10, "bold"),
            text_color=COLORS["text_dim"],
        ).pack(side="left")

        self.format_combo = ctk.CTkOptionMenu(
            format_row,
            values=["9:16 (Vertical)", "16:9 (Horizontal)"],
            font=("JetBrains Mono", 11),
            fg_color=COLORS["border"],
            button_color=COLORS["accent_magenta"],
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
            button_color="#E040FB",
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

        self.use_wrapper_var = ctk.BooleanVar(value=False)
        self.wrapper_check = ctk.CTkCheckBox(
            controls,
            text="🔲 KR-CLI Wrapper (Terminal B)",
            variable=self.use_wrapper_var,
            font=("JetBrains Mono", 10),
            text_color=COLORS["text_dim"],
            fg_color=COLORS["accent_magenta"],
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
            self.editor_container_a.pack(fill="both", expand=True)
            self.tab_btn_a.configure(
                fg_color=COLORS["accent_cyan"], text_color="#000000"
            )
            self.tab_btn_b.configure(fg_color="#1a1b2e", text_color=COLORS["text_dim"])
        else:
            self.editor_container_a.pack_forget()
            self.editor_container_b.pack(fill="both", expand=True)
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
            button_color="#E040FB",
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
        voice_dir = os.path.join(self.workspace_dir, "voces_manuales")
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
        series_dir = getattr(self.series_orchestrator, "_series_dir", None)
        if series_dir:
            try:
                tab = self.chapters_tabview.get()
                tab_safe = re.sub(r"[^a-zA-Z0-9_\-]", "_", tab.lower())
                audio_dir = os.path.join(series_dir, tab_safe, "audio")
            except Exception:
                audio_dir = os.path.join(series_dir, "audio_batch")
        else:
            audio_dir = os.path.join(self.workspace_dir, "voces_manuales", "batch")
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
        voice_dir = os.path.join(self.workspace_dir, "voces_manuales")
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

        d = os.path.join(self.workspace_dir, "voces_manuales")
        os.makedirs(d, exist_ok=True)
        _sp.Popen(["xdg-open", d])

    def _build_postprod_tab(self):
        """Pestaña 2: Orquestador de Series y Películas. Genera N capítulos secuencialmente."""
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
        ctk.CTkLabel(lh, text="📚", font=("Arial", 18)).pack(side="left", padx=(12, 4))
        ctk.CTkLabel(
            lh,
            text="PLANIFICADOR DE SERIE",
            font=("JetBrains Mono", 12, "bold"),
            text_color=COLORS["accent_cyan"],
        ).pack(side="left")

        # Controles
        ctrl_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        ctrl_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(
            ctrl_frame,
            text="Tema Principal de la Serie:",
            font=("JetBrains Mono", 10, "bold"),
            text_color=COLORS["text_dim"],
        ).pack(anchor="w", pady=(0, 2))
        self.series_topic_entry = ctk.CTkEntry(
            ctrl_frame,
            placeholder_text="Ej: Curso de Hacking Ético con Nmap...",
            font=("JetBrains Mono", 11),
            fg_color=COLORS["bg_dark"],
            border_color=COLORS["border"],
        )
        self.series_topic_entry.pack(fill="x", pady=(0, 8))

        # Selector de Modo
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
            values=["DUAL AI", "SOLO TERM"],
            variable=self.orchestrator_mode_var,
            selected_color=COLORS["accent_cyan"],
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
            selected_color="#7B1FA2",
            selected_hover_color="#6A1B9A",
            unselected_color=COLORS["bg_dark"],
            unselected_hover_color="#2a2b3e",
            text_color=COLORS["text_primary"],
            font=("JetBrains Mono", 10, "bold"),
        )
        self.orchestrator_format_seg.pack(
            side="right", fill="x", expand=True, padx=(10, 0)
        )

        # Fila para # Capítulos y Botón Generar
        row2 = ctk.CTkFrame(ctrl_frame, fg_color="transparent")
        row2.pack(fill="x")

        ctk.CTkLabel(
            row2,
            text="# Capítulos:",
            font=("JetBrains Mono", 10, "bold"),
            text_color=COLORS["text_dim"],
        ).pack(side="left")
        self.series_chapters_var = ctk.StringVar(value="5")
        self.series_chapters_combo = ctk.CTkComboBox(
            row2,
            values=[str(i) for i in range(1, 21)],
            variable=self.series_chapters_var,
            width=60,
            font=("JetBrains Mono", 11),
            fg_color=COLORS["bg_dark"],
            border_color=COLORS["border"],
        )
        self.series_chapters_combo.pack(side="left", padx=(4, 10))

        self.btn_generate_master = ctk.CTkButton(
            row2,
            text="✨ Generar Estructura",
            command=self._generate_master_structure,
            font=("JetBrains Mono", 10, "bold"),
            fg_color="#7B1FA2",
            hover_color="#6A1B9A",
        )
        self.btn_generate_master.pack(side="right", fill="x", expand=True)

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

        # Tabview
        self.chapters_tabview = ctk.CTkTabview(
            right_panel,
            fg_color=COLORS["bg_dark"],
            segmented_button_fg_color=COLORS["bg_panel"],
            segmented_button_selected_color=COLORS["accent_cyan"],
            segmented_button_selected_hover_color="#00b8d4",
            segmented_button_unselected_color=COLORS["bg_dark"],
            segmented_button_unselected_hover_color="#2a2b3e",
            text_color=COLORS["text_primary"],
            corner_radius=8,
        )
        self.chapters_tabview.grid(row=1, column=0, sticky="nsew", padx=6, pady=(0, 6))

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

        # Botones de Lanzar Capítulo Individual
        chap_btn_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
        chap_btn_frame.grid(row=4, column=0, sticky="ew", padx=6, pady=(0, 6))

        self.btn_chap_duo = ctk.CTkButton(
            chap_btn_frame,
            text="🎭 Lanzar Cap (Duo)",
            command=lambda: self._launch_director(auto_record=False, is_solo=False),
            font=("JetBrains Mono", 11, "bold"),
            fg_color=COLORS["accent_yellow"],
            text_color="#000000",
            hover_color="#CBAA00",
        )
        self.btn_chap_duo.pack(side="left", padx=(0, 5), expand=True, fill="x")

        self.btn_chap_solo = ctk.CTkButton(
            chap_btn_frame,
            text="🖥️ Lanzar Cap (Solo)",
            command=lambda: self._launch_director(auto_record=False, is_solo=True),
            font=("JetBrains Mono", 11, "bold"),
            fg_color=COLORS["accent_cyan"],
            text_color="#1a1a2e",
            hover_color="#4361EE",
        )
        self.btn_chap_solo.pack(side="left", padx=5, expand=True, fill="x")

        self.btn_chap_tts = ctk.CTkButton(
            chap_btn_frame,
            text="🔊 TTS Cap",
            command=self.generate_audios_for_chapter,
            font=("JetBrains Mono", 11, "bold"),
            fg_color="#E040FB",
            hover_color="#AA00FF",
        )
        self.btn_chap_tts.pack(side="left", padx=5, expand=True, fill="x")

        self.btn_chap_stop = ctk.CTkButton(
            chap_btn_frame,
            text="⏹",
            command=self.stop_director,
            font=("Arial", 14),
            fg_color="#e74c3c",
            hover_color="#c0392b",
            text_color="#ffffff",
            width=40,
            state="disabled",
        )
        self.btn_chap_stop.pack(side="right")

        # Pestaña placeholder
        welcome_tab = self.chapters_tabview.add("Bienvenido")
        welcome_lbl = tk.Label(
            welcome_tab,
            text="Genera la estructura maestra para crear las pestañas de capítulos.",
            bg=COLORS["bg_dark"],
            fg=COLORS["text_dim"],
            font=("JetBrains Mono", 11),
        )
        welcome_lbl.pack(expand=True)

        self.chapter_editors = {}  # Almacena ref a los tk.Text de cada pestaña
        self.chapter_widgets = []  # Almacena ref a los frames de la lista izquierda

    def _generate_master_structure(self):
        topic = self.series_topic_entry.get().strip()
        if not topic:
            self.append_chat(
                "Error", "⚠️ Debes ingresar un Tema Principal para la Serie."
            )
            return

        try:
            num_chapters = int(self.series_chapters_var.get())
        except ValueError:
            num_chapters = 5

        self.btn_generate_master.configure(state="disabled", text="⏳ Generando...")
        self.series_orchestrator.ai = self.ai  # Asegurar inyección

        def on_success(json_data):
            self.after(0, self._render_master_structure_ui, json_data)

        def on_error(msg):
            self.after(
                0, self.append_chat, "Error", f"❌ Error generando estructura: {msg}"
            )
            self.after(
                0,
                lambda: self.btn_generate_master.configure(
                    state="normal", text="✨ Generar Estructura"
                ),
            )

        mode_var = getattr(self, "orchestrator_mode_var", None)
        mode = mode_var.get() if mode_var is not None else "DUAL AI"  # type: ignore
        aspect_var = getattr(self, "orchestrator_format_var", None)
        aspect = aspect_var.get() if aspect_var is not None else "16:9 (YouTube)"  # type: ignore
        self.series_orchestrator.generate_master_structure(
            topic, num_chapters, mode, aspect, on_success, on_error
        )

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
            self.chapters_tabview.delete("Bienvenido")
        except:
            pass

        for name in list(self.chapter_editors.keys()):
            try:
                self.chapters_tabview.delete(name)
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
            tab = self.chapters_tabview.add(tab_name)

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
                self.chapters_tabview.set(tab_name)
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

            # Leer formato para decidir geometría (is_vertical prevalece sobre is_solo)
            aspect = ""
            if hasattr(self, "orchestrator_format_var"):
                aspect = self.orchestrator_format_var.get()
            elif hasattr(self, "format_combo"):
                aspect = self.format_combo.get()
            is_vertical = "9:16" in aspect

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
                self.after(1000, callback)
        except Exception as e:
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
            tab_name = self.chapters_tabview.get() if self.chapters_tabview else "Cap 1"
        except Exception:
            tab_name = "cap_unknown"

        # ── Construir ruta de audio junto al JSON del capítulo ──
        # Truncar topic a 40 chars para evitar [Errno 36] File name too long
        topic_raw = self.series_topic_entry.get().strip() or "serie_generica"
        topic_safe = (
            re.sub(r"[^a-zA-Z0-9_\-]", "_", topic_raw)[:40].strip("_") or "serie"
        )  # type: ignore

        # Obtener series_dir real del orquestador si existe, sino construir
        series_dir = getattr(self.series_orchestrator, "_series_dir", None)
        if not series_dir:
            series_dir = os.path.join(self.workspace_dir, "projects", topic_safe)

        tab_safe = re.sub(r"[^a-zA-Z0-9_\-]", "_", tab_name.lower())
        # Audios van DENTRO de la carpeta del capítulo: series_dir/cap_1/audio/
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
                "TTS": "#E040FB",
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
            aspect_ratio=aspect,
            obs_password=self._load_env_value("OBS_PASSWORD", ""),
            auto_record=auto_record,
            terminals_preconfigured=True,
        )
        self._active_director.floating_ctrl = self._floating_ctrl

        # Registrar callback de fin para re-habilitar botones
        def _on_finished():
            self.after(0, self._on_director_finished)

        self._active_director.on_finished = _on_finished

        # Lanzar en thread daemon
        threading.Thread(
            target=self._active_director.setup_and_run, daemon=True
        ).start()

        # Reforzar tamaño de terminal 1.5s y 3s después
        self.after(1500, self._reinforce_terminal_size)
        self.after(3000, self._reinforce_terminal_size)

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
                    ["xdotool", "key", "--window", str(self.wid_b), "ctrl+c"],  # type: ignore
                    capture_output=True,
                    timeout=3,
                )
                time.sleep(0.2)
                sp.run(
                    ["xdotool", "key", "--window", str(self.wid_b), "ctrl+c"],  # type: ignore
                    capture_output=True,
                    timeout=3,
                )
            if self.wid_a and self.wid_a != self.wid_b:
                sp.run(
                    ["xdotool", "key", "--window", str(self.wid_a), "ctrl+c"],  # type: ignore
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
            self._floating_ctrl._set_idle()  # type: ignore

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
                self.chapters_tabview.get() if self.chapters_tabview else "Bienvenido"
            )  # type: ignore
            if current_chapter_tab in self.chapter_editors:
                json_str = (
                    self.chapter_editors[current_chapter_tab].get("1.0", "end").strip()
                )
                editor_name = f"Orquestador ({current_chapter_tab})"
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
