"""
solo_director.py — Director Solo (Terminal B únicamente)
Sistema ADAPTATIVO: ejecuta → detecta fin → AI analiza output → narra resumen → siguiente.
Si hay error, AI explica y genera comando corregido.
"""
import threading
import subprocess
import time
import os
import json
from kr_studio.core.tts_engine import TTSEngine
from kr_studio.core.obs_controller import OBSController
from kr_studio.core.dynamic_director import LOG_TERMINAL_B, read_log_file

# ── Prompt: Generar plan de comandos ──

PROMPT_SOLO_PLAN = """Eres un experto en ciberseguridad creando un video profesional EN VIVO.

Tema: "{topic}"
Ciclo {cycle}/{total_cycles}.

{context_block}

Genera un plan de comandos para ejecutar en terminal Linux.
{wrapper_instruction}

TARGETS AUTORIZADOS: scanme.nmap.org, testphp.vulnweb.com, httpbin.org, badssl.com, google.com

REGLAS:
- Comandos con output VISUAL interesante para video
- NUNCA: exit, quit, Ctrl+C, kill, shutdown, clear, reboot
- Progresión logica: reconocimiento → análisis → explotación
- Cada comando enseña algo diferente
- NO incluyas texto de narración — eso se genera después

Responde SOLO JSON (lista de comandos):
[
  {{"comando": "nmap -sV scanme.nmap.org", "descripcion_corta": "Escaneo de servicios"}},
  {{"comando": "curl -I httpbin.org", "descripcion_corta": "Headers HTTP"}}
]

Genera 3-5 comandos por ciclo."""


# ── Prompt: Analizar output de comando ──

PROMPT_ANALYZE_OUTPUT = """Eres un narrador experto de videos de ciberseguridad.
Acabas de ejecutar este comando en vivo:

COMANDO: {command}
OUTPUT (últimas líneas):
{output}

Genera un RESUMEN TÉCNICO para narrar en voz (TTS) en el video.

REGLAS:
1. NO digas el comando textual (ya se ve en pantalla)
2. Explica QUÉ significan los resultados en 2-3 frases
3. Si hay ERROR: explica por qué ocurrió y qué haremos diferente
4. Usa lenguaje profesional pero accesible
5. Máximo 40 palabras (se lee en voz alta)

Responde SOLO JSON:
{{
  "resumen_tts": "Los resultados muestran 3 puertos abiertos...",
  "tiene_error": false,
  "comando_corregido": "",
  "explicacion_error": ""
}}

Si tiene_error=true, incluye un comando_corregido y explicacion_error."""


