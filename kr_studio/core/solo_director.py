"""
solo_director.py — Director Solo (Terminal B únicamente)
Genera videos de herramientas y testeo profesional sin kr-clidn.
Flujo: AI genera comandos → ejecuta en Terminal B → lee output → genera más → repite.

Soporta:
  - Modo wrapper: usa kr-cli para envolver comandos
  - Modo limpio: comandos directos en terminal
"""
import threading
import subprocess
import time
import os
import re
import json
from kr_studio.core.audio_engine import AudioEngine
from kr_studio.core.obs_controller import OBSController
from kr_studio.core.dynamic_director import LOG_TERMINAL_B, read_log_file, strip_ansi

# ── Prompts ──

PROMPT_SOLO_COMMANDS = """Eres un experto en ciberseguridad creando un video de testeo profesional.

Tema: "{topic}"
Ciclo {cycle}/{total_cycles}. Duración objetivo: {duration_min} min.

{context_block}

Genera comandos para ejecutar EN VIVO en una terminal Linux.
{wrapper_instruction}

TARGETS AUTORIZADOS: scanme.nmap.org, testphp.vulnweb.com, httpbin.org, badssl.com, google.com

REGLAS:
- Comandos que producen output VISUAL interesante para un video
- NUNCA: exit, quit, Ctrl+C, kill, shutdown, clear (no borrar pantalla)
- Progresión lógica: de reconocimiento a explotación
- Cada comando debe enseñar algo diferente
- Si hay contexto anterior, profundiza basándote en los resultados

Responde SOLO JSON:
[
  {{"tipo": "narracion", "voz": "Descripción de lo que haremos (TTS)"}},
  {{"tipo": "ejecucion", "voz": "Explicación corta", "comando_real": "comando limpio"}},
  {{"tipo": "pausa", "voz": "Analizando resultados", "espera": 4.0}}
]

Genera 4-6 acciones por ciclo."""


