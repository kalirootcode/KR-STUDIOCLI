"""
chat_panel.py - Componente de UI para el Panel de Chat de KR-Studio
"""
import customtkinter as ctk  # pyre-ignore[21]
from typing import TYPE_CHECKING

from kr_studio.ui.theme import COLORS  # pyre-ignore[21]

if TYPE_CHECKING:
    from kr_studio.ui.main_window import MainWindow  # pyre-ignore[21]


class ChatPanel(ctk.CTkFrame):
    """
    Panel izquierdo de la UI que contiene la interfaz de chat con DOMINION AI,
    los campos de metadatos y los controles de modo.
    """
    def __init__(self, master: 'MainWindow', **kwargs):
        # pyre-ignore[6, 28]
        super().__init__(master, fg_color=COLORS["bg_panel"], corner_radius=12,
                         border_width=1, border_color=COLORS["border"], **kwargs)  # pyre-ignore[28]

        self.main_window = master
        self._build_widgets()

    def _build_widgets(self):
        """Construye todos los widgets dentro de este panel."""
        # Header estilizado
        header = ctk.CTkFrame(self, fg_color=COLORS["header_bg"], height=48, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(header, text="🧠", font=("Arial", 20)).pack(side="left", padx=(12, 4))
        ctk.CTkLabel(header, text="DOMINION AI",
                     font=("JetBrains Mono", 14, "bold"),
                     text_color=COLORS["accent_cyan"]).pack(side="left")

        # Indicador de estado (controlado desde MainWindow)
        self.main_window.status_label = ctk.CTkLabel(header, text="● EN LÍNEA",
                                                     font=("JetBrains Mono", 10),
                                                     text_color=COLORS["accent_green"])
        self.main_window.status_label.pack(side="right", padx=12)

        # Botón OSINT Radar
        self.main_window.btn_osint = ctk.CTkButton(header, text="🌐 Radar OSINT",
                                                   command=self.main_window.osint_search,
                                                   font=("JetBrains Mono", 10, "bold"),
                                                   fg_color="#FF6D00", hover_color="#E65100",
                                                   text_color="#000000",
                                                   width=120, height=30)
        self.main_window.btn_osint.pack(side="right", padx=(0, 6))

        # ─── METADATA SECTION ───
        meta_frame = ctk.CTkFrame(self, fg_color="transparent")
        meta_frame.pack(fill="x", padx=6, pady=4)
        meta_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(meta_frame, text="Título:", font=("JetBrains Mono", 10, "bold"), text_color=COLORS["text_dim"]).grid(row=0, column=0, sticky="w", pady=2)
        self.main_window.meta_title = ctk.CTkEntry(meta_frame, font=("JetBrains Mono", 11), fg_color=COLORS["bg_dark"], border_color=COLORS["border"], height=28)
        self.main_window.meta_title.grid(row=0, column=1, sticky="ew", padx=4, pady=2)

        ctk.CTkLabel(meta_frame, text="Desc:", font=("JetBrains Mono", 10, "bold"), text_color=COLORS["text_dim"]).grid(row=1, column=0, sticky="nw", pady=2)
        self.main_window.meta_desc = ctk.CTkTextbox(meta_frame, font=("JetBrains Mono", 11), fg_color=COLORS["bg_dark"], border_color=COLORS["border"], border_width=1, height=50)
        self.main_window.meta_desc.grid(row=1, column=1, sticky="ew", padx=4, pady=2)

        ctk.CTkLabel(meta_frame, text="Tags:", font=("JetBrains Mono", 10, "bold"), text_color=COLORS["text_dim"]).grid(row=2, column=0, sticky="w", pady=2)
        self.main_window.meta_tags = ctk.CTkEntry(meta_frame, font=("JetBrains Mono", 11), fg_color=COLORS["bg_dark"], border_color=COLORS["border"], height=28, text_color=COLORS["accent_cyan"])
        self.main_window.meta_tags.grid(row=2, column=1, sticky="ew", padx=4, pady=2)

        # Chat display
        self.main_window.chat_display = ctk.CTkTextbox(self, wrap="word",
                                                       font=("JetBrains Mono", 12),
                                                       fg_color=COLORS["bg_chat"],
                                                       text_color=COLORS["text_primary"],
                                                       state="disabled",
                                                       border_width=0)
        self.main_window.chat_display.pack(fill="both", expand=True, padx=6, pady=(4, 4))
        self._configure_chat_tags()

        # Selector de Modo Pre-Generación
        mode_frame = ctk.CTkFrame(self, fg_color="transparent")
        mode_frame.pack(fill="x", padx=6, pady=(4, 2))
        
        ctk.CTkLabel(mode_frame, text="Formato:", 
                     font=("JetBrains Mono", 10, "bold"), 
                     text_color=COLORS["text_dim"]).pack(side="left", padx=(4, 8))
        
        self.main_window.pre_mode_var = ctk.StringVar(value="DUAL AI")
        self.main_window.pre_mode_selector = ctk.CTkSegmentedButton(
            mode_frame, values=["DUAL AI", "SOLO TERM"], variable=self.main_window.pre_mode_var,
            font=("JetBrains Mono", 10, "bold"), height=24,
            fg_color=COLORS["bg_dark"], selected_color=COLORS["accent_cyan"],
            selected_hover_color="#00b8d4"
        )
        self.main_window.pre_mode_selector.pack(side="left", fill="x", expand=True, padx=(0, 4))

        # Input
        input_frame = ctk.CTkFrame(self, fg_color="transparent")
        input_frame.pack(fill="x", padx=6, pady=(0, 6))

        self.main_window.chat_entry = ctk.CTkEntry(input_frame,
                                                   placeholder_text="Pide un guion de video...",
                                                   font=("JetBrains Mono", 12),
                                                   fg_color=COLORS["bg_dark"],
                                                   border_color=COLORS["border"])
        self.main_window.chat_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.main_window.chat_entry.bind("<Return>", lambda e: self.main_window.action_handler.send_chat_message())

        self.main_window.chat_btn = ctk.CTkButton(input_frame, text="⚡", width=45,
                                                  command=self.main_window.action_handler.send_chat_message,
                                                  font=("Arial", 18),
                                                  fg_color=COLORS["accent_cyan"],
                                                  text_color="#000000",
                                                  hover_color="#00b8d4")
        self.main_window.chat_btn.pack(side="right")

    def _configure_chat_tags(self):
        """Configura los tags de colores para los mensajes del chat."""
        chat = self.main_window.chat_display
        chat._textbox.tag_config("sender_system", foreground=COLORS["accent_yellow"])
        chat._textbox.tag_config("sender_user", foreground=COLORS["accent_cyan"])
        chat._textbox.tag_config("sender_ai", foreground=COLORS["accent_green"])
        chat._textbox.tag_config("sender_error", foreground=COLORS["accent_magenta"])
        chat._textbox.tag_config("sender_director", foreground="#AB47BC")
        chat._textbox.tag_config("sender_osint", foreground="#FF6D00")
        chat._textbox.tag_config("msg_body", foreground=COLORS["text_primary"])