class SoloDirectorEngine:
    """Director Solo — usa SOLO Terminal B. Flujo adaptativo."""

    def __init__(self, main_app, topic: str, duration_min: int, workspace_dir: str):
        self.app = main_app
        self.topic = topic
        self.duration_min = max(1, min(30, duration_min))
        self.workspace_dir = workspace_dir
        self.tts = TTSEngine(workspace_dir, "audio_solo")
        self.is_running = False

        self.wid_b = None  # SOLO Terminal B
        self.typing_delay = 120
        self.obs = OBSController()
        self.floating_ctrl = None
        self.ai_engine = None

        self.use_wrapper = False
        self.current_cycle = 0
        self.total_cycles = max(2, duration_min // 2)

        self.on_json_terminal_b = None
        self.json_data = None  # Agregado para soportar ejecución de scripts pre-generados
        self.timestamps = {
            "menu": [],
            "ejecucion": [],
            "pausa": []
        }
        self._start_wall = 0.0

    def start(self):
        self.is_running = True
        try:
            self._log("Debug", f"SoloDirectorEngine.start() llamado. json_data existe: {self.json_data is not None}")
            if self.json_data:
                self._log("Debug", f"Scenes in json_data: {len(self.json_data)}")
            open(LOG_TERMINAL_B, 'w').close()
        except Exception:
            pass
        threading.Thread(target=self._run_solo_sequence, daemon=True).start()

    def stop(self):
        self.is_running = False
        self.tts.stop_current()

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

    # ─── Command Completion Detection ───

    def _wait_for_command_done(self, max_wait: int = 30) -> str:
        """
        Monitorea el log de Terminal B.
        Cuando el output deja de crecer por 1.5s → comando terminó.
        Retorna las últimas líneas del output.
        """
        prev_size = 0
        stable_count = 0

        for _ in range(max_wait * 2):  # check every 0.5s
            if not self.is_running:
                break
            time.sleep(0.5)
            try:
                size = os.path.getsize(LOG_TERMINAL_B)
            except OSError:
                size = 0

            if size == prev_size:
                stable_count += 1
                if stable_count >= 3:  # 1.5s sin cambios
                    break
            else:
                stable_count = 0
                prev_size = size

        return read_log_file(LOG_TERMINAL_B, 25)

    # ─── AI: Post-Command Analysis ───

    def _analyze_output(self, command: str, output: str) -> dict:
        """AI analiza el output de un comando → resumen TTS + detección de error."""
        if not self.ai_engine or not self.ai_engine.chat_session:
            return {"resumen_tts": "", "tiene_error": False}

        try:
            prompt = PROMPT_ANALYZE_OUTPUT.format(
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

        except Exception as e:
            self._log("Error", f"Error análisis: {e}")
            return {"resumen_tts": "", "tiene_error": False}

    # ─── AI: Generate Command Plan ───

    def _generate_plan(self, context_block: str, wrapper_instruction: str, cycle: int) -> list:
        if not self.ai_engine or not self.ai_engine.chat_session:
            self._flog("  ❌ AI no configurado", "error")
            return []
        try:
            prompt = PROMPT_SOLO_PLAN.format(
                topic=self.topic,
                cycle=cycle,
                total_cycles=self.total_cycles,
                context_block=context_block,
                wrapper_instruction=wrapper_instruction
            )
            response = self.ai_engine.chat_session.send_message(prompt)
            data = self.ai_engine.extraer_json(response.text)
            return data if data else []
        except Exception as e:
            self._log("Error", f"Error AI: {e}")
            return []

    # ─── Wrapper ───

    def _wrap_command(self, cmd: str) -> str:
        if self.use_wrapper:
            return f"kr-cli {cmd}"
        return cmd

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

        self._start_wall = time.monotonic()
        self._resize_window(self.wid_b)

        # ── OBS (solo Terminal-B) ──
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
            time.sleep(0.5)

        # ── SI HAY JSON DATA PRE-GENERADO ──
        if self.json_data:
            self._log("Debug", "Tomando ruta de EJECUCIÓN LINEAL DE JSON")
            self._flog(f"Iniciando guion: {len(self.json_data)} escenas", "info")
            total = len(self.json_data)
            for i, escena in enumerate(self.json_data):
                if not self.is_running:
                    break
                
                self.current_cycle = i + 1
                if self.floating_ctrl:
                    self.floating_ctrl.set_progress(self.current_cycle, total)
                
                self._ejecutar_escena_json(escena, i)
            
            self.tts.speak_and_wait("Secuencia completada. Revisar logs detallados.")
            
        else:
            self._log("Error", "❌ El JSON de Terminal B está vacío o no se leyó correctamente. Ejecución abortada.")
            self._flog("JSON no detectado.", "error")
            self.tts.speak_and_wait("Error crítico. No se ha provisto un guion válido para el modo Solo.")

        # ── FIN ──
        if obs_ok:
            time.sleep(2.0)
            self.obs.stop_recording()
            self.obs.disconnect()

        self.tts.cleanup()
        self.is_running = False
        self._log("Director", f"✅ Video Solo completado.")
        if self.floating_ctrl:
            self.floating_ctrl.notify_finished()

    # ── Ejecución Lineal JSON para Modo Solo ──
    def _ejecutar_escena_json(self, escena: dict, index: int):
        tipo = escena.get("tipo", "")
        voz = escena.get("voz", "")

        self._log("Director", f"▶ Escena {index+1} [{tipo}]")
        self._flog(f"Escena {index+1}: {tipo}", "step")

        if tipo == "narracion":
            if voz:
                # Generar un hash único basado en el texto para evitar que se reproduzcan audios viejos
                import hashlib
                text_hash = hashlib.md5(voz.encode('utf-8')).hexdigest()[:8]
                path = os.path.join(self.workspace_dir, "audio_solo", f"audio_{index}_{text_hash}.mp3")
                
                if not os.path.exists(path):
                    self._flog("Generando audio...", "info")
                    from kr_studio.core.audio_engine import AudioEngine
                    AudioEngine().generar_audio(voz, path)
                self.tts.play_audio(path)

        elif tipo == "ejecucion":
            cmd = escena.get("comando_visual", "")
            if not cmd:
                fallback = escena.get("voz", "")
                # Si el fallback es un párrafo largo (narración accidental), usar ls en su lugar
                if len(fallback.split()) > 5:
                    cmd = "ls -l"
                else:
                    cmd = fallback if fallback else "ls -l"

            # Registrar timestamp en ejecución de comando
            rel_time = time.monotonic() - self._start_wall
            self.timestamps["ejecucion"].append(round(rel_time, 2))

            cmd_final = self._wrap_command(cmd)
            self._type_text(self.wid_b, cmd_final)
            time.sleep(1.0)
            self._send_key(self.wid_b, "Return")
            
            # 1. Reproducir la voz DESPUÉS de lanzar el comando, mientras corre
            if voz:
                import hashlib
                text_hash = hashlib.md5(voz.encode('utf-8')).hexdigest()[:8]
                path = os.path.join(self.workspace_dir, "audio_solo", f"audio_{index}_{text_hash}.mp3")
                
                if not os.path.exists(path):
                    from kr_studio.core.audio_engine import AudioEngine
                    AudioEngine().generar_audio(voz, path)
                self.tts.play_audio_bg(path)

            # 2. Esperar a que el comando termine
            self._flog("  ⏳ Esperando output...", "wait")
            cmd_output = self._wait_for_command_done(20)
            time.sleep(1.5)

            # 3. Analizar la salida por si hubo error
            self._flog("  🧠 AI analizando salida...", "info")
            analysis = self._analyze_output(cmd, cmd_output)
            
            tiene_error = analysis.get("tiene_error", False)
            cmd_corregido = analysis.get("comando_corregido", "")
            error_exp = analysis.get("explicacion_error", "")
            resumen = analysis.get("resumen_tts", "")

            # Guardar el análisis en el chat explícitamente sin tocar el JSON
            if resumen:
                self._log("AI Analysis", f"📝 Resultado: {resumen}")

            if tiene_error and cmd_corregido:
                self._log("AI Analysis", f"⚠ Error detectado. Acción: {error_exp}")
                self._flog(f"  ⚠ Error → corrigiendo", "error")
                
                # Explicar el error
                if error_exp:
                    self.tts.speak_and_wait(error_exp)
                
                # Ejecutar comando corregido
                corrected = self._wrap_command(cmd_corregido)
                self._flog(f"  🔧 {corrected[:45]}", "ok")
                self._type_text(self.wid_b, corrected)
                time.sleep(0.3)
                self._send_key(self.wid_b, "Return")
                
                fix_output = self._wait_for_command_done(max_wait=25)
                
                # Analizar resultado del parche (opcional, sin bucle infinito)
                fix_analysis = self._analyze_output(cmd_corregido, fix_output)
                fix_resumen = fix_analysis.get("resumen_tts", "")
                if fix_resumen:
                    self._log("AI Analysis", f"🛠 Fix: {fix_resumen}")
                    self.tts.speak_and_wait(fix_resumen)

        elif tipo == "pausa":
            delay = float(escena.get("espera", 3.0))
            rel_time = time.monotonic() - self._start_wall
            self.timestamps["pausa"].append(round(rel_time, 2))
            
            self._flog(f"  Pausa: {delay}s", "wait")
            time.sleep(delay)