class SoloDirectorEngine:
    """Director Solo — usa solo Terminal B para videos de herramientas."""

    def __init__(self, main_app, topic: str, duration_min: int, workspace_dir: str):
        self.app = main_app
        self.topic = topic
        self.duration_min = max(1, min(30, duration_min))
        self.workspace_dir = workspace_dir
        self.audio_engine = AudioEngine()
        self.is_running = False

        self.wid_b = None
        self.typing_delay = 120
        self.obs = OBSController()
        self.floating_ctrl = None
        self.ai_engine = None

        self.use_wrapper = False  # True = kr-cli wrapper, False = clean
        self.current_cycle = 0
        self.total_cycles = max(2, duration_min // 2)

        self.on_json_terminal_b = None  # callback

    def start(self):
        self.is_running = True
        # Limpiar log
        try:
            open(LOG_TERMINAL_B, 'w').close()
        except Exception:
            pass
        threading.Thread(target=self._run_solo_sequence, daemon=True).start()

    def stop(self):
        self.is_running = False

    # ─── X11 Utils ───

    def _focus_window(self, wid: str):
        try:
            subprocess.run(['xdotool', 'windowactivate', '--sync', wid],
                           capture_output=True, timeout=5)
            time.sleep(0.3)
        except Exception:
            pass

    def _type_text(self, wid: str, text: str, delay_ms: int = None):
        delay = delay_ms or self.typing_delay
        self._focus_window(wid)
        try:
            subprocess.run(['xdotool', 'type', '--clearmodifiers', '--delay', str(delay), text],
                           capture_output=True, text=True, timeout=120)
        except Exception as e:
            self._log("Error", f"xdotool type: {e}")

    def _send_key(self, wid: str, key: str):
        self._focus_window(wid)
        try:
            subprocess.run(['xdotool', 'key', '--clearmodifiers', key],
                           capture_output=True, text=True, timeout=5)
        except Exception:
            pass

    def _resize_window(self, wid: str, w=450, h=800):
        try:
            subprocess.run(['wmctrl', '-i', '-r', hex(int(wid)), '-e', f'0,-1,-1,{w},{h}'],
                           capture_output=True, timeout=5)
        except Exception:
            pass

    def _log(self, sender: str, msg: str):
        try:
            self.app.after(0, self.app.append_chat, sender, msg)
        except Exception:
            print(f"[{sender}] {msg}")

    def _flog(self, msg: str, tag: str = "info"):
        if self.floating_ctrl:
            self.floating_ctrl.add_log(msg, tag)

    def _wait_continue(self, msg: str):
        if self.floating_ctrl:
            self.floating_ctrl.wait_for_continue(msg)

    def _show_json_b(self, json_data):
        if self.on_json_terminal_b and json_data:
            text = json.dumps(json_data, indent=2, ensure_ascii=False)
            try:
                self.app.after(0, self.on_json_terminal_b, text)
            except Exception:
                pass

    def _wrap_command(self, cmd: str) -> str:
        """Envuelve un comando con kr-cli wrapper si está habilitado."""
        if self.use_wrapper:
            return f"kr-cli {cmd}"
        return cmd

    def _speak(self, text: str) -> float:
        """Genera TTS y reproduce audio. Retorna duración en segundos."""
        if not text or not text.strip():
            return 0.0
        self._audio_counter = getattr(self, '_audio_counter', 0) + 1
        audio_dir = os.path.join(self.workspace_dir, "audio_solo")
        os.makedirs(audio_dir, exist_ok=True)
        audio_path = os.path.join(audio_dir, f"solo_{self._audio_counter}.mp3")

        try:
            duracion = self.audio_engine.generar_audio(text, audio_path)
            self._flog(f"  🔊 TTS: {duracion:.1f}s", "info")

            # Reproducir audio en background
            subprocess.Popen(
                ['mpv', '--no-video', '--really-quiet', audio_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return duracion
        except Exception as e:
            self._flog(f"  ⚠ TTS error: {e}", "error")
            return 2.0

    # ─── SECUENCIA PRINCIPAL ───

    def _run_solo_sequence(self):
        mode = "KR-CLI Wrapper" if self.use_wrapper else "Comandos Limpios"
        self._log("Director", f"⚡ MODO SOLO — {self.topic}")
        self._log("Director", f"📐 {self.duration_min} min | {self.total_cycles} ciclos | {mode}")
        self._flog(f"Solo: {self.topic} ({mode})", "ok")

        if not self.wid_b:
            self._log("Error", "❌ No hay Terminal B.")
            self.is_running = False
            return

        self._resize_window(self.wid_b)

        # ── OBS ──
        obs_ok = self.obs.connect()
        if obs_ok:
            self.obs.switch_scene("Terminal-B")
            self.obs.start_recording()
            time.sleep(1.0)
        else:
            self._flog("OBS no disponible", "wait")

        # ── Boot Terminal B con log ──
        self._focus_window(self.wid_b)
        self._type_text(self.wid_b, f"script -q -f {LOG_TERMINAL_B}", delay_ms=30)
        self._send_key(self.wid_b, "Return")
        time.sleep(0.5)
        self._type_text(self.wid_b, "clear", delay_ms=30)
        self._send_key(self.wid_b, "Return")
        time.sleep(0.3)

        if self.use_wrapper:
            self._type_text(self.wid_b, "source venv/bin/activate", delay_ms=30)
            self._send_key(self.wid_b, "Return")
            time.sleep(1.0)

        self._wait_continue("Terminal lista")

        # ── Narración introductoria ──
        intro = f"Bienvenidos. Hoy vamos a explorar {self.topic} con demostraciones prácticas en vivo."
        dur = self._speak(intro)
        time.sleep(max(dur, 2.0))

        # ── CICLOS ──
        prev_output = ""
        all_commands = []

        for cycle in range(1, self.total_cycles + 1):
            if not self.is_running:
                break

            self.current_cycle = cycle
            self._log("Director", f"═══ CICLO {cycle}/{self.total_cycles} ═══")
            self._flog(f"═══ CICLO {cycle}/{self.total_cycles} ═══", "step")

            if self.floating_ctrl:
                self.floating_ctrl.set_progress(cycle, self.total_cycles)

            # ── Generar comandos con AI ──
            self._flog("  🤖 AI generando comandos...", "wait")

            context_block = ""
            if prev_output:
                context_block = (
                    f"RESULTADOS ANTERIORES (Terminal B):\n"
                    f"{prev_output[:2000]}\n\n"
                    f"Comandos ya ejecutados: {', '.join(all_commands[-5:])}\n"
                    f"Basándote en estos resultados, profundiza con nuevos comandos."
                )
            else:
                context_block = "Este es el primer ciclo. Comienza con reconocimiento básico."

            wrapper_instruction = ""
            if self.use_wrapper:
                wrapper_instruction = (
                    "IMPORTANTE: Todos los comandos deben usar el wrapper kr-cli.\n"
                    "Ejemplo: 'kr-cli nmap -sV target' en vez de 'nmap -sV target'"
                )
            else:
                wrapper_instruction = "Los comandos son LIMPIOS (sin wrapper, directos en la terminal)."

            commands_json = self._generate_commands(context_block, wrapper_instruction, cycle)

            if not commands_json:
                self._flog("  Sin comandos generados", "error")
                continue

            self._flog(f"  {len(commands_json)} acciones generadas ✅", "ok")
            self._show_json_b(commands_json)

            # ── Ejecutar comandos con TTS ──
            for ci, cmd in enumerate(commands_json):
                if not self.is_running:
                    break

                voz = cmd.get("voz", "")

                if cmd.get("tipo") == "narracion":
                    # Generar y reproducir narración TTS
                    self._flog(f"  🎙 {voz[:40]}", "info")
                    dur = self._speak(voz)
                    time.sleep(max(dur, 2.0))

                elif cmd.get("tipo") == "ejecucion":
                    comando = cmd.get("comando_real", "")
                    if comando:
                        # Narrar mientras se tipea
                        if voz:
                            dur = self._speak(voz)
                        else:
                            dur = 0.0

                        # Aplicar wrapper y ejecutar
                        final_cmd = self._wrap_command(comando)
                        self._flog(f"  > {final_cmd[:45]}", "ok")
                        self._focus_window(self.wid_b)
                        self._type_text(self.wid_b, final_cmd)
                        time.sleep(0.5)
                        self._send_key(self.wid_b, "Return")
                        # Esperar: al menos la duración del audio + 2s para output
                        time.sleep(max(dur, 2.0) + 1.0)
                        all_commands.append(comando)
                        self._wait_continue(f"Cmd {ci+1} ejecutado")

                elif cmd.get("tipo") == "pausa":
                    if voz:
                        dur = self._speak(voz)
                        time.sleep(max(dur, cmd.get("espera", 3.0)))
                    else:
                        time.sleep(cmd.get("espera", 3.0))

            # ── Leer output de Terminal B ──
            self._flog("  📖 Leyendo Terminal B...", "info")
            prev_output = read_log_file(LOG_TERMINAL_B, 40)
            tb_lines = len(prev_output.split('\n'))
            self._flog(f"  Terminal B: {tb_lines} líneas ✅", "ok")

            if cycle < self.total_cycles and self.is_running:
                self._wait_continue(f"Listo para ciclo {cycle+1}")

        # ── Narración de cierre ──
        outro = f"Esto ha sido una demostración práctica de {self.topic}. Síguenos para más contenido de ciberseguridad."
        dur = self._speak(outro)
        time.sleep(max(dur, 3.0))

        # ── FIN ──
        if obs_ok:
            time.sleep(2.0)
            self.obs.stop_recording()
            self.obs.disconnect()

        self.is_running = False
        self._log("Director", f"✅ Video Solo completado — {self.total_cycles} ciclos")
        if self.floating_ctrl:
            self.floating_ctrl.notify_finished()

    # ─── AI: Generar comandos ───

    def _generate_commands(self, context_block: str, wrapper_instruction: str, cycle: int) -> list:
        if not self.ai_engine or not self.ai_engine.chat_session:
            self._flog("  ❌ AI Engine no configurado", "error")
            return []
        try:
            prompt = PROMPT_SOLO_COMMANDS.format(
                topic=self.topic,
                cycle=cycle,
                total_cycles=self.total_cycles,
                duration_min=self.duration_min,
                context_block=context_block,
                wrapper_instruction=wrapper_instruction
            )
            response = self.ai_engine.chat_session.send_message(prompt)
            data = self.ai_engine.extraer_json(response.text)
            return data if data else []
        except Exception as e:
            self._log("Error", f"Error AI: {e}")
            return []
