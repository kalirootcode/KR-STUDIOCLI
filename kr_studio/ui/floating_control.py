"""
floating_control.py — Mini Control Flotante para KR-STUDIO
Widget pequeño, siempre visible, arrastrable, con botones de control
y mini log animado de procesos.
"""

import threading
import typing
import tkinter as tk
import customtkinter as ctk  # type: ignore
from datetime import datetime


class FloatingControl(ctk.CTkToplevel):
    """Ventana flotante mini con controles de producción + mini log."""

    def __init__(self, main_window: typing.Any):
        super().__init__()
        self.main_window = main_window
        self._app_root = main_window.master_app  # Referencia al CTk root

        # ── Configuración de ventana ──
        self.title("KR-CTRL")
        self.geometry("340x480")  # Ventana más ancha y alta
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.configure(fg_color="#0d0e15")  # Fondo un poco más azul/oscuro
        self.protocol("WM_DELETE_WINDOW", lambda: None)  # No cerrar

        # Posicionar en esquina inferior derecha
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = sw - 360
        y = sh - 520
        self.geometry(f"340x480+{int(x)}+{int(y)}")

        # ── Arrastre ──
        self._drag_x = 0
        self._drag_y = 0

        # ── Header arrastrable ──
        header = ctk.CTkFrame(self, fg_color="#151722", height=32, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)

        title_lbl = ctk.CTkLabel(
            header,
            text="🎬 DIRECTOR CTRL",
            font=("JetBrains Mono", 11, "bold"),
            text_color="#00D9FF",
        )
        title_lbl.pack(side="left", padx=10)

        self.status_lbl = ctk.CTkLabel(
            header,
            text="● LISTO",
            font=("JetBrains Mono", 10, "bold"),
            text_color="#2ECC71",
        )
        self.status_lbl.pack(side="right", padx=10)

        header.bind("<Button-1>", self._start_drag)
        header.bind("<B1-Motion>", self._do_drag)
        title_lbl.bind("<Button-1>", self._start_drag)
        title_lbl.bind("<B1-Motion>", self._do_drag)

        # Contenedor de botones (Grid para alineación perfecta)
        btn_container = ctk.CTkFrame(self, fg_color="transparent")
        btn_container.pack(fill="x", padx=8, pady=8)

        # Configurar 3 columnas iguales
        btn_container.grid_columnconfigure((0, 1, 2), weight=1, uniform="col")

        # Fila 0: Lanzar | TTS | Grabar
        self.btn_launch = ctk.CTkButton(
            btn_container,
            text="🚀 Lanzar",
            command=self._on_launch,
            fg_color="#1E88E5",
            hover_color="#1565C0",
            font=("JetBrains Mono", 11, "bold"),
            height=32,
        )
        self.btn_launch.grid(row=0, column=0, sticky="ew", padx=2, pady=2)

        self.btn_tts = ctk.CTkButton(
            btn_container,
            text="🔊 Prep. Audio",
            command=self._on_tts,
            fg_color="#5E35B1",
            hover_color="#4527A0",
            font=("JetBrains Mono", 11, "bold"),
            height=32,
        )
        self.btn_tts.grid(row=0, column=1, sticky="ew", padx=2, pady=2)

        self.btn_record = ctk.CTkButton(
            btn_container,
            text="🔴 Grabar",
            command=self._on_record,
            fg_color="#D32F2F",
            hover_color="#C62828",
            font=("JetBrains Mono", 11, "bold"),
            height=32,
        )
        self.btn_record.grid(row=0, column=2, sticky="ew", padx=2, pady=2)

        # Fila 1: CONTINUAR (ocupa 2 cols) | DETENER (ocupa 1 col)
        self.btn_continue = ctk.CTkButton(
            btn_container,
            text="▶ CONTINUAR",
            command=self._on_continue,
            fg_color="#2E7D32",
            hover_color="#1B5E20",
            font=("JetBrains Mono", 12, "bold"),
            height=36,
            state="disabled",
        )
        self.btn_continue.grid(
            row=1, column=0, columnspan=2, sticky="ew", padx=2, pady=4
        )

        self.btn_stop = ctk.CTkButton(
            btn_container,
            text="⏹ STOP",
            command=self._on_stop,
            fg_color="#424242",
            hover_color="#212121",
            font=("JetBrains Mono", 12, "bold"),
            height=36,
            state="disabled",
        )
        self.btn_stop.grid(row=1, column=2, sticky="ew", padx=2, pady=4)

        # Fila 2: Inicio | Retry | Skip
        self.btn_restart = ctk.CTkButton(
            btn_container,
            text="⏮ Inicio",
            command=self._on_restart,
            fg_color="#455A64",
            hover_color="#263238",
            font=("JetBrains Mono", 10),
            height=28,
            state="disabled",
        )
        self.btn_restart.grid(row=2, column=0, sticky="ew", padx=2, pady=2)

        self.btn_retry = ctk.CTkButton(
            btn_container,
            text="↺ Reintentar",
            command=self._on_retry,
            fg_color="#455A64",
            hover_color="#263238",
            font=("JetBrains Mono", 10),
            height=28,
            state="disabled",
        )
        self.btn_retry.grid(row=2, column=1, sticky="ew", padx=2, pady=2)

        self.btn_skip = ctk.CTkButton(
            btn_container,
            text="⏭ Saltar",
            command=self._on_skip,
            fg_color="#455A64",
            hover_color="#263238",
            font=("JetBrains Mono", 10),
            height=28,
            state="disabled",
        )
        self.btn_skip.grid(row=2, column=2, sticky="ew", padx=2, pady=2)

        # ── Fila Navegación / Status (Fuera del grid de botones) ──
        nav_row = ctk.CTkFrame(self, fg_color="#151722", height=32, corner_radius=6)
        nav_row.pack(fill="x", padx=8, pady=(2, 6))
        nav_row.pack_propagate(False)

        ctk.CTkLabel(
            nav_row, text="Ir a:", font=("JetBrains Mono", 10), text_color="#78909C"
        ).pack(side="left", padx=(10, 4))

        self.scene_jump_entry = ctk.CTkEntry(
            nav_row,
            width=36,
            height=22,
            font=("JetBrains Mono", 10),
            fg_color="#0a0b0d",
            border_color="#263238",
        )
        self.scene_jump_entry.pack(side="left")

        self.btn_jump = ctk.CTkButton(
            nav_row,
            text="→",
            command=self._on_jump_to_scene,
            fg_color="#37474F",
            hover_color="#263238",
            width=30,
            height=22,
            state="disabled",
        )
        self.btn_jump.pack(side="left", padx=4)

        self.scene_counter_label = ctk.CTkLabel(
            nav_row,
            text="0/0",
            font=("JetBrains Mono", 10, "bold"),
            text_color="#00D9FF",
        )
        self.scene_counter_label.pack(side="right", padx=10)

        # ── Progreso Visual ──
        self.progress = ctk.CTkProgressBar(
            self, height=4, progress_color="#00D9FF", fg_color="#263238"
        )
        self.progress.pack(fill="x", padx=8, pady=(0, 6))
        self.progress.set(0)

        # ── Mini Log de Procesos (Mucho más grande) ──
        log_header = ctk.CTkFrame(self, fg_color="#151722", height=24, corner_radius=0)
        log_header.pack(fill="x", padx=8)
        log_header.pack_propagate(False)

        ctk.CTkLabel(
            log_header,
            text="📋 CONSOLA / NARRACIÓN",
            font=("JetBrains Mono", 9, "bold"),
            text_color="#B0BEC5",
        ).pack(side="left", padx=8)

        self.step_label = ctk.CTkLabel(
            log_header, text="", font=("JetBrains Mono", 9), text_color="#78909C"
        )
        self.step_label.pack(side="right", padx=8)

        log_frame = ctk.CTkFrame(
            self,
            fg_color="#0a0b0d",
            corner_radius=0,
            border_width=1,
            border_color="#263238",
        )
        log_frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        self.log_text = tk.Text(
            log_frame,
            bg="#0a0b0d",
            fg="#CFD8DC",
            font=("JetBrains Mono", 10),
            relief="flat",
            bd=0,
            highlightthickness=0,
            wrap="word",
            state="disabled",
            padx=8,
            pady=8,
            spacing1=2,  # Espacio extra entre lineas para legibilidad
        )
        self.log_text.pack(fill="both", expand=True)

        # Scrollbar para el log
        scrollbar = ctk.CTkScrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.log_text.configure(yscrollcommand=scrollbar.set)

        # Tags de color para el log (Colores más sobrios/pastel)
        self.log_text.tag_config("time", foreground="#546E7A")
        self.log_text.tag_config("step", foreground="#FFB74D")  # Naranja suave
        self.log_text.tag_config("ok", foreground="#81C784")  # Verde suave
        self.log_text.tag_config("wait", foreground="#FFF176")  # Amarillo
        self.log_text.tag_config("error", foreground="#E57373")  # Rojo suave
        self.log_text.tag_config("info", foreground="#64B5F6")  # Azul claro

        # ── Estado de pausa (thread-safe con Lock) ──
        self._waiting = False
        self._continue_clicked = False
        self._lock = threading.Lock()

        self._animating = False

        self._total_scenes = 0
        self._current_scene = 0
        self._scene_index_override: typing.Optional[int] = (
            None  # Para saltar a escena específica
        )
        self._skip_current = False  # Para saltar escena actual
        self._retry_current = False  # Para reintentar escena actual

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
        self._app_root.after(
            0, lambda: self.step_label.configure(text=f"Paso {current}/{total}")
        )

    # ── Acciones ──
    def _on_launch(self):
        """Lanza SOLO el JSON a la terminal (sin grabar). Detecta modo automáticamente."""
        self.main_window.smart_launch()
        self._set_running()

    def _on_record(self):
        """Lanza el JSON + activa grabación OBS. Detecta modo automáticamente."""
        self.main_window.launch_and_record()
        self._set_running()

    def _on_tts(self):
        import os

        director = getattr(self.main_window, "_active_director", None)
        if not director:
            self.add_log("No hay script activo", "error")
            return

        json_data = getattr(director, "guion", None)
        if not json_data:
            self.add_log("Aún sin JSON cargado", "error")
            return

        topic = getattr(director, "project_name", "live_session")
        topic_safe = "".join([c if c.isalnum() else "_" for c in topic])

        output_dir = os.path.join(
            self.main_window.workspace_dir, "projects", topic_safe, "audio"
        )

        self.btn_tts.configure(state="disabled")
        self.add_log("🔊 Compilando audios TTS...", "info")

        try:
            threading.Thread(
                target=self.main_window._generate_audios_thread,
                args=(json_data, output_dir, self.btn_tts),
                daemon=True,
            ).start()
        except AttributeError:
            self.add_log("⚠ Motor TTS no disponible", "error")
            self.btn_tts.configure(state="normal")
        except Exception as e:
            self.add_log(f"⚠ Error iniciando TTS: {e}", "error")
            self.btn_tts.configure(state="normal")

    def _get_current_mode(self) -> str:
        """Lee el modo actual desde la UI principal (DUAL AI / SOLO TERM)."""
        try:
            if (
                hasattr(self.main_window, "pre_mode_var")
                and self.main_window.pre_mode_var
            ):
                return self.main_window.pre_mode_var.get()
        except Exception:
            pass
        return "DUAL AI"

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

    def _on_retry(self):
        with self._lock:
            self._retry_current = True
            self._continue_clicked = True
        self.btn_retry.configure(state="disabled")
        self.add_log("↺ Reintentando escena...", "wait")

    def _on_skip(self):
        with self._lock:
            self._skip_current = True
            self._continue_clicked = True
        self.btn_skip.configure(state="disabled")
        self.add_log("⏭ Escena saltada", "step")

    def _on_restart(self):
        with self._lock:
            self._scene_index_override = 0
            self._continue_clicked = True
        self.btn_restart.configure(state="disabled")
        self.add_log("⏮ Reiniciando desde escena 1...", "error")

    def _on_jump_to_scene(self):
        try:
            n = int(self.scene_jump_entry.get().strip()) - 1
            if 0 <= n < self._total_scenes:
                with self._lock:
                    self._scene_index_override = n
                    self._continue_clicked = True
                self.add_log(f"→ Saltando a escena {n + 1}", "step")
                self.scene_jump_entry.delete(0, "end")
        except ValueError:
            self.add_log("⚠ Número de escena inválido", "error")

    def set_scene_info(self, current: int, total: int):
        self._total_scenes = total
        self._current_scene = current
        self._app_root.after(
            0, lambda: self.scene_counter_label.configure(text=f"{current}/{total}")
        )

    def consume_retry(self) -> bool:
        with self._lock:
            val = self._retry_current
            self._retry_current = False
            return val

    def consume_skip(self) -> bool:
        with self._lock:
            val = self._skip_current
            self._skip_current = False
            return val

    def consume_jump(self) -> int:
        """Retorna el índice de escena a saltar, o -1 si no hay salto pendiente."""
        with self._lock:
            val = self._scene_index_override
            self._scene_index_override = None
            return int(val) if val is not None else -1

    def _set_running(self):
        self.btn_stop.configure(state="normal")
        self.btn_launch.configure(state="disabled")
        self.btn_record.configure(state="disabled")
        self.btn_retry.configure(state="normal")
        self.btn_skip.configure(state="normal")
        self.btn_restart.configure(state="normal")
        self.btn_jump.configure(state="normal")
        self.status_lbl.configure(text="▶ CORRIENDO", text_color="#00CA4E")
        # Limpiar log
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")
        self.step_label.configure(text="")
        self.add_log("Secuencia iniciada", "ok")

    def _set_idle(self):
        self._animating = False
        self.btn_stop.configure(state="disabled")
        self.btn_launch.configure(state="normal")
        self.btn_record.configure(state="normal")
        self.btn_continue.configure(state="disabled")
        self.btn_retry.configure(state="disabled")
        self.btn_skip.configure(state="disabled")
        self.btn_restart.configure(state="disabled")
        self.btn_jump.configure(state="disabled")
        self.status_lbl.configure(text="● LISTO", text_color="#00CA4E")

    # ── API para el Director (llamada desde thread del Director) ──
    def wait_for_continue(self, step_msg: str = "", duration_seconds: float = 0):
        """Bloquea el thread del Director hasta que el usuario presione CONTINUAR.
        Si duration_seconds > 0, bloquea el botón y cuenta atrás antes de permitir continuar."""
        with self._lock:
            self._continue_clicked = False
            self._waiting = True

            # Generar un ID único para esta espera para evitar "scene-skipping" por race condition
            if not hasattr(self, "_wait_id"):
                self._wait_id = 0
            self._wait_id += 1
            current_wait_id = self._wait_id

        # Si hay duración, deshabilitamos el botón y hacemos un countdown visual
        if duration_seconds > 0:

            def _countdown_and_enable(wait_id: int):
                import time as _t

                remaining = int(duration_seconds)

                # Deshabilitar botón al inicio
                self._app_root.after(
                    0,
                    lambda: self.btn_continue.configure(
                        state="disabled", text=f"▶ ESPERA ({remaining}s)"
                    ),
                )
                self._app_root.after(0, self._activate_continue, step_msg, False)

                while remaining > 0:
                    with self._lock:
                        if (
                            not self._waiting
                            or getattr(self, "_wait_id", -1) != wait_id
                        ):
                            return  # Cancelado o saltado

                    _t.sleep(1)
                    remaining -= 1

                    if remaining > 0:
                        self._app_root.after(
                            0,
                            lambda r=remaining: self.btn_continue.configure(
                                text=f"▶ ESPERA ({r}s)"
                            ),
                        )

                # Al terminar, rehabilitar el botón
                with self._lock:
                    if self._waiting and getattr(self, "_wait_id", -1) == wait_id:
                        self._app_root.after(
                            0,
                            lambda: self.btn_continue.configure(
                                state="normal",
                                text="▶ CONTINUAR (Enter)",
                                fg_color="#00CA4E",
                            ),
                        )

            threading.Thread(
                target=_countdown_and_enable, args=(current_wait_id,), daemon=True
            ).start()
        else:
            # Sin duración, activar botón inmediatamente
            msg = step_msg or "Esperando CONTINUAR..."
            self._app_root.after(0, self._activate_continue, msg, True)

        # Polling: esperar a que _continue_clicked sea True (usuario hizo click)
        while not self._continue_clicked:
            if not self.main_window._active_director:
                break
            if getattr(self.main_window._active_director, "stop_requested", False):
                break
            if not self.main_window._active_director.is_running:
                break
            threading.Event().wait(timeout=0.1)  # Sleep 100ms sin bloquear

        with self._lock:
            self._waiting = False

    def _activate_continue(self, msg: str, enable_button: bool = True):
        """Prepara la interfaz para la espera (solo llamar desde main thread)."""
        try:
            if enable_button:
                self.btn_continue.configure(
                    state="normal", text="▶ CONTINUAR (Enter)", fg_color="#00CA4E"
                )
            else:
                self.btn_continue.configure(state="disabled", fg_color="#555555")

            self.status_lbl.configure(text="⏸ ESPERANDO", text_color="#FFCC00")
            self.lift()
            self.add_log(f"⏸ {msg}", "wait")
        except Exception:
            pass

    def notify_finished(self):
        """Llamado cuando el Director termina."""
        with self._lock:
            self._continue_clicked = True  # Desbloquear si está esperando
            self._animating = False
        self.add_log("✅ Secuencia finalizada", "ok")
        self._app_root.after(0, self._set_idle)
        if hasattr(self.main_window, "_on_director_finished"):
            self._app_root.after(200, self.main_window._on_director_finished)

    def start_processing_animation(self, msg="INICIALIZANDO"):
        """Inicia una animación de puntos suspensivos en el label de estado."""
        self._animating = True
        self._anim_dots = 0
        self._anim_msg = msg
        self._animate()

    def _animate(self):
        if not getattr(self, "_animating", False):
            return
        dots = "." * (self._anim_dots % 4)
        try:
            self.status_lbl.configure(
                text=f"⚙ {self._anim_msg}{dots}", text_color="#00D9FF"
            )
        except Exception:
            pass
        self._anim_dots += 1
        self._app_root.after(500, self._animate)

    def stop_processing_animation(self):
        """Detiene la animación y restaura el estado."""
        self._animating = False
        try:
            self.status_lbl.configure(text="▶ CORRIENDO", text_color="#00CA4E")
        except Exception:
            pass
