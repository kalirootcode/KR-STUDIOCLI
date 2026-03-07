"""
dynamic_director.py — Director Dinámico v2 con Log Files
Alterna entre Terminal A (kr-clidn) y Terminal B (comandos).
LEE terminales via archivos de log (script -f) — NUNCA interrumpe kr-clidn.

Flujo por ciclo:
  1. Pregunta en Terminal A → DOMINION responde
  2. Lee log de Terminal A (archivo, sin interrumpir)
  3. AI analiza → genera comandos para Terminal B
  4. Ejecuta en Terminal B
  5. Lee log de Terminal B (archivo)
  6. AI genera siguiente pregunta basada en ambos contextos
  7. Repite
"""
import threading
import subprocess
import time
import os
import re
import json
from kr_studio.core.tts_engine import TTSEngine
from kr_studio.core.obs_controller import OBSController

# Archivos de log para leer terminales sin interrumpir
LOG_TERMINAL_A = "/tmp/kr_terminal_a.log"
LOG_TERMINAL_B = "/tmp/kr_terminal_b.log"

# ── Prompts especializados ──

PROMPT_ANALYZE_RESPONSE = """Eres un analista de ciberseguridad creando un video profesional.

DOMINION AI respondió esto en Terminal A:
--- RESPUESTA ---
{terminal_output}
--- FIN ---

Tema: "{topic}"

Genera comandos PRÁCTICOS para Terminal B basados en lo que DOMINION sugirió.
Usa SOLO estos targets legales: scanme.nmap.org, testphp.vulnweb.com, httpbin.org, badssl.com, google.com

REGLAS:
- Comandos LIMPIOS (sin kr-cli wrapper)
- NUNCA: exit, quit, Ctrl+C, kill, shutdown
- Solo comandos que producen output visual interesante
- Máximo 3-4 comandos

Responde SOLO JSON:
[
  {{"tipo": "ejecucion", "voz": "Descripción corta", "comando_real": "comando"}},
  {{"tipo": "pausa", "voz": "Analizando", "espera": 4.0}}
]"""

PROMPT_ANALYZE_CMD_OUTPUT = """Eres un narrador de videos de ciberseguridad.
Se ejecutó este comando en Terminal B:

COMANDO: {command}
OUTPUT:
{output}

Genera un resumen técnico para narrar en voz (TTS).
REGLAS:
- NO digas el comando (ya se ve en pantalla)
- Explica QUÉ significan los resultados en 2-3 frases
- Si hay error: explica por qué y qué haremos
- Máximo 40 palabras

Responde SOLO JSON:
{{"resumen_tts": "...", "tiene_error": false, "comando_corregido": "", "explicacion_error": ""}}"""

PROMPT_GENERATE_FOLLOWUP = """Eres un experto creando un video de ciberseguridad CONTINUO y profesional.

Tema: "{topic}" | Ciclo {cycle}/{total_cycles}

LO QUE YA PASÓ:
- Preguntamos a DOMINION: {previous_question}
- DOMINION dijo: {dominion_response}
- Ejecutamos en Terminal B: {executed_commands}
- RESULTADOS de Terminal B:
{terminal_b_output}

Genera la SIGUIENTE pregunta para DOMINION.
DEBE:
1. Referenciar los resultados de Terminal B
2. Profundizar o explorar un aspecto nuevo
3. Ser concisa (1-2 líneas, se tipea en terminal)

Responde SOLO JSON:
{{"pregunta": "La siguiente pregunta"}}

IMPORTANTE: La pregunta NO debe contener signos de interrogación, exclamación, asteriscos
ni caracteres especiales. Se tipea directamente en una terminal Linux."""


def strip_ansi(text: str) -> str:
    """Elimina códigos ANSI de escape del texto."""
    return re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', text)


