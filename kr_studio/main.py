"""
KR-STUDIO — IDE de Producción de Videos de Ciberseguridad
Punto de entrada principal.
"""
import customtkinter as ctk
import sys
import os
import logging

# Activar logging para ver errores de OBS en la terminal
logging.basicConfig(level=logging.INFO, format="%(name)s: %(message)s")

# Agregar el directorio padre al path para imports relativos
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kr_studio.ui.main_window import MainWindow

def main():
    # Configuración global de CustomTkinter
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    # Crear ventana raíz
    app = ctk.CTk()
    app.title("KR-STUDIO — Script-to-Screen IDE")
    app.minsize(900, 600)

    # Instanciar la interfaz principal
    main_window = MainWindow(app)

    # Iniciar el loop de eventos
    app.mainloop()


if __name__ == "__main__":
    main()
