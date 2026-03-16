"""
KR-STUDIO — IDE de Producción de Videos de Ciberseguridad
Punto de entrada principal.
"""

import customtkinter as ctk
import sys
import os
import logging
import signal

# Activar logging para ver errores de OBS en la terminal
logging.basicConfig(level=logging.INFO, format="%(name)s: %(message)s")

# Agregar el directorio padre al path para imports relativos
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kr_studio.ui.main_window import MainWindow

# Variable global para controlar el cierre
_app_instance = None


def graceful_shutdown(signum=None, frame=None):
    """Cierre graceful ante Ctrl+C."""
    print("\n" + "=" * 50)
    print("👋 KR-STUDIO cerrando gracefully...")
    print("¡Hasta luego! 🎬")
    print("=" * 50 + "\n")
    if _app_instance:
        try:
            _app_instance.destroy()
        except Exception:
            pass
    sys.exit(0)


# Registrar handler para Ctrl+C
signal.signal(signal.SIGINT, graceful_shutdown)
signal.signal(signal.SIGTERM, graceful_shutdown)


def main():
    global _app_instance

    # Configuración global de CustomTkinter
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    # Crear ventana raíz
    app = ctk.CTk()
    app.title("KR-STUDIO — Script-to-Screen IDE")
    app.minsize(900, 600)

    _app_instance = app

    # Instanciar la interfaz principal
    main_window = MainWindow(app)

    # Iniciar el loop de eventos
    app.mainloop()


if __name__ == "__main__":
    main()
