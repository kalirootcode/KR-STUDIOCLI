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
    "bg_dark": "#08090a",
    "bg_panel": "#0d0e10",
    "bg_editor": "#0a0b0d",
    "bg_chat": "#0a0b0d",
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
        self.typing_speed_ms = 120  # Default
        self.wid_a = None  # Terminal A (kr-cli)
        self.wid_b = None  # Terminal B (ejecución)
        self._anim_id = None  # Para la animación de "procesando"
        self._floating_ctrl = None  # Widget flotante

        # ─── LAYOUT ───
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_api_bar()
        self._build_chat_panel()
        self._build_editor_panel()

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
            except Exception:
                self.append_chat("Sistema", "Bienvenido a KR-STUDIO 🎬\n⚠ API Key en .env inválida. Ingresa una nueva.")
        else:
            self.append_chat("Sistema", "Bienvenido a KR-STUDIO 🎬\nIDE de Producción de Videos — DOMINION Edition\nIngresa tu API Key para comenzar.")

        # Lanzar Konsole al inicio
        self.after(1000, self._launch_konsole_on_startup)

        # Crear widget flotante
        self.after(500, self._create_floating_control)

    def _create_floating_control(self):
        """Crea el mini control flotante."""
        self._floating_ctrl = FloatingControl(self)

    # ═══════════════════════════════════════════════
    # CONSTRUCCIÓN DE PANELES
    # ═══════════════════════════════════════════════

    def _build_api_bar(self):
        """Barra superior de API Key."""
        bar = ctk.CTkFrame(self, fg_color=COLORS["header_bg"], height=50, corner_radius=0)
        bar.grid(row=0, column=0, columnspan=2, sticky="ew")
        bar.grid_propagate(False)

        lbl = ctk.CTkLabel(bar, text="🔑 API KEY", font=("JetBrains Mono", 12, "bold"),
                           text_color=COLORS["accent_cyan"])
        lbl.pack(side="left", padx=(15, 8))

        self.api_entry = ctk.CTkEntry(bar, width=350, show="*",
                                       placeholder_text="Gemini API Key...",
                                       font=("JetBrains Mono", 12),
                                       fg_color=COLORS["bg_dark"],
                                       border_color=COLORS["border"])
        self.api_entry.pack(side="left", padx=5, fill="x", expand=True)

        self.api_btn = ctk.CTkButton(bar, text="Conectar", width=90,
                                      command=self.save_api_key,
                                      font=("JetBrains Mono", 12, "bold"),
                                      fg_color=COLORS["accent_cyan"],
                                      text_color="#000000",
                                      hover_color="#00b8d4")
        self.api_btn.pack(side="left", padx=(5, 15))

    def _build_chat_panel(self):
        """Panel izquierdo — Chat AI DOMINION."""
        panel = ctk.CTkFrame(self, fg_color=COLORS["bg_panel"], corner_radius=12,
                              border_width=1, border_color=COLORS["border"])
        panel.grid(row=1, column=0, sticky="nsew", padx=(8, 4), pady=8)

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
        """Panel derecho — Editor JSON Profesional + controles."""
        panel = ctk.CTkFrame(self, fg_color=COLORS["bg_panel"], corner_radius=12,
                              border_width=1, border_color=COLORS["border"])
        panel.grid(row=1, column=1, sticky="nsew", padx=(4, 8), pady=8)

        # Usar grid para que el editor se expanda y los controles queden fijos abajo
        panel.grid_rowconfigure(2, weight=1)  # Editor row se expande
        panel.grid_columnconfigure(0, weight=1)

        # ── Header (row 0) ──
        header = ctk.CTkFrame(panel, fg_color=COLORS["header_bg"], height=42, corner_radius=0)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)

        ctk.CTkLabel(header, text="📝", font=("Arial", 18)).pack(side="left", padx=(12, 4))
        ctk.CTkLabel(header, text="EDITOR DE GUION",
                     font=("JetBrains Mono", 13, "bold"),
                     text_color=COLORS["accent_cyan"]).pack(side="left")

        # ── Toolbar proyectos (row 1) ──
        toolbar = ctk.CTkFrame(panel, fg_color=COLORS["header_bg"], height=34)
        toolbar.grid(row=1, column=0, sticky="ew")
        toolbar.grid_propagate(False)

        ctk.CTkButton(toolbar, text="💾", width=36, height=26,
                       command=self.save_project,
                       font=("JetBrains Mono", 10, "bold"),
                       fg_color="#1a1b2e", hover_color="#252640",
                       border_width=1, border_color=COLORS["border"]).pack(side="left", padx=(6, 2))

        ctk.CTkButton(toolbar, text="📂", width=36, height=26,
                       command=self.load_project,
                       font=("JetBrains Mono", 10, "bold"),
                       fg_color="#1a1b2e", hover_color="#252640",
                       border_width=1, border_color=COLORS["border"]).pack(side="left", padx=2)

        # Target selector
        ctk.CTkLabel(toolbar, text="🎯",
                     font=("Arial", 12)).pack(side="left", padx=(8, 2))

        self.target_combo = ctk.CTkComboBox(
            toolbar, width=190, height=26,
            values=[
                "scanme.nmap.org",
                "testphp.vulnweb.com",
                "httpbin.org",
                "badssl.com",
                "rest.vulnweb.com",
                "IP Personalizada"
            ],
            font=("JetBrains Mono", 9),
            fg_color=COLORS["bg_dark"],
            border_color=COLORS["border"],
            dropdown_fg_color=COLORS["bg_dark"]
        )
        self.target_combo.set("scanme.nmap.org")
        self.target_combo.pack(side="left", padx=2)

        self.project_name_label = ctk.CTkLabel(toolbar, text="",
                                                font=("JetBrains Mono", 9),
                                                text_color=COLORS["text_dim"])
        self.project_name_label.pack(side="right", padx=6)

        # ── Editor DUAL con pestañas (row 2 — SE EXPANDE) ──
        editor_tabs_frame = ctk.CTkFrame(panel, fg_color="transparent")
        editor_tabs_frame.grid(row=2, column=0, sticky="nsew", padx=6, pady=(2, 0))
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
                                     font=("JetBrains Mono", 12),
                                     state="disabled",
                                     relief="flat", bd=0,
                                     selectbackground="#08090a",
                                     highlightthickness=0,
                                     padx=6, pady=4)
        self.line_numbers.pack(side="left", fill="y")

        self.editor = tk.Text(self.editor_container_a,
                               bg=COLORS["bg_editor"],
                               fg=COLORS["text_primary"],
                               font=("JetBrains Mono", 12),
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
                                       font=("JetBrains Mono", 12),
                                       state="disabled",
                                       relief="flat", bd=0,
                                       selectbackground="#08090a",
                                       highlightthickness=0,
                                       padx=6, pady=4)
        self.line_numbers_b.pack(side="left", fill="y")

        self.editor_b = tk.Text(self.editor_container_b,
                                 bg="#0a0d0a",
                                 fg="#a0ffa0",
                                 font=("JetBrains Mono", 12),
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

        # Syntax highlighting tags para ambos editores
        for ed in [self.editor, self.editor_b]:
            ed.tag_config("json_key", foreground=COLORS["accent_cyan"])
            ed.tag_config("json_string", foreground=COLORS["accent_green"])
            ed.tag_config("json_bracket", foreground=COLORS["accent_yellow"])
            ed.tag_config("json_keyword", foreground=COLORS["accent_magenta"])
            ed.tag_config("json_colon", foreground="#8888aa")
            ed.tag_config("json_number", foreground="#FF8A65")

        self.editor.bind("<KeyRelease>", lambda e: self.after(100, self._update_editor))
        self.editor.bind("<ButtonRelease-1>", lambda e: self._update_line_numbers())

        # ── CONTROLES FIJOS ABAJO (row 3 — NO se expande) ──
        controls = ctk.CTkFrame(panel, fg_color=COLORS["header_bg"], corner_radius=8)
        controls.grid(row=3, column=0, sticky="ew", padx=6, pady=(2, 6))

        # Slider de velocidad
        speed_row = ctk.CTkFrame(controls, fg_color="transparent")
        speed_row.pack(fill="x", padx=8, pady=(6, 2))

        ctk.CTkLabel(speed_row, text="⌨ Velocidad:",
                     font=("JetBrains Mono", 10, "bold"),
                     text_color=COLORS["text_dim"]).pack(side="left")

        self.speed_slider = ctk.CTkSlider(speed_row, from_=40, to=200,
                                           number_of_steps=16,
                                           command=self._on_speed_change,
                                           width=140,
                                           fg_color=COLORS["border"],
                                           progress_color=COLORS["accent_cyan"],
                                           button_color=COLORS["accent_cyan"])
        self.speed_slider.set(120)
        self.speed_slider.pack(side="left", padx=6)

        self.speed_label = ctk.CTkLabel(speed_row, text="120ms",
                                         font=("JetBrains Mono", 10, "bold"),
                                         text_color=COLORS["accent_cyan"])
        self.speed_label.pack(side="left")

        # Slider de duración de video
        dur_row = ctk.CTkFrame(controls, fg_color="transparent")
        dur_row.pack(fill="x", padx=8, pady=(0, 2))

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
        btn_row.pack(fill="x", padx=8, pady=(2, 3))

        self.btn_tts = ctk.CTkButton(btn_row, text="🔊 TTS",
                                      command=self.generate_audios,
                                      font=("JetBrains Mono", 11, "bold"),
                                      fg_color="#1a1b2e",
                                      hover_color="#252640",
                                      border_width=1,
                                      border_color=COLORS["accent_cyan"],
                                      height=34)
        self.btn_tts.pack(side="left", expand=True, padx=(0, 3), fill="x")

        self.btn_launch = ctk.CTkButton(btn_row, text="🎬 Lanzar",
                                         command=self.launch_konsole,
                                         fg_color=COLORS["accent_green"],
                                         hover_color="#00A23D",
                                         text_color="#000000",
                                         font=("JetBrains Mono", 11, "bold"),
                                         height=34)
        self.btn_launch.pack(side="left", expand=True, padx=3, fill="x")

        self.btn_record = ctk.CTkButton(btn_row, text="🔴 Grabar",
                                         command=self.launch_and_record,
                                         fg_color="#D32F2F",
                                         hover_color="#B71C1C",
                                         text_color="#ffffff",
                                         font=("JetBrains Mono", 11, "bold"),
                                         height=34)
        self.btn_record.pack(side="left", expand=True, padx=3, fill="x")

        self.btn_stop = ctk.CTkButton(btn_row, text="⏹ Detener",
                                       command=self.stop_director,
                                       fg_color="#424242",
                                       hover_color="#616161",
                                       text_color="#ffffff",
                                       font=("JetBrains Mono", 11, "bold"),
                                       height=34,
                                       state="disabled")
        self.btn_stop.pack(side="right", expand=True, padx=(3, 0), fill="x")

        # Fila 2: Botón Dinámico
        btn_row2 = ctk.CTkFrame(controls, fg_color="transparent")
        btn_row2.pack(fill="x", padx=8, pady=(0, 6))

        self.btn_dynamic = ctk.CTkButton(btn_row2, text="🚀 DINÁMICO",
                                          command=self.launch_dynamic,
                                          fg_color="#7B1FA2",
                                          hover_color="#6A1B9A",
                                          text_color="#ffffff",
                                          font=("JetBrains Mono", 12, "bold"),
                                          height=34)
        self.btn_dynamic.pack(fill="x")

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

    def _on_speed_change(self, value):
        self.typing_speed_ms = int(value)
        self.speed_label.configure(text=f"{self.typing_speed_ms}ms")

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
        if not self.wid_a or not self.wid_b:
            self.append_chat("Error", "❌ No hay terminales detectadas. Espera a que abran.")
            return

        if not self.ai or not self.ai.chat_session:
            self.append_chat("Error", "❌ Conecta la API Key primero.")
            return

        # Obtener el tema del último mensaje del chat
        topic = self._get_last_user_topic()
        if not topic:
            self.append_chat("Error", "❌ Escribe un tema en el chat primero.\nEjemplo: 'créame un post sobre metasploit'")
            return

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
        self._active_director.typing_delay = self.typing_speed_ms
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

        self._active_director.start()

        # Re-habilitar después de un timeout largo
        self.after(duration * 60 * 1000 + 30000, lambda: self.btn_dynamic.configure(state="normal"))

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
    # KONSOLE AL INICIO
    # ═══════════════════════════════════════════════

    def _launch_konsole_on_startup(self):
        threading.Thread(target=self._startup_konsole_thread, daemon=True).start()

    def _startup_konsole_thread(self):
        import subprocess as sp

        self.after(0, self.append_chat, "Sistema",
                   "🖥 Abriendo 2 terminales Konsole...\n"
                   "  Terminal A → KR-CLIDN (dashboard/AI) [KaliRootCLI + venv]\n"
                   "  Terminal B → Ejecución de comandos")
        try:
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
            if len(wids) >= 2:
                self.wid_a = wids[-2]  # Terminal A
                self.wid_b = wids[-1]  # Terminal B

                # Redimensionar y posicionar ambas
                for wid in [self.wid_a, self.wid_b]:
                    hex_wid = hex(int(wid))
                    sp.run(['wmctrl', '-i', '-r', hex_wid, '-e', '0,-1,-1,450,800'],
                           capture_output=True, timeout=5)

                self.after(0, self.append_chat, "Sistema",
                           f"✅ Terminal A (WID: {self.wid_a}) — KR-CLIDN\n"
                           f"✅ Terminal B (WID: {self.wid_b}) — Ejecución\n"
                           f"Ambas a 450x800 (9:16). Configura OBS con 2 escenas:\n"
                           f"  Scene 'Terminal-A' → captura Terminal A\n"
                           f"  Scene 'Terminal-B' → captura Terminal B")
            elif len(wids) == 1:
                self.wid_a = wids[0]
                self.wid_b = wids[0]
                self.after(0, self.append_chat, "Sistema",
                           f"⚠ Solo 1 Konsole encontrada (WID: {self.wid_a}).\nUsando misma terminal para A y B.")
            else:
                self.after(0, self.append_chat, "Sistema", "⚠ Konsoles abiertas pero sin WID detectado.")
        except Exception as e:
            self.after(0, self.append_chat, "Error", f"⚠ {e}")

    # ═══════════════════════════════════════════════
    # CHAT AI — MENSAJES ELEGANTES
    # ═══════════════════════════════════════════════

    def save_api_key(self):
        key = self.api_entry.get().strip()
        if not key:
            self.append_chat("Sistema", "⚠ La API Key está vacía.")
            return
        try:
            self.ai = AIEngine(key)
            self._save_env_key(key)
            self.append_chat("Sistema", "✅ API Key conectada y guardada en .env — DOMINION listo.")
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
            # Resetear sesión para evitar contaminación de temas anteriores
            if self.ai.model:
                self.ai.chat_session = self.ai.model.start_chat(history=[])

            # Inyectar el target legal seleccionado
            target = self.target_combo.get() if hasattr(self, 'target_combo') else "scanme.nmap.org"
            enriched_prompt = (
                f"TEMA SOLICITADO POR EL USUARIO: {prompt}\n\n"
                f"[TARGET LEGAL OBLIGATORIO: {target}]\n\n"
                f"Genera un guion sobre EXACTAMENTE este tema: {prompt}\n"
                f"NO generes sobre nmap ni otro tema diferente al solicitado."
            )
            response = self.ai.chat(enriched_prompt)
            json_data = self.ai.extraer_json(response)

            if json_data:
                self.after(0, self._stop_processing_animation)
                self.after(0, self.append_chat, "DOMINION",
                           f"✅ Guion generado — {len(json_data)} escenas. Revisa el Editor →")
                json_str = json.dumps(json_data, indent=4, ensure_ascii=False)

                def inject_json():
                    self.editor.delete("1.0", "end")
                    self.editor.insert("end", json_str)
                    self._update_editor()
                    # Auto-save
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
        for idx, escena in enumerate(json_data):
            voz = escena.get("voz", "")
            if not voz:
                continue
            path = os.path.join(self.workspace_dir, f"audio_{idx}.mp3")
            try:
                dur = audio_engine.generar_audio(voz, path)
                self.after(0, self.append_chat, "TTS", f"Audio {idx+1}/{total} — {dur:.1f}s")
            except Exception as e:
                errores += 1
                self.after(0, self.append_chat, "Error", f"❌ Audio {idx+1}: {e}")

        msg = "✅ Todos los audios listos." if errores == 0 else f"⚠ {errores} error(es)."
        self.after(0, self.append_chat, "Sistema", msg)
        self.after(0, lambda: self.btn_tts.configure(state="normal"))

    # ═══════════════════════════════════════════════
    # LANZAR KONSOLE + XDOTOOL
    # ═══════════════════════════════════════════════

    def launch_konsole(self):
        """Lanza la secuencia dual SIN grabación OBS."""
        self._launch_director(auto_record=False)

    def launch_and_record(self):
        """Lanza la secuencia dual CON grabación OBS automática."""
        self._launch_director(auto_record=True)

    def _launch_director(self, auto_record=False):
        json_data = self._parse_editor_json()
        if json_data is None:
            return

        mode_txt = "+ OBS GRABANDO" if auto_record else "sin grabación"
        self.append_chat("Sistema", f"🎬 Lanzando secuencia DUAL ({mode_txt}, tipeo: {self.typing_speed_ms}ms)...")
        self.btn_launch.configure(state="disabled")
        self.btn_record.configure(state="disabled")

        self._active_director = DirectorEngine(self, json_data, self.workspace_dir)
        self._active_director.wid_a = self.wid_a
        self._active_director.wid_b = self.wid_b
        self._active_director.typing_delay = self.typing_speed_ms
        self._active_director.obs.password = self._load_env_value("OBS_PASSWORD", "")

        if not auto_record:
            # Desactivar OBS para modo sin grabación
            self._active_director.obs = type('MockOBS', (), {'connect': lambda s: False, 'connected': False})()

        # Pasar referencia del widget flotante ANTES de iniciar
        self._active_director.floating_ctrl = self._floating_ctrl

        self._active_director.start()

        # Activar botón Detener, desactivar Lanzar/Grabar
        self.btn_stop.configure(state="normal")
        self.after(5000, lambda: self.btn_launch.configure(state="normal"))
        self.after(5000, lambda: self.btn_record.configure(state="normal"))

    def stop_director(self):
        """Detiene la secuencia del Director inmediatamente."""
        if self._active_director and self._active_director.is_running:
            self._active_director.stop()
            self.append_chat("Sistema", "⏹ Secuencia detenida por el usuario.")
        self.btn_stop.configure(state="disabled")
        self.btn_launch.configure(state="normal")
        self.btn_record.configure(state="normal")

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
        json_str = self.editor.get("1.0", "end").strip()
        if not json_str:
            self.append_chat("Sistema", "⚠ El editor está vacío.")
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
