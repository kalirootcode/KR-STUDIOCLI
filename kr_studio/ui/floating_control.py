"""
floating_control.py — Mini Control Flotante para KR-STUDIO
Widget pequeño, siempre visible, arrastrable, con botones de control
y mini log animado de procesos.
"""
import customtkinter as ctk
import tkinter as tk
import threading
from datetime import datetime


class FloatingControl(ctk.CTkToplevel):
    """Ventana flotante mini con controles de producción + mini log."""

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self._app_root = main_window.master_app  # Referencia al CTk root

        # ── Configuración de ventana ──
        self.title("KR-CTRL")
        self.geometry("300x260")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.configure(fg_color="#0a0b0d")
        self.protocol("WM_DELETE_WINDOW", lambda: None)  # No cerrar

        # Posicionar en esquina inferior derecha
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = sw - 320
        y = sh - 320
        self.geometry(f"300x260+{x}+{y}")

        # ── Arrastre ──
        self._drag_x = 0
        self._drag_y = 0

        # ── Header arrastrable ──
        header = ctk.CTkFrame(self, fg_color="#1a1b2e", height=28, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)

        title_lbl = ctk.CTkLabel(header, text="🎬 KR-STUDIO",
                                  font=("JetBrains Mono", 10, "bold"),
                                  text_color="#00D9FF")
        title_lbl.pack(side="left", padx=8)

        self.status_lbl = ctk.CTkLabel(header, text="● LISTO",
                                        font=("JetBrains Mono", 9, "bold"),
                                        text_color="#00CA4E")
        self.status_lbl.pack(side="right", padx=8)

        header.bind("<Button-1>", self._start_drag)
        header.bind("<B1-Motion>", self._do_drag)
        title_lbl.bind("<Button-1>", self._start_drag)
        title_lbl.bind("<B1-Motion>", self._do_drag)

        # ── Fila 1: Lanzar / Grabar ──
        row1 = ctk.CTkFrame(self, fg_color="transparent")
        row1.pack(fill="x", padx=6, pady=(6, 3))

        self.btn_launch = ctk.CTkButton(row1, text="🎬 Lanzar",
                                         command=self._on_launch,
                                         fg_color="#00CA4E", hover_color="#00A23D",
                                         text_color="#000000",
                                         font=("JetBrains Mono", 11, "bold"),
                                         height=30)
        self.btn_launch.pack(side="left", expand=True, padx=(0, 2), fill="x")

        self.btn_record = ctk.CTkButton(row1, text="🔴 Grabar",
                                         command=self._on_record,
                                         fg_color="#D32F2F", hover_color="#B71C1C",
                                         text_color="#000000",
                                         font=("JetBrains Mono", 11, "bold"),
                                         height=30)
        self.btn_record.pack(side="right", expand=True, padx=(2, 0), fill="x")

        # ── Fila 2: CONTINUAR / DETENER ──
        row2 = ctk.CTkFrame(self, fg_color="transparent")
        row2.pack(fill="x", padx=6, pady=(0, 3))

        self.btn_continue = ctk.CTkButton(row2, text="▶ CONTINUAR",
                                           command=self._on_continue,
                                           fg_color="#FF8F00", hover_color="#F57C00",
                                           text_color="#000000",
                                           font=("JetBrains Mono", 12, "bold"),
                                           height=34,
                                           state="disabled")
        self.btn_continue.pack(side="left", expand=True, padx=(0, 2), fill="x")

        self.btn_stop = ctk.CTkButton(row2, text="⏹ DETENER",
                                       command=self._on_stop,
                                       fg_color="#424242", hover_color="#616161",
                                       text_color="#000000",
                                       font=("JetBrains Mono", 12, "bold"),
                                       height=34,
                                       state="disabled")
        self.btn_stop.pack(side="right", expand=True, padx=(2, 0), fill="x")

        # ── Mini Log de Procesos ──
        log_header = ctk.CTkFrame(self, fg_color="#1a1b2e", height=20, corner_radius=0)
        log_header.pack(fill="x", padx=6, pady=(0, 0))
        log_header.pack_propagate(False)
        ctk.CTkLabel(log_header, text="📋 LOG DE PROCESOS",
                     font=("JetBrains Mono", 8, "bold"),
                     text_color="#00D9FF").pack(side="left", padx=6)

        self.step_label = ctk.CTkLabel(log_header, text="",
                                        font=("JetBrains Mono", 8),
                                        text_color="#888888")
        self.step_label.pack(side="right", padx=6)

        log_frame = ctk.CTkFrame(self, fg_color="#08090a", corner_radius=4)
        log_frame.pack(fill="both", expand=True, padx=6, pady=(0, 6))

        self.log_text = tk.Text(log_frame, bg="#08090a", fg="#00CA4E",
                                 font=("JetBrains Mono", 8),
                                 relief="flat", bd=0,
                                 highlightthickness=0,
                                 wrap="word",
                                 state="disabled",
                                 padx=6, pady=4)
        self.log_text.pack(fill="both", expand=True)

        # Tags de color para el log
        self.log_text.tag_config("time", foreground="#555555")
        self.log_text.tag_config("step", foreground="#FF8F00")
        self.log_text.tag_config("ok", foreground="#00CA4E")
        self.log_text.tag_config("wait", foreground="#FFCC00")
        self.log_text.tag_config("error", foreground="#FF4444")
        self.log_text.tag_config("info", foreground="#00D9FF")

        # ── Estado de pausa (thread-safe con Lock) ──
        self._waiting = False
        self._continue_clicked = False
        self._lock = threading.Lock()

    # ── Arrastre ──
    def _start_drag(self, event):
        self._drag_x = event.x
        self._drag_y = event.y

    def _do_drag(self, event):
        x = self.winfo_x() + event.x - self._drag_x
        y = self.winfo_y() + event.y - self._drag_y
        self.geometry(f"+{x}+{y}")

    # ── Log (thread-safe via root.after) ──
    def add_log(self, message: str, tag: str = "info"):
        """Agrega una línea al mini log con timestamp."""
        def _insert():
            try:
                self.log_text.configure(state="normal")
                now = datetime.now().strftime("%H:%M:%S")
                self.log_text.insert("end", f"[{now}] ", "time")
                self.log_text.insert("end", f"{message}\n", tag)
                self.log_text.see("end")
                self.log_text.configure(state="disabled")
            except Exception:
                pass
        self._app_root.after(0, _insert)

    def set_progress(self, current: int, total: int):
        """Actualiza el contador de pasos."""
        self._app_root.after(0, lambda: self.step_label.configure(
            text=f"Paso {current}/{total}"))

    # ── Acciones ──
    def _on_launch(self):
        self.main_window.launch_konsole()
        self._set_running()

    def _on_record(self):
        self.main_window.launch_and_record()
        self._set_running()

    def _on_stop(self):
        self.main_window.stop_director()
        with self._lock:
            self._continue_clicked = True  # Desbloquear si está esperando
            self._waiting = False
        self._set_idle()
        self.add_log("Secuencia detenida por el usuario", "error")

    def _on_continue(self):
        """Desbloquea el Director para que continúe."""
        with self._lock:
            self._continue_clicked = True
        self.btn_continue.configure(state="disabled")
        self.status_lbl.configure(text="▶ CORRIENDO", text_color="#00CA4E")
        self.add_log("→ CONTINUAR", "ok")

    def _set_running(self):
        self.btn_stop.configure(state="normal")
        self.btn_launch.configure(state="disabled")
        self.btn_record.configure(state="disabled")
        self.status_lbl.configure(text="▶ CORRIENDO", text_color="#00CA4E")
        # Limpiar log
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")
        self.step_label.configure(text="")
        self.add_log("Secuencia iniciada", "ok")

    def _set_idle(self):
        self.btn_stop.configure(state="disabled")
        self.btn_launch.configure(state="normal")
        self.btn_record.configure(state="normal")
        self.btn_continue.configure(state="disabled")
        self.status_lbl.configure(text="● LISTO", text_color="#00CA4E")

    # ── API para el Director (llamada desde thread del Director) ──
    def wait_for_continue(self, step_msg: str = ""):
        """Bloquea el thread del Director hasta que el usuario presione CONTINUAR."""
        with self._lock:
            self._continue_clicked = False
            self._waiting = True

        # Activar botón CONTINUAR desde el main thread
        msg = step_msg or "Esperando CONTINUAR..."
        self._app_root.after(0, self._activate_continue, msg)

        # Polling: esperar a que _continue_clicked sea True
        while not self._continue_clicked:
            if not self.main_window._active_director or not self.main_window._active_director.is_running:
                break  # Director fue detenido
            threading.Event().wait(timeout=0.1)  # Sleep 100ms sin bloquear

        with self._lock:
            self._waiting = False

    def _activate_continue(self, msg: str):
        """Activa el botón CONTINUAR (solo llamar desde main thread)."""
        try:
            self.btn_continue.configure(state="normal")
            self.status_lbl.configure(text="⏸ ESPERANDO", text_color="#FFCC00")
            self.lift()
            self.add_log(f"⏸ {msg}", "wait")
        except Exception:
            pass

    def notify_finished(self):
        """Llamado cuando el Director termina."""
        with self._lock:
            self._continue_clicked = True  # Desbloquear si está esperando
        self.add_log("✅ Secuencia finalizada", "ok")
        self._app_root.after(0, self._set_idle)
