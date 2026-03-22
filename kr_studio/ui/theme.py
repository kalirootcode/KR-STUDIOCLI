"""
theme.py - Tema Black Red Team profesional para KR-Studio
Estilo: Dark Mode + Red Team - Negro, Rojo, Gris
"""

import customtkinter as ctk
from typing import Dict

# ═══════════════════════════════════════════════════════════════════
#  PALETA DE COLORES - BLACK RED TEAM CYBER
# ═══════════════════════════════════════════════════════════════════

COLORS = {
    # Fondos principales (Negro)
    "bg_dark": "#0a0a0a",
    "bg_panel": "#111111",
    "bg_hover": "#1a1a1a",
    "bg_active": "#222222",
    "bg_chat": "#0a0a0a",
    "bg_editor": "#0a0a0a",
    "bg_header": "#0f0f0f",
    # Acentos (Rojo)
    "accent_red": "#ff3333",
    "accent_red_dim": "#cc2222",
    "accent_red_glow": "#ff4444",
    # Otros acentos
    "accent_cyan": "#00ccff",
    "accent_cyan_dim": "#0099cc",
    "accent_yellow": "#ffcc00",
    "accent_yellow_dim": "#cc9900",
    "accent_green": "#00cc66",
    "accent_green_dim": "#009944",
    "accent_orange": "#ff6633",
    "accent_orange_dim": "#cc4422",
    "accent_magenta": "#ff33ff",
    # Grises
    "gray_dark": "#2a2a2a",
    "gray_medium": "#3a3a3a",
    "gray_light": "#4a4a4a",
    # Estados
    "success": "#00cc66",
    "warning": "#ffaa00",
    "info": "#00aaff",
    # Textos (Blanco)
    "text_primary": "#ffffff",
    "text_secondary": "#cccccc",
    "text_dim": "#888888",
    # Bordes
    "border": "#333333",
    "header_bg": "#0f0f0f",
}

# ═══════════════════════════════════════════════════════════════════
#  COLORES POR MÓDULO (Rojos y variaciones)
# ═══════════════════════════════════════════════════════════════════

MODULE_COLORS = [
    {"name": "Rojo", "primary": "#ff3333", "dim": "#cc2222", "bg": "#1a0a0a"},
    {"name": "Rojo2", "primary": "#ff4444", "dim": "#cc3333", "bg": "#1a0a0a"},
    {"name": "Rojo3", "primary": "#ff5555", "dim": "#cc4444", "bg": "#1a0a0a"},
    {"name": "Rojo4", "primary": "#ff2222", "dim": "#bb1111", "bg": "#150505"},
    {"name": "Rojo5", "primary": "#ee3333", "dim": "#bb2222", "bg": "#180808"},
    {"name": "Rojo6", "primary": "#dd3333", "dim": "#aa2222", "bg": "#160606"},
    {"name": "Rojo7", "primary": "#ff6666", "dim": "#dd4444", "bg": "#1a0c0c"},
    {"name": "Rojo8", "primary": "#ff7777", "dim": "#dd5555", "bg": "#1a0d0d"},
    {"name": "Rojo9", "primary": "#ff8888", "dim": "#dd6666", "bg": "#1a0e0e"},
    {"name": "Rojo10", "primary": "#ff9999", "dim": "#dd7777", "bg": "#1a0f0f"},
]


def get_module_color(nro_modulo: int) -> Dict[str, str]:
    """Obtiene los colores para un módulo específico."""
    index = (nro_modulo - 1) % len(MODULE_COLORS)
    return MODULE_COLORS[index]


# ═══════════════════════════════════════════════════════════════════
#  CONFIGURACIÓN GLOBAL DE CTK
# ═══════════════════════════════════════════════════════════════════


def configure_ctk_appearance():
    """Configura el aspecto global de CustomTkinter."""
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("red")
