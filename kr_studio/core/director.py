"""
director.py — Módulo Director / Titiritero (Phase 3)
Orquesta la ejecución del video con DOBLE terminal + OBS:
  Terminal A → kr-clidn (dashboard, ya con venv activado)
  Terminal B → ejecución de comandos reales (limpios)
  OBS → cambia escenas automáticamente
  Widget flotante → pausa paso a paso + mini log
  NEW: Lee respuestas del terminal con xdotool + xclip
"""
import threading
import subprocess
import time
import os
from kr_studio.core.audio_engine import AudioEngine
from kr_studio.core.obs_controller import OBSController


class DirectorEngine:
    def __init__(self, main_app, json_data: list, workspace_dir: str):
        self.app = main_app
        self.json_data = json_data
        self.workspace_dir = workspace_dir
        self.audio_engine = AudioEngine()
        self.is_running = False

        # Dual terminal WIDs
        self.wid_a = None  # Terminal A (kr-clidn)
        self.wid_b = None  # Terminal B (ejecución)

        self.typing_delay = 120  # ms entre teclas
        self.obs = OBSController()
        self.floating_ctrl = None  # Widget flotante

        # Almacén de respuestas leídas del terminal
        self.last_terminal_read = ""

    def start(self):
        self.is_running = True
        threading.Thread(target=self._run_sequence, daemon=True).start()

    def stop(self):
        self.is_running = False

    # ─────────────────────────────────────────────
    # UTILIDADES X11
    # ─────────────────────────────────────────────

    def _find_all_konsole_wids(self) -> list:
        for search_type, term in [('--class', 'konsole'), ('--name', 'Konsole')]:
            try:
                result = subprocess.run(
                    ['xdotool', 'search', search_type, term],
                    capture_output=True, text=True, timeout=5
                )
                wids = [w.strip() for w in result.stdout.strip().split('\n') if w.strip()]
                if wids:
                    return wids
            except Exception:
                pass
        return []

    def _resize_window(self, wid: str, width=450, height=800):
        try:
            hex_wid = hex(int(wid))
            result = subprocess.run(
                ['wmctrl', '-i', '-r', hex_wid, '-e', f'0,-1,-1,{width},{height}'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode != 0:
                raise RuntimeError("wmctrl falló")
        except (FileNotFoundError, RuntimeError, ValueError):
            try:
                subprocess.run(
                    ['xdotool', 'windowsize', wid, str(width), str(height)],
                    capture_output=True, timeout=5
                )
            except Exception:
                pass

    def _focus_window(self, wid: str):
        try:
            subprocess.run(
                ['xdotool', 'windowactivate', '--sync', wid],
                capture_output=True, timeout=5
            )
            time.sleep(0.3)
        except Exception as e:
            self._log("Error", f"windowactivate falló: {e}")

    def _type_text(self, wid: str, text: str, delay_ms: int = None):
        delay = delay_ms or self.typing_delay
        self._focus_window(wid)
        try:
            subprocess.run(
                ['xdotool', 'type', '--clearmodifiers', '--delay', str(delay), text],
                capture_output=True, text=True, timeout=120
            )
        except Exception as e:
            self._log("Error", f"xdotool type falló: {e}")

    def _send_key(self, wid: str, key: str):
        self._focus_window(wid)
        try:
            subprocess.run(
                ['xdotool', 'key', '--clearmodifiers', key],
                capture_output=True, text=True, timeout=5
            )
        except Exception as e:
            self._log("Error", f"xdotool key falló: {e}")

    def _log(self, sender: str, message: str):
        try:
            self.app.after(0, self.app.append_chat, sender, message)
        except Exception:
            print(f"[{sender}] {message}")

    def _flog(self, message: str, tag: str = "info"):
        """Log al widget flotante."""
        if self.floating_ctrl:
            self.floating_ctrl.add_log(message, tag)

    # ─────────────────────────────────────────────
    # LEER TERMINAL (desde archivos de log)
    # ─────────────────────────────────────────────

    def _read_terminal(self, wid: str) -> str:
        """Lee el terminal desde archivo de log — NUNCA interrumpe kr-clidn."""
        from kr_studio.core.dynamic_director import LOG_TERMINAL_A, LOG_TERMINAL_B, read_log_file

        # Determinar qué log leer según el WID
        if wid == self.wid_a:
            return read_log_file(LOG_TERMINAL_A, 40)
        else:
            return read_log_file(LOG_TERMINAL_B, 30)

    # ─────────────────────────────────────────────
    # KR-CLIDN BOOT SEQUENCE (Terminal A)
    # Terminal ya tiene venv activado desde el startup
    # ─────────────────────────────────────────────

    def _boot_krcli_terminal_a(self):
        self._log("Director", "🚀 Iniciando KR-CLIDN en Terminal A...")
        self._flog("Boot: script + venv + kr-clidn", "info")

        self._focus_window(self.wid_a)

        # 1. Iniciar script para logging (subshell, NO -c)
        self._type_text(self.wid_a, "script -q -f /tmp/kr_terminal_a.log", delay_ms=30)
        self._send_key(self.wid_a, "Return")
        time.sleep(0.8)

        # 2. Limpiar
        self._type_text(self.wid_a, "clear", delay_ms=30)
        self._send_key(self.wid_a, "Return")
        time.sleep(0.3)

        # 3. Activar venv
        self._type_text(self.wid_a, "source venv/bin/activate", delay_ms=30)
        self._send_key(self.wid_a, "Return")
        time.sleep(1.0)

        # 4. Lanzar kr-clidn como comando normal
        self._type_text(self.wid_a, "kr-clidn", delay_ms=80)
        self._send_key(self.wid_a, "Return")

        self._log("Director", "⏳ Esperando splash de KR-CLIDN...")
        self._flog("Esperando splash screen...", "wait")
        time.sleep(5.0)

        # Esperar confirmación del usuario
        self._log("Director", "⏸ Presiona CONTINUAR cuando el dashboard esté listo.")
        if self.floating_ctrl:
            self.floating_ctrl.wait_for_continue("Dashboard KR-CLIDN cargando...")

        self._log("Director", "✅ KR-CLIDN Dashboard listo")
        self._flog("KR-CLIDN Dashboard ✅", "ok")

    # ─────────────────────────────────────────────
    # SECUENCIA PRINCIPAL (DUAL TERMINAL + OBS)
    # ─────────────────────────────────────────────

    def _run_sequence(self):
        self._log("Director", "🎬 Iniciando secuencia DUAL TERMINAL...")
        self._flog("Iniciando secuencia...", "ok")

        # ── PASO 1: Detectar o lanzar 2 Konsoles ──
        if self.wid_a and self.wid_b:
            self._log("Director", f"Terminal A: {self.wid_a} | Terminal B: {self.wid_b}")
        else:
            self._flog("Lanzando 2 Konsoles...", "info")
            for i in range(2):
                try:
                    subprocess.Popen(['konsole'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    time.sleep(1.5)
                except FileNotFoundError:
                    self._log("Error", "❌ Konsole no está instalado.")
                    self.is_running = False
                    return

            time.sleep(2.0)
            wids = self._find_all_konsole_wids()
            if len(wids) < 2:
                self._log("Error", f"❌ Se necesitan 2 Konsoles, encontradas: {len(wids)}")
                self.is_running = False
                return
            self.wid_a = wids[-2]
            self.wid_b = wids[-1]

        # ── PASO 2: Redimensionar ──
        self._resize_window(self.wid_a, 450, 800)
        self._resize_window(self.wid_b, 450, 800)
        self._flog("Terminales a 450x800", "ok")
        time.sleep(0.5)

        # ── PASO 3: Conectar a OBS ──
        obs_ok = self.obs.connect()
        if obs_ok:
            scenes = self.obs._get_scene_names()
            self._log("Director", f"🔴 OBS conectado — Escenas: {scenes}")
            self._flog(f"OBS OK — Escenas: {scenes}", "ok")

            if "Terminal-A" not in scenes or "Terminal-B" not in scenes:
                self._log("Director", "⚠ FALTAN escenas 'Terminal-A' y/o 'Terminal-B' en OBS!")
                self._flog("⚠ Crear escenas Terminal-A y Terminal-B", "error")

            self.obs.start_recording()
            time.sleep(1.0)
            self.obs.switch_scene("Terminal-A")
            self._flog("Grabación OBS iniciada", "ok")
        else:
            self._log("Director", "⚠ OBS no disponible — Modo manual")
            self._flog("OBS no disponible", "wait")

        # ── PASO 4: Limpiar Terminal B ──
        self._focus_window(self.wid_b)
        self._type_text(self.wid_b, "clear", delay_ms=20)
        self._send_key(self.wid_b, "Return")
        time.sleep(0.3)

        # ── PASO 5: Boot KR-CLIDN en Terminal A ──
        self._boot_krcli_terminal_a()

        # ── PASO 6: Ejecutar escenas del guion ──
        total = len(self.json_data)
        for idx, escena in enumerate(self.json_data):
            if not self.is_running:
                self._log("Director", "⏹ Secuencia detenida.")
                break

            tipo = escena.get("tipo", "")
            step_num = idx + 1
            self._log("Director", f"▶ Escena {step_num}/{total} — {tipo.upper()}")

            # Progreso en widget flotante
            if self.floating_ctrl:
                self.floating_ctrl.set_progress(step_num, total)
                self.floating_ctrl.add_log(f"Escena {step_num}/{total}: {tipo.upper()}", "step")

            # Duración del audio
            audio_path = os.path.join(self.workspace_dir, f"audio_{idx}.mp3")
            duracion = self.audio_engine.obtener_duracion(audio_path) if os.path.exists(audio_path) else 3.0

            if tipo == "narracion":
                # Solo espera la duración del audio (kr-clidn activo en Terminal A)
                if obs_ok:
                    self.obs.switch_scene("Terminal-A")
                time.sleep(max(0.5, duracion))
                self._flog(f"  Voz: {escena.get('voz', '')[:40]}", "info")

            elif tipo == "ejecucion":
                if obs_ok:
                    self.obs.switch_scene("Terminal-B")
                comando_real = escena.get("comando_real", "")
                if comando_real:
                    self._type_text(self.wid_b, comando_real)
                    time.sleep(max(0.5, duracion))
                    self._send_key(self.wid_b, "Return")
                    time.sleep(1.5)
                self._flog(f"  Ejecutado: {comando_real[:40]}", "ok")

            elif tipo == "menu":
                if obs_ok:
                    self.obs.switch_scene("Terminal-A")
                tecla = escena.get("tecla", "")
                texto = escena.get("texto", "")
                espera = escena.get("espera", 2.0)
                if tecla:
                    self._type_text(self.wid_a, tecla, delay_ms=150)
                    time.sleep(0.3)
                    self._send_key(self.wid_a, "Return")
                    time.sleep(espera)
                    self._flog(f"  Menú: tecla '{tecla}'", "info")
                elif texto:
                    self._type_text(self.wid_a, texto)
                    time.sleep(max(0.5, duracion))
                    self._send_key(self.wid_a, "Return")
                    time.sleep(espera)
                    self._flog(f"  Texto: {texto[:35]}", "info")

            elif tipo == "enter":
                terminal = escena.get("terminal", "A")
                wid = self.wid_a if terminal == "A" else self.wid_b
                espera = escena.get("espera", 2.0)
                if obs_ok:
                    scene = "Terminal-A" if terminal == "A" else "Terminal-B"
                    self.obs.switch_scene(scene)
                self._send_key(wid, "Return")
                time.sleep(espera)
                self._flog(f"  Enter Terminal {terminal}", "info")

            elif tipo == "pausa":
                espera = escena.get("espera", 3.0)
                time.sleep(espera)
                self._flog(f"  Pausa {espera}s", "info")

            elif tipo == "leer":
                # ── LEER → Captura el contenido del terminal ──
                terminal = escena.get("terminal", "A")
                wid = self.wid_a if terminal == "A" else self.wid_b
                espera = escena.get("espera", 2.0)
                time.sleep(espera)  # Esperar a que la respuesta termine

                output = self._read_terminal(wid)
                # Guardar las últimas 30 líneas para contexto
                lines = output.split('\n')
                last_lines = '\n'.join(lines[-30:]) if len(lines) > 30 else output
                self.last_terminal_read = last_lines
                self._log("Director", f"📖 Terminal {terminal} leída ({len(lines)} líneas)")
                self._flog(f"  Leído: {len(lines)} líneas de Terminal {terminal}", "ok")

            elif tipo == "esperar":
                if self.floating_ctrl:
                    self.floating_ctrl.wait_for_continue(f"Escena {step_num}: Esperando...")
                else:
                    time.sleep(escena.get("espera", 5.0))

            else:
                self._log("Director", f"⚠ Tipo desconocido: {tipo}")
                time.sleep(1.0)

            # ═══ PAUSA ENTRE CADA PASO ═══
            if self.is_running and self.floating_ctrl and tipo != "esperar":
                self.floating_ctrl.wait_for_continue(f"Paso {step_num}/{total} listo")

        # ── PASO 7: Finalizar ──
        if obs_ok:
            time.sleep(2.0)
            self.obs.stop_recording()
            self.obs.disconnect()
            self._log("Director", "🔴 Grabación detenida.")

        self.is_running = False
        self._log("Director", "✅ Secuencia DUAL finalizada. ¡Video listo!")
        if self.floating_ctrl:
            self.floating_ctrl.notify_finished()
