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
        self.geometry(f"300x260+{int(x)}+{int(y)}")

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

        self.btn_tts = ctk.CTkButton(row1, text="🔊",
                                     command=self._on_tts,
                                     fg_color="#E040FB", hover_color="#AA00FF",
                                     text_color="#ffffff", width=36, height=30)
        self.btn_tts.pack(side="left", padx=2)

        self.btn_record = ctk.CTkButton(row1, text="🔴 Grabar",
                                         command=self._on_record,
                                         fg_color="#D32F2F", hover_color="#B71C1C",
                                         text_color="#ffffff",
                                         font=("JetBrains Mono", 11, "bold"),
                                         height=30)
        self.btn_record.pack(side="right", expand=True, padx=(2, 0), fill="x")

        # ── Fila 2: CONTINUAR / DETENER ──
        row2 = ctk.CTkFrame(self, fg_color="transparent")
        row2.pack(fill="x", padx=6, pady=(0, 3))

        self.btn_continue = ctk.CTkButton(row2, text="▶ CONTINUAR (Enter)",
                                           command=self._on_continue,
                                           fg_color="#00CA4E", hover_color="#008A35",
                                           text_color="#ffffff",
                                           font=("JetBrains Mono", 11, "bold"),
                                           height=32, state="disabled")
        self.btn_continue.pack(side="left", expand=True, padx=(0, 2), fill="x")

        self.btn_stop = ctk.CTkButton(row2, text="⏹ DETENER",
                                       command=self._on_stop,
                                       fg_color="#FF2D78", hover_color="#B31F54",
                                       text_color="#ffffff",
                                       font=("JetBrains Mono", 11, "bold"),
                                       height=32, state="disabled")
        self.btn_stop.pack(side="left", expand=True, padx=(2, 0), fill="x")

        # ── Fila 3: Navegación de Escenas ──
        row3 = ctk.CTkFrame(self, fg_color="transparent")
        row3.pack(fill="x", padx=6, pady=(0, 3))

        self.btn_retry = ctk.CTkButton(row3, text="↺ RETRY",
            command=self._on_retry,
            fg_color="#1565C0", hover_color="#0D47A1",
            text_color="#ffffff",
            font=("JetBrains Mono", 10, "bold"),
            height=28, state="disabled")
        self.btn_retry.pack(side="left", expand=True, padx=(0,2), fill="x")

        self.btn_skip = ctk.CTkButton(row3, text="⏭ SKIP",
            command=self._on_skip,
            fg_color="#4A148C", hover_color="#6A1B9A",
            text_color="#ffffff",
            font=("JetBrains Mono", 10, "bold"),
            height=28, state="disabled")
        self.btn_skip.pack(side="left", expand=True, padx=2, fill="x")

        self.btn_restart = ctk.CTkButton(row3, text="⏮ INICIO",
            command=self._on_restart,
            fg_color="#BF360C", hover_color="#E64A19",
            text_color="#ffffff",
            font=("JetBrains Mono", 10, "bold"),
            height=28, state="disabled")
        self.btn_restart.pack(side="right", expand=True, padx=(2,0), fill="x")

        # ── Fila 4: Saltar a escena específica ──
        row4 = ctk.CTkFrame(self, fg_color="transparent")
        row4.pack(fill="x", padx=6, pady=(0, 3))

        ctk.CTkLabel(row4, text="Ir a:",
            font=("JetBrains Mono", 9), text_color="#6A6A7A").pack(side="left", padx=4)

        self.scene_jump_entry = ctk.CTkEntry(row4, width=40, height=24,
            font=("JetBrains Mono", 10), fg_color="#08090a",
            border_color="#1a1b2e", placeholder_text="N°")
        self.scene_jump_entry.pack(side="left", padx=2)

        self.btn_jump = ctk.CTkButton(row4, text="IR →",
            command=self._on_jump_to_scene,
            fg_color="#006064", hover_color="#00838F",
            text_color="#ffffff",
            font=("JetBrains Mono", 9, "bold"),
            height=24, width=40, state="disabled")
        self.btn_jump.pack(side="left", padx=2)

        self.scene_counter_label = ctk.CTkLabel(row4, text="0/0",
            font=("JetBrains Mono", 9, "bold"),
            text_color="#00D9FF")
        self.scene_counter_label.pack(side="right", padx=6)

        # ── Progreso Visual ──
        self.progress = ctk.CTkProgressBar(self, height=4, progress_color="#00D9FF")
        self.progress.pack(fill="x", padx=6, pady=(4, 0))

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

        self._animating = False

        self._total_scenes = 0
        self._current_scene = 0
        self._scene_index_override: typing.Optional[int] = None  # Para saltar a escena específica
        self._skip_current = False          # Para saltar escena actual
        self._retry_current = False         # Para reintentar escena actual

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
            
        json_data = getattr(director, "json_data", None)
        if not json_data:
            self.add_log("Aún sin JSON cargado", "error")
            return
            
        topic = getattr(director, "topic", "live_session")
        topic_safe = "".join([c if c.isalnum() else "_" for c in topic])
        
        output_dir = os.path.join(self.main_window.workspace_dir, "projects", topic_safe, "audio_live")
        
        self.btn_tts.configure(state="disabled")
        self.add_log("🔊 Compilando audios TTS...", "info")
        
        try:
            threading.Thread(
                target=self.main_window._generate_audios_thread,
                args=(json_data, output_dir, self.btn_tts),
                daemon=True
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
            if hasattr(self.main_window, 'pre_mode_var') and self.main_window.pre_mode_var:
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
                self.add_log(f"→ Saltando a escena {n+1}", "step")
                self.scene_jump_entry.delete(0, "end")
        except ValueError:
            self.add_log("⚠ Número de escena inválido", "error")

    def set_scene_info(self, current: int, total: int):
        self._total_scenes = total
        self._current_scene = current
        self._app_root.after(0, lambda: self.scene_counter_label.configure(
            text=f"{current}/{total}"))

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
        Si duration_seconds > 0, auto-continúa después de ese tiempo."""
        with self._lock:
            self._continue_clicked = False
            self._waiting = True
            
            # Generar un ID único para esta espera para evitar "scene-skipping" por race condition
            if not hasattr(self, "_wait_id"):
                self._wait_id = 0
            self._wait_id += 1
            current_wait_id = self._wait_id

        if duration_seconds > 0:
            # Auto-continuar después de duration_seconds
            def _auto_continue(wait_id: int):
                import time as _t
                _t.sleep(duration_seconds)
                with self._lock:
                    # Solo autocompletar si seguimos en la MISMA espera
                    if self._waiting and getattr(self, "_wait_id", -1) == wait_id:
                        self._continue_clicked = True
                        
                self._app_root.after(0, self.btn_continue.configure,
                                     {"state": "disabled"})
            threading.Thread(target=_auto_continue, args=(current_wait_id,), daemon=True).start()

        # Activar botón CONTINUAR desde el main thread
        msg = step_msg or "Esperando CONTINUAR..."
        self._app_root.after(0, self._activate_continue, msg)

        # Polling: esperar a que _continue_clicked sea True
        while not self._continue_clicked:
            if not self.main_window._active_director:
                break
            if not self.main_window._active_director.is_running:
                break
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
            self._animating = False
        self.add_log("✅ Secuencia finalizada", "ok")
        self._app_root.after(0, self._set_idle)
        if hasattr(self.main_window, '_on_director_finished'):
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
            self.status_lbl.configure(text=f"⚙ {self._anim_msg}{dots}", text_color="#00D9FF")
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