def read_log_file(filepath: str, last_n_lines: int = 40) -> str:
    """Lee las últimas N líneas de un log, limpiando ANSI."""
    try:
        if not os.path.exists(filepath):
            return ""
        with open(filepath, 'r', errors='replace') as f:
            lines = f.readlines()
        # Últimas N líneas, limpias
        recent = lines[-last_n_lines:] if len(lines) > last_n_lines else lines
        clean = [strip_ansi(line).rstrip() for line in recent]
        # Filtrar líneas vacías consecutivas
        result = []
        prev_empty = False
        for line in clean:
            if line.strip() == "":
                if not prev_empty:
                    result.append("")
                prev_empty = True
            else:
                result.append(line)
                prev_empty = False
        return '\n'.join(result).strip()
    except Exception:
        return ""


class DynamicDirectorEngine:
    """Director dinámico v2 — lee terminales via log files."""

    def __init__(self, main_app, topic: str, duration_min: int, workspace_dir: str):
        self.app = main_app
        self.topic = topic
        self.duration_min = max(1, min(30, duration_min))
        self.workspace_dir = workspace_dir
        self.tts = TTSEngine(workspace_dir, "audio_dynamic")
        self.is_running = False

        self.wid_a = None
        self.wid_b = None
        self.typing_delay = 120
        self.obs = OBSController()
        self.floating_ctrl = None
        self.ai_engine = None

        self.current_cycle = 0
        self.total_cycles = max(2, duration_min // 3)

        # Callback para insertar JSON en los editores de la UI
        self.on_json_terminal_a = None  # callback(json_str)
        self.on_json_terminal_b = None  # callback(json_str)

    def start(self):
        self.is_running = True
        # Limpiar logs anteriores
        for f in [LOG_TERMINAL_A, LOG_TERMINAL_B]:
            try:
                open(f, 'w').close()
            except Exception:
                pass
        threading.Thread(target=self._run_dynamic_sequence, daemon=True).start()

    def stop(self):
        self.is_running = False
        self.tts.stop_current()

    # ─── Command Completion Detection ───

    def _wait_for_command_done(self, log_path: str, max_wait: int = 25) -> str:
        """Monitorea log hasta que el output deje de crecer por 1.5s."""
        prev_size = 0
        stable_count = 0
        for _ in range(max_wait * 2):
            if not self.is_running:
                break
            time.sleep(0.5)
            try:
                size = os.path.getsize(log_path)
            except OSError:
                size = 0
            if size == prev_size:
                stable_count += 1
                if stable_count >= 3:
                    break
            else:
                stable_count = 0
                prev_size = size
        return read_log_file(log_path, 25)

    def _analyze_cmd_output(self, command: str, output: str) -> dict:
        """AI analiza output de comando → resumen TTS + detección de error."""
        if not self.ai_engine or not self.ai_engine.chat_session:
            return {"resumen_tts": "", "tiene_error": False}
        try:
            prompt = PROMPT_ANALYZE_CMD_OUTPUT.format(
                command=command,
                output=output[-2000:] if len(output) > 2000 else output
            )
            response = self.ai_engine.chat_session.send_message(prompt)
            data = self.ai_engine.extraer_json(response.text)
            if isinstance(data, dict):
                return data
            elif isinstance(data, list) and len(data) > 0:
                return data[0]
            return {"resumen_tts": "", "tiene_error": False}
        except Exception:
            return {"resumen_tts": "", "tiene_error": False}

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
            try:
                subprocess.run(['xdotool', 'windowsize', wid, str(w), str(h)],
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

    # ─── Lectura NO intrusiva de terminales ───

    def _read_terminal_a(self, lines=40) -> str:
        """Lee Terminal A desde archivo de log — NUNCA interrumpe kr-clidn."""
        return read_log_file(LOG_TERMINAL_A, lines)

    def _read_terminal_b(self, lines=30) -> str:
        """Lee Terminal B desde archivo de log."""
        return read_log_file(LOG_TERMINAL_B, lines)

    # ─── Insertar JSON en editores ───

    def _show_json_a(self, json_data):
        """Muestra el JSON de Terminal A en el editor izquierdo."""
        if self.on_json_terminal_a and json_data:
            text = json.dumps(json_data, indent=2, ensure_ascii=False)
            try:
                self.app.after(0, self.on_json_terminal_a, text)
            except Exception:
                pass

    def _show_json_b(self, json_data):
        """Muestra el JSON de Terminal B en el editor derecho."""
        self._flog(f"  JSON B: callback={'✅' if self.on_json_terminal_b else '❌'} data={len(json_data) if json_data else 0}", "info")
        if self.on_json_terminal_b and json_data:
            text = json.dumps(json_data, indent=2, ensure_ascii=False)
            try:
                self.app.after(0, self.on_json_terminal_b, text)
                self._flog("  Editor B actualizado ✅", "ok")
            except Exception as e:
                self._flog(f"  Error Editor B: {e}", "error")

    # ─── SECUENCIA PRINCIPAL ───

    def _run_dynamic_sequence(self):
        self._log("Director", f"🎬 MODO DINÁMICO v2 — {self.topic}")
        self._log("Director", f"📐 {self.duration_min} min | {self.total_cycles} ciclos")
        self._flog(f"Dinámico: {self.topic} ({self.duration_min}min)", "ok")

        if not self.wid_a or not self.wid_b:
            self._log("Error", "❌ No hay terminales.")
            self.is_running = False
            return

        self._resize_window(self.wid_a)
        self._resize_window(self.wid_b)

        # ── OBS ──
        obs_ok = self.obs.connect()
        if obs_ok:
            scenes = self.obs._get_scene_names()
            self._flog(f"OBS: {scenes}", "ok")
            self.obs.start_recording()
            time.sleep(1.0)
            self.obs.switch_scene("Terminal-A")
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

        # ── Boot kr-clidn en Terminal A ──
        self._flog("Boot: venv + kr-clidn (log activo)", "info")
        self._focus_window(self.wid_a)

        # 1. Iniciar script para capturar output (SIN -c, abre subshell)
        self._type_text(self.wid_a, f"script -q -f {LOG_TERMINAL_A}", delay_ms=30)
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

        # 4. Lanzar kr-clidn como comando normal (NO como -c subproceso)
        self._type_text(self.wid_a, "kr-clidn", delay_ms=80)
        self._send_key(self.wid_a, "Return")

        self._flog("Esperando splash kr-clidn...", "wait")
        time.sleep(5.0)
        self._wait_continue("Dashboard KR-CLIDN listo?")
        self._flog("Dashboard ✅", "ok")

        # ── Navegar al chat ──
        if obs_ok:
            self.obs.switch_scene("Terminal-A")

        self._flog("Menú: 1 → Consola AI", "info")
        self._type_text(self.wid_a, "1", delay_ms=150)
        self._send_key(self.wid_a, "Return")
        time.sleep(3.0)
        self._wait_continue("Submenú Consola AI")

        self._flog("N → Nuevo Chat", "info")
        self._type_text(self.wid_a, "N", delay_ms=150)
        self._send_key(self.wid_a, "Return")
        time.sleep(2.0)

        title = self.topic[:50]
        self._type_text(self.wid_a, title)
        self._send_key(self.wid_a, "Return")
        time.sleep(3.0)
        self._wait_continue("Chat creado")

        # ── CICLOS DINÁMICOS SINCRONIZADOS ──
        prev_question = ""
        dom_summary = ""
        tb_summary = ""
        exec_cmds = ""

        for cycle in range(1, self.total_cycles + 1):
            if not self.is_running:
                break

            self.current_cycle = cycle
            self._log("Director", f"═══ CICLO {cycle}/{self.total_cycles} ═══")
            self._flog(f"═══ CICLO {cycle}/{self.total_cycles} ═══", "step")

            if self.floating_ctrl:
                self.floating_ctrl.set_progress(cycle, self.total_cycles)

            # ══════════════════════════════════════
            # FASE A: Preguntar a DOMINION
            # ══════════════════════════════════════
            if obs_ok:
                self.obs.switch_scene("Terminal-A")

            if cycle == 1:
                question = f"Explicame paso a paso como hacer {self.topic} con ejemplos practicos de comandos"
            else:
                question = self._generate_followup(
                    prev_question, dom_summary, exec_cmds, tb_summary, cycle
                )

            # Sanitizar: remover caracteres que zsh interpreta como glob
            question = question.replace("?", "").replace("!", "").replace("*", "")
            question = question.replace("¿", "").replace("¡", "")
            question = question.replace("[", "(").replace("]", ")").replace("`", "'")

            self._flog(f"  Q: {question[:45]}...", "info")
            self._focus_window(self.wid_a)
            time.sleep(0.5)
            self._type_text(self.wid_a, question)
            time.sleep(1.0)
            self._send_key(self.wid_a, "Return")

            self._flog("  Esperando DOMINION...", "wait")
            time.sleep(12.0)

            self._wait_continue(f"DOMINION respondió (Ciclo {cycle})")
            prev_question = question

            # ══════════════════════════════════════
            # FASE B: Leer Terminal A (desde archivo)
            # ══════════════════════════════════════
            self._flog("  📖 Leyendo log Terminal A...", "info")
            dom_summary = self._read_terminal_a(50)
            line_count = len(dom_summary.split('\n'))
            self._log("Director", f"📖 Terminal A: {line_count} líneas (desde log)")
            self._flog(f"  Terminal A: {line_count} líneas ✅", "ok")

            # ══════════════════════════════════════
            # FASE C: AI genera comandos para Terminal B
            # ══════════════════════════════════════
            self._flog("  🤖 AI analizando respuesta...", "wait")
            commands_json = self._analyze_and_generate_commands(dom_summary)

            if commands_json:
                self._flog(f"  {len(commands_json)} acciones generadas", "ok")
                self._show_json_b(commands_json)

                # ══════════════════════════════════════
                # FASE D: Ejecutar en Terminal B (ADAPTATIVO)
                # ══════════════════════════════════════
                if obs_ok:
                    self.obs.switch_scene("Terminal-B")

                executed_list = []
                for ci, cmd in enumerate(commands_json):
                    if not self.is_running:
                        break

                    if cmd.get("tipo") == "ejecucion":
                        comando = cmd.get("comando_real", "")
                        if comando:
                            self._flog(f"  B> {comando[:40]}", "ok")
                            self._focus_window(self.wid_b)
                            self._type_text(self.wid_b, comando)
                            time.sleep(0.3)
                            self._send_key(self.wid_b, "Return")

                            # Detectar fin del comando automáticamente
                            self._flog("  ⏳ Esperando output...", "wait")
                            cmd_output = self._wait_for_command_done(LOG_TERMINAL_B, max_wait=25)
                            executed_list.append(comando)

                            # AI analiza resultado → narrar resumen
                            analysis = self._analyze_cmd_output(comando, cmd_output)
                            resumen = analysis.get("resumen_tts", "")
                            if resumen:
                                self._flog(f"📝 {resumen}", "info")
                                num_words = len(resumen.split())
                                time.sleep(max(1.5, num_words / 2.5))

                            # Si hay error → corregir automáticamente
                            if analysis.get("tiene_error") and analysis.get("comando_corregido"):
                                error_exp = analysis.get("explicacion_error", "")
                                if error_exp:
                                    self._flog(f"📝 {error_exp}", "info")
                                corrected = analysis["comando_corregido"]
                                self._flog(f"  🔧 {corrected[:40]}", "ok")
                                self._focus_window(self.wid_b)
                                self._type_text(self.wid_b, corrected)
                                time.sleep(0.3)
                                self._send_key(self.wid_b, "Return")
                                fix_out = self._wait_for_command_done(LOG_TERMINAL_B)
                                fix_a = self._analyze_cmd_output(corrected, fix_out)
                                if fix_a.get("resumen_tts"):
                                    self._flog(f"📝 {fix_a['resumen_tts']}", "info")
                                executed_list.append(corrected)

                            self._wait_continue(f"Cmd {ci+1} listo")

                    elif cmd.get("tipo") == "pausa":
                        time.sleep(cmd.get("espera", 3.0))

                exec_cmds = ", ".join(executed_list[:5])

                # ══════════════════════════════════════
                # FASE E: Leer Terminal B (desde archivo)
                # ══════════════════════════════════════
                self._flog("  📖 Leyendo log Terminal B...", "info")
                tb_summary = self._read_terminal_b(35)
                tb_lines = len(tb_summary.split('\n'))
                self._flog(f"  Terminal B: {tb_lines} líneas ✅", "ok")
            else:
                self._flog("  Sin comandos generados", "error")
                tb_summary = ""
                exec_cmds = ""

            # Volver a Terminal A para siguiente ciclo
            if obs_ok and self.is_running:
                self.obs.switch_scene("Terminal-A")

            # Preparar para siguiente pregunta (NO enviar Return — chat ya espera input)
            if cycle < self.total_cycles and self.is_running:
                self._focus_window(self.wid_a)
                self._wait_continue(f"Listo para ciclo {cycle+1}")
                time.sleep(0.5)

        # ── FIN ──
        if obs_ok:
            time.sleep(2.0)
            self.obs.stop_recording()
            self.obs.disconnect()

        self.is_running = False
        self._log("Director", f"✅ Video dinámico de {self.duration_min} min — {self.total_cycles} ciclos ¡Listo!")
        if self.floating_ctrl:
            self.floating_ctrl.notify_finished()

    # ─── AI: Generate commands from DOMINION response ───

    def _analyze_and_generate_commands(self, terminal_output: str) -> list:
        if not self.ai_engine or not self.ai_engine.chat_session:
            self._flog("  ❌ AI Engine no configurado", "error")
            return []
        try:
            self._flog(f"  AI input: {len(terminal_output)} chars", "info")
            prompt = PROMPT_ANALYZE_RESPONSE.format(
                terminal_output=terminal_output[:3000],
                topic=self.topic
            )
            response = self.ai_engine.chat_session.send_message(prompt)
            data = self.ai_engine.extraer_json(response.text)
            if data:
                self._flog(f"  AI generó {len(data)} acciones ✅", "ok")
            else:
                self._flog("  AI no generó JSON válido", "error")
                self._log("Director", f"📝 AI raw: {response.text[:200]}")
            return data if data else []
        except Exception as e:
            self._log("Error", f"Error análisis: {e}")
            return []

    def _generate_followup(self, prev_q, dom_resp, exec_cmds, tb_out, cycle) -> str:
        if not self.ai_engine or not self.ai_engine.chat_session:
            return f"Profundiza más sobre {self.topic}"
        try:
            prompt = PROMPT_GENERATE_FOLLOWUP.format(
                topic=self.topic, cycle=cycle, total_cycles=self.total_cycles,
                previous_question=prev_q[:200],
                dominion_response=dom_resp[:1500],
                executed_commands=exec_cmds[:500],
                terminal_b_output=tb_out[:1500]
            )
            response = self.ai_engine.chat_session.send_message(prompt)
            text = response.text.strip()
            text = re.sub(r'```json\s*', '', text)
            text = re.sub(r'```\s*', '', text).strip()
            try:
                data = json.loads(text)
                if isinstance(data, dict) and "pregunta" in data:
                    return data["pregunta"]
            except Exception:
                pass
            start = text.find('{')
            end = text.rfind('}')
            if start != -1 and end > start:
                try:
                    data = json.loads(text[start:end + 1])
                    if "pregunta" in data:
                        return data["pregunta"]
                except Exception:
                    pass
            return f"Muéstrame técnicas avanzadas de {self.topic}"
        except Exception as e:
            self._log("Error", f"Error followup: {e}")
            return f"Dame más ejemplos de {self.topic}"
