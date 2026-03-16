"""
editor_panel.py - Componente de UI para el Panel del Editor de KR-Studio
"""
import customtkinter as ctk
from typing import TYPE_CHECKING

from kr_studio.ui.theme import COLORS

if TYPE_CHECKING:
    from kr_studio.ui.main_window import MainWindow


class EditorPanel(ctk.CTkFrame):
    """
    Panel central de la UI que contiene el editor de guiones con pestañas
    para la Terminal A y la Terminal B.
    """
    def __init__(self, master: 'MainWindow', **kwargs):
        super().__init__(master, fg_color=COLORS["bg_panel"], corner_radius=12,
                         border_width=1, border_color=COLORS["border"], **kwargs)
        
        self.main_window = master
        self._build_widgets()

    def _build_widgets(self):
        """Construye todos los widgets dentro de este panel."""
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Header con pestañas para editores A/B
        header = ctk.CTkFrame(self, fg_color=COLORS["header_bg"], height=48)
        header.grid(row=0, column=0, sticky="ew")

        self.main_window.editor_tabs = ctk.CTkSegmentedButton(
            header,
            values=["● Terminal A", "● Terminal B"],
            command=self.main_window.on_tab_switch,
            font=("JetBrains Mono", 11, "bold"),
            height=30,
            corner_radius=8,
            border_width=1,
            fg_color=COLORS["bg_dark"],
            selected_color=COLORS["accent_green"],
            selected_hover_color="#00a23d",
            unselected_color=COLORS["header_bg"],
            unselected_hover_color="#2a2b3e"
        )
        self.main_window.editor_tabs.set("● Terminal A")
        self.main_window.editor_tabs.pack(pady=8, padx=12, fill="x")

        # Contenedor para los editores
        editor_container = ctk.CTkFrame(self, fg_color=COLORS["bg_editor"])
        editor_container.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)
        editor_container.grid_rowconfigure(0, weight=1)
        editor_container.grid_columnconfigure(0, weight=1)

        # Editor A (principal)
        self.main_window.editor = ctk.CTkTextbox(
            editor_container,
            wrap="word",
            font=("JetBrains Mono", 12, "normal"),
            fg_color=COLORS["bg_editor"],
            text_color="#e0e0e0",
            border_width=0,
            undo=True
        )
        self.main_window.editor.grid(row=0, column=0, sticky="nsew")
        self.main_window.editor.bind("<<Modified>>", self.main_window.on_editor_modified)

        # Editor B (para modo SOLO TERM)
        self.main_window.editor_b = ctk.CTkTextbox(
            editor_container,
            wrap="word",
            font=("JetBrains Mono", 12, "normal"),
            fg_color=COLORS["bg_editor"],
            text_color="#e0e0e0",
            border_width=0,
            undo=True
        )
        self.main_window.editor_b.bind("<<Modified>>", self.main_window.on_editor_modified)

        # Mostrar Editor A por defecto
        if self.main_window.editor:
            self.main_window.editor.tkraise()
