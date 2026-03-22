"""
course_engine.py — Orquestador de Cursos Profesionales de Ciberseguridad
KR-STUDIO - kr-clidn Academy
"""

import json
import logging
import threading
import os
import re
import typing
from typing import Callable

from kr_studio.core.course_prompts import (
    COURSE_PLANNER_PROMPT,
    COURSE_CHAPTER_PROMPT,
    COURSE_CHAPTER_OPERATIVO_PROMPT,
    MODULE_CLOSURE_PROMPT,
    COURSE_COMPLETION_PROMPT,
    PERSONA_KR_CLDN,
    PERSONA_ANONYMOPS,
    MARKETING_LAUNCH_PROMPT,
    MARKETING_VIDEOS_PROMPT,
    EJEMPLOS_EDUCATIVOS,
)

logger = logging.getLogger(__name__)


class CourseOrchestrator:
    """
    Orquestador de Cursos Profesionales.
    Encargado de la lógica de negocio para crear cursos de ciberseguridad
    con estructura progresiva, certificación y práctica en PC.
    """

    def __init__(self, ai_engine, workspace_dir: str):
        self.ai = ai_engine
        self.workspace_dir = workspace_dir
        self.projects_dir = os.path.join(workspace_dir, "projects")
        os.makedirs(self.projects_dir, exist_ok=True)

        self.master_course_structure: typing.Any = None
        self._course_dir: typing.Optional[str] = None
        self._is_rendering = False

    def _clean_folder_name(self, name: str) -> str:
        """Limpia un nombre para usarlo como carpeta."""
        import unicodedata

        name_norm = unicodedata.normalize("NFKD", name)
        name_ascii = name_norm.encode("ascii", "ignore").decode("ascii")
        clean_name = re.sub(r"[^a-zA-Z0-9_\-]", "_", name_ascii.replace(" ", "_"))
        clean_name = re.sub(r"_+", "_", clean_name).strip("_")[:50]
        return clean_name if clean_name else "unnamed"

    def set_course_name(self, topic: str):
        """Normaliza el nombre del curso y crea la carpeta principal."""
        clean_topic = self._clean_folder_name(topic)
        self._course_dir = os.path.join(self.projects_dir, f"curso_{clean_topic}")
        os.makedirs(self._course_dir, exist_ok=True)

        # Guardar estructura master
        self._modules_dir = os.path.join(self._course_dir, "modulos")
        os.makedirs(self._modules_dir, exist_ok=True)

        logger.info(f"Course dir: {self._course_dir}")
        return self._course_dir

    def get_module_dir(self, modulo_info: dict) -> str:
        """Crea y retorna la carpeta del módulo."""
        nro = modulo_info.get("nro", 0)
        titulo = modulo_info.get("titulo", f"modulo_{nro}")
        clean_titulo = self._clean_folder_name(titulo)
        module_dir = os.path.join(self._modules_dir, f"modulo_{nro}_{clean_titulo}")
        os.makedirs(module_dir, exist_ok=True)
        return module_dir

    def get_chapter_dir(self, modulo_info: dict, chapter_info: dict) -> str:
        """Crea y retorna la carpeta del capítulo."""
        nro_mod = modulo_info.get("nro", 0)
        nro_cap = chapter_info.get("nro", 0)
        titulo = chapter_info.get("titulo", f"capitulo_{nro_cap}")
        clean_titulo = self._clean_folder_name(titulo)

        # Primero crear la carpeta del módulo
        module_dir = self.get_module_dir(modulo_info)

        # Crear carpeta del capítulo
        chapter_dir = os.path.join(module_dir, f"cap_{nro_cap}_{clean_titulo}")
        os.makedirs(chapter_dir, exist_ok=True)
        return chapter_dir

    def _normalize_course_json(self, data: dict) -> dict:
        """Normaliza los campos del JSON del curso (inglés → español)."""
        # Mapeo de campos inglés → español
        field_map = {
            "modules": "modulos",
            "course_title": "titulo_curso",
            "module_title": "titulo",
            "chapter_title": "titulo",
            "chapter_objective": "objetivo",
            "chapter_type": "tipo",
            "num_chapters": "num_capitulos",
            "number": "nro",
            "level": "nivel",
            "duration": "duracion_total",
            "requirements": "requisitos",
        }

        result = {}
        for key, value in data.items():
            new_key = field_map.get(key, key)
            result[new_key] = value

        # Normalizar módulos
        if "modulos" in result and isinstance(result["modulos"], list):
            mod_field_map = {
                "modules": "modulos",
                "course_title": "titulo_curso",
                "module_title": "titulo",
                "number": "nro",
                "objective": "objetivo",
                "description": "descripcion",
                "module_description": "descripcion",
                "prerequisites": "prerrequisitos",
                "cta": "cta_modulo",
                "num_chapters": "num_capitulos",
                "chapters": "capitulos",
            }

            chapter_field_map = {
                "number": "nro",
                "chapter_title": "titulo",
                "chapter_objective": "objetivo",
                "chapter_type": "tipo",
                "description": "descripcion",
                "chapter_description": "descripcion",
            }

            normalized_mods = []
            for mod in result["modulos"]:
                norm_mod = {}
                for k, v in mod.items():
                    new_k = mod_field_map.get(k, k)
                    norm_mod[new_k] = v

                # Normalizar capítulos dentro del módulo
                if "capitulos" in norm_mod and isinstance(norm_mod["capitulos"], list):
                    norm_caps = []
                    for cap in norm_mod["capitulos"]:
                        norm_cap = {}
                        for k, v in cap.items():
                            new_k = chapter_field_map.get(k, k)
                            norm_cap[new_k] = v
                        norm_caps.append(norm_cap)
                    norm_mod["capitulos"] = norm_caps

                # Asegurar que cada módulo tenga número
                if "nro" not in norm_mod:
                    norm_mod["nro"] = len(normalized_mods) + 1

                normalized_mods.append(norm_mod)

            result["modulos"] = normalized_mods

        return result

    def generate_master_course_structure(
        self,
        topic: str,
        num_modules: int,
        nivel: str = "intermedio",
        modo: str = "DUAL AI",
        aspect: str = "16:9 (YouTube)",
        on_success: Callable = None,
        on_error: Callable = None,
    ):
        """Fase 1 (Planner): Crea la estructura JSON del curso en un thread."""
        # Guardar configuración para uso posterior
        self._nivel = nivel
        self._modo = modo
        self._aspect = aspect

        def _worker():
            try:
                modo_upper = modo.upper()
                if modo_upper == "SOLO TERM":
                    mode_hint = " (Enfoque 100% Terminal de Comandos, sin interfaces)."
                elif modo_upper == "OPERATIVO":
                    mode_hint = " (Estilo operativo profesional hacker anónimo. NUNCA menciones Docker o laboratorio. Trata todo como si ya estuviera corriendo.)"
                else:
                    mode_hint = " (Formato dual con chat inicial y ejecución)."
                format_hint = (
                    " IMPORTANTE: Formato VERTICAL (9:16) para Reels/TikTok, comandos compactos."
                    if "9:16" in aspect
                    else ""
                )

                prompt = COURSE_PLANNER_PROMPT.format(
                    tema=topic, nivel=nivel, num_modulos=num_modules
                )

                prompt += f"""
═══════════════════════════════════════════════════════════════════
ESTRUCTURA DEL CURSO (usar exactamente):
═══════════════════════════════════════════════════════════════════
El JSON debe tener esta estructura exacta:

{{
  "tipo": "curso",
  "titulo_curso": "Título del curso",
  "instructor": "kr-clidn",
  "nivel": "{nivel}",
  "duracion_total": "X horas",
  "objetivo_principal": "Lo que podrá hacer el estudiante",
  "modulos": [
    {{
      "nro": 1,
      "titulo": "Título del módulo",
      "objetivo": "Qué sabrá hacer al terminar",
      "descripcion": "Descripción persuasiva de 100-150 palabras para la landing page. Incluye qué aprenderá, por qué es importante y qué podrá hacer al terminar.",
      "prerrequisitos": [],
      "cta_modulo": "CTA para siguiente módulo",
      "capitulos": [
        {{
          "nro": 1,
          "titulo": "Título capítulo",
          "objetivo": "Objetivo del capítulo",
          "descripcion": "Descripción de 50-80 palabras para la página del capítulo en Hotmart. Persuasiva, muestra el valor.",
          "tipo": "teorico"
        }}
      ]
    }}
  ],
  "requisitos": ["Requisitos"],
  "bonus": ["Certificado kr-clidn", "Práctica en tu PC"]
}}

RESPUESTA: Solo el JSON, sin texto adicional.
{mode_hint}{format_hint}
"""

                self.ai._configure(self.ai.api_key)
                response = self.ai.chat(prompt)

                json_data = None
                start = response.find("{")
                end = response.rfind("}")

                if start != -1 and end != -1 and end > start:
                    json_str = response[start : end + 1]
                    print(f"[COURSE_ENGINE] JSON raw: {json_str[:300]}...")
                    json_data = json.loads(json_str)
                    print(
                        f"[COURSE_ENGINE] JSON parseado OK, keys: {list(json_data.keys())}"
                    )
                else:
                    raise ValueError(f"No se pudo extraer el JSON")

                # Normalizar campos de la IA (puede devolver en inglés o español)
                json_data = self._normalize_course_json(json_data)
                print(
                    f"[COURSE_ENGINE] JSON normalizado, keys: {list(json_data.keys())}"
                )
                print(f"[COURSE_ENGINE] Módulos: {len(json_data.get('modulos', []))}")

                self.master_course_structure = json_data
                self.set_course_name(json_data.get("titulo_curso", topic))

                # Crear carpetas para cada módulo
                modulos = json_data.get("modulos", [])
                for mod in modulos:
                    mod_dir = self.get_module_dir(mod)
                    print(f"[COURSE_ENGINE] Carpeta módulo creada: {mod_dir}")

                # Guardar estructura master
                path = os.path.join(self._course_dir, "master_course_structure.json")
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(json_data, f, indent=4, ensure_ascii=False)
                print(f"[COURSE_ENGINE] Master guardado en: {path}")

                on_success(json_data)

            except Exception as e:
                on_error(str(e))

        threading.Thread(target=_worker, daemon=True).start()

    def generate_chapter_json(
        self,
        target_ip: str,
        chapter: dict,
        modulo_info: dict,
        modo: str,
        aspect: str,
        on_success: Callable,
        on_error: Callable,
    ):
        """Fase 2 (Writer): Genera el JSON ejecutable de un capítulo específico del curso."""

        def _worker():
            try:
                nro_modulo = modulo_info.get("nro", 1)
                titulo_modulo = modulo_info.get("titulo", "")
                objetivo_modulo = modulo_info.get("objetivo", "")

                nro_capitulo = chapter.get("nro", 1)
                titulo_capitulo = chapter.get("titulo", "")
                objetivo_capitulo = chapter.get("objetivo", "")

                modo_upper = modo.upper()

                # Seleccionar prompt según el modo
                if modo_upper == "OPERATIVO":
                    # Reemplazar variables usando %s para evitar problemas con .format()
                    replacements = {
                        "{OPERATIVO}": PERSONA_ANONYMOPS,
                        "{curso_titulo}": self.master_course_structure.get(
                            "titulo_curso", ""
                        ),
                        "{modulo_nro}": str(nro_modulo),
                        "{modulo_titulo}": titulo_modulo,
                        "{capitulo_nro}": str(nro_capitulo),
                        "{capitulo_titulo}": titulo_capitulo,
                        "{capitulo_objetivo}": objetivo_capitulo,
                        "{laboratorio}": target_ip,
                    }
                    chapter_prompt = COURSE_CHAPTER_OPERATIVO_PROMPT
                    for key, value in replacements.items():
                        chapter_prompt = chapter_prompt.replace(key, str(value))
                    solo_instruction = ""
                elif modo_upper == "SOLO TERM":
                    chapter_prompt = COURSE_CHAPTER_PROMPT.format(
                        curso_titulo=self.master_course_structure.get(
                            "titulo_curso", ""
                        ),
                        modulo_nro=nro_modulo,
                        modulo_titulo=titulo_modulo,
                        capitulo_nro=nro_capitulo,
                        capitulo_titulo=titulo_capitulo,
                        capitulo_objetivo=objetivo_capitulo,
                        laboratorio=target_ip,
                        EJEMPLOS_EDUCATIVOS=EJEMPLOS_EDUCATIVOS,
                    )
                    solo_instruction = """
[MODO SOLO TERM ACTIVADO]
- Estás generando un guion para MODO SOLO (SOLO TERMINAL).
- IGNORA el flujo de 'MENU' y 'leer'.
- Empieza con 'narracion' introduciendo el tema.
- Usa 'ejecucion' para comandos reales en Terminal B.
- 'comando_visual' es OBLIGATORIO en cada ejecución.
- Cierra con 'narracion' de despedida.
"""
                else:
                    # DUAL AI - modo estándar
                    chapter_prompt = COURSE_CHAPTER_PROMPT.format(
                        curso_titulo=self.master_course_structure.get(
                            "titulo_curso", ""
                        ),
                        modulo_nro=nro_modulo,
                        modulo_titulo=titulo_modulo,
                        capitulo_nro=nro_capitulo,
                        capitulo_titulo=titulo_capitulo,
                        capitulo_objetivo=objetivo_capitulo,
                        laboratorio=target_ip,
                        EJEMPLOS_EDUCATIVOS=EJEMPLOS_EDUCATIVOS,
                    )
                    solo_instruction = ""

                format_instruction = ""
                if "9:16" in aspect:
                    format_instruction = """
[FORMATO 9:16 (VERTICAL)]
- Comandos compactos, usa | head -n 15
- Evita herramientas de texto muy grande
"""

                prompt = (
                    chapter_prompt
                    + f"""
{solo_instruction}{format_instruction}

OBJETIVO DEL CAPÍTULO: {objetivo_capitulo}
INSTRUCTOR: KR-CLDN (kr-clidn Academy)
"""
                )

                response = self.ai.chat(prompt)
                json_array = self.ai.extraer_json(response)

                print(
                    f"[COURSE_ENGINE] Modo: {modo_upper}, Prompt length: {len(prompt)}"
                )
                print(f"[COURSE_ENGINE] Response preview: {str(response)[:200]}...")

                if not json_array:
                    raise ValueError(
                        "La IA no devolvió un JSONArray válido para el capítulo."
                    )

                for step in json_array:
                    cmd = step.get("comando_visual", "")
                    if cmd:
                        forbidden_patterns = [
                            "rm -rf /",
                            "chmod 777 -R /",
                            "mkfs",
                            "dd if=/dev/zero of=/dev/sda",
                        ]
                        for pattern in forbidden_patterns:
                            if pattern in cmd:
                                step["comando_visual"] = (
                                    f"echo 'COMANDO BLOQUEADO: Patrón inseguro detectado'"
                                )
                                step["voz"] = (
                                    "He detectado un patrón inseguro y lo he bloqueado por seguridad."
                                )

                if not self._course_dir:
                    self.set_course_name("Curso_Desconocido")

                # Crear carpeta del capítulo y guardar JSON
                chapter_dir = self.get_chapter_dir(modulo_info, chapter)
                filename = "guion_capitulo.json"
                path = os.path.join(chapter_dir, filename)

                with open(path, "w", encoding="utf-8") as f:
                    json.dump(json_array, f, indent=4, ensure_ascii=False)

                print(f"[COURSE_ENGINE] JSON guardado en: {path}")

                on_success(nro_modulo, nro_capitulo, json_array, path)

            except Exception as e:
                on_error(chapter.get("nro", 0), str(e))

        threading.Thread(target=_worker, daemon=True).start()

    def generate_module_closure(
        self, modulo_info: dict, on_success: Callable, on_error: Callable
    ):
        """Genera la escena de cierre de módulo."""

        def _worker():
            try:
                prompt = MODULE_CLOSURE_PROMPT.format(
                    modulo_nro=modulo_info.get("nro", 1),
                    curso_titulo=self.master_course_structure.get("titulo_curso", ""),
                )

                response = self.ai.chat(prompt)
                json_data = self.ai.extraer_json(response)

                if not json_data:
                    raise ValueError("No se pudo generar el cierre del módulo")

                if not self._course_dir:
                    self.set_course_name("Curso_Desconocido")

                filename = f"modulo_{modulo_info.get('nro', 1)}_cierre.json"
                path = (
                    os.path.join(self._course_dir, filename) if self._course_dir else ""
                )
                if path:
                    with open(path, "w", encoding="utf-8") as f:
                        json.dump(json_data, f, indent=4, ensure_ascii=False)

                on_success(modulo_info.get("nro", 1), json_data, path)

            except Exception as e:
                on_error(str(e))

        threading.Thread(target=_worker, daemon=True).start()

    def generate_course_completion(self, on_success: Callable, on_error: Callable):
        """Genera la escena final de cierre del curso (certificado)."""

        def _worker():
            try:
                prompt = COURSE_COMPLETION_PROMPT.format(
                    curso_titulo=self.master_course_structure.get("titulo_curso", "")
                )

                response = self.ai.chat(prompt)
                json_data = self.ai.extraer_json(response)

                if not json_data:
                    raise ValueError("No se pudo generar el cierre del curso")

                if not self._course_dir:
                    self.set_course_name("Curso_Desconocido")

                path = (
                    os.path.join(self._course_dir, "cierre_curso.json")
                    if self._course_dir
                    else ""
                )
                if path:
                    with open(path, "w", encoding="utf-8") as f:
                        json.dump(json_data, f, indent=4, ensure_ascii=False)

                on_success(json_data, path)

            except Exception as e:
                on_error(str(e))

        threading.Thread(target=_worker, daemon=True).start()

    def process_course_loop(
        self,
        main_app,
        target_ip: str,
        modo: str,
        aspect: str,
        on_progress: Callable,
        on_finish: Callable,
        on_error: Callable,
    ):
        """Renderiza el Curso Completo secuencialmente."""
        if self._is_rendering:
            on_error("Ya hay un renderizado en curso.")
            return

        if (
            not self.master_course_structure
            or "modulos" not in self.master_course_structure
        ):
            on_error("No hay una estructura de curso.")
            return

        self._is_rendering = True

        def _worker():
            try:
                from kr_studio.core.master_director import MasterDirector, DirectorMode

                modulos = self.master_course_structure.get("modulos", [])

                for idx_mod, mod in enumerate(modulos):
                    if not self._is_rendering:
                        break

                    nro_mod = mod.get("nro", idx_mod + 1)
                    capitulos = mod.get("capitulos", [])

                    on_progress(f"Módulo {nro_mod}: {mod.get('titulo')}")

                    for idx_cap, cap in enumerate(capitulos):
                        if not self._is_rendering:
                            break

                        nro_cap = cap.get("nro", idx_cap + 1)
                        path = (
                            os.path.join(
                                self._course_dir,
                                f"modulo_{nro_mod}_capitulo_{nro_cap}.json",
                            )
                            if self._course_dir
                            else ""
                        )

                        if not os.path.exists(path):
                            on_error(f"Falta el JSON del capítulo {nro_mod}.{nro_cap}")
                            self._is_rendering = False
                            return

                        with open(path, "r", encoding="utf-8") as f:
                            json_data = json.load(f)

                        on_progress(f"  Capítulo {nro_cap}: {cap.get('titulo')}")

                        director_mode = (
                            DirectorMode.SOLO_TERM
                            if modo == "SOLO TERM"
                            else DirectorMode.DUAL_AI
                        )

                        director = MasterDirector(
                            guion=json_data,
                            mode=director_mode,
                            workspace_dir=main_app.workspace_dir,
                            typing_speed=main_app.typing_speed_pct,
                            wid_a=main_app.wid_a,
                            wid_b=main_app.wid_b,
                            project_name=f"modulo_{nro_mod}_cap_{nro_cap}",
                            aspect_ratio=aspect,
                            obs_password=main_app._load_env_value("OBS_PASSWORD", ""),
                            auto_record=True,
                        )
                        director.floating_ctrl = main_app._floating_ctrl

                        if main_app.wid_b:
                            director.x11.focus_window(main_app.wid_b)
                            director.x11.type_text(main_app.wid_b, "clear", delay_ms=20)
                            director.x11.send_key(main_app.wid_b, "Return")
                            import time

                            time.sleep(1)

                        main_app._active_director = director
                        director.run()

                        import time

                        time.sleep(3.0)

                    on_progress(f"Módulo {nro_mod} completado")

                on_finish(
                    "Curso completado exitosamente. ¡Felicidades por tu certificado kr-clidn!"
                )

            except Exception as e:
                on_error(str(e))
            finally:
                self._is_rendering = False

        threading.Thread(target=_worker, daemon=True).start()

    def cancel_render(self):
        self._is_rendering = False

    def generate_marketing_plan(
        self,
        on_success: Callable = None,
        on_error: Callable = None,
    ):
        """Genera el Marketing Launch Kit para Hotmart."""

        def _worker():
            try:
                if not self.master_course_structure:
                    raise ValueError("No hay estructura de curso generada.")

                curso_titulo = self.master_course_structure.get(
                    "titulo_curso", "Curso KR-CLDN"
                )
                nivel = self.master_course_structure.get("nivel", "intermedio")
                duracion = self.master_course_structure.get("duracion_total", "N/A")
                modulos = self.master_course_structure.get("modulos", [])

                modulos_info = ", ".join(
                    [
                        f"Módulo {m.get('nro', i + 1)}: {m.get('titulo', '')}"
                        for i, m in enumerate(modulos)
                    ]
                )
                objetivos_info = "; ".join(
                    [m.get("objetivo", "") for m in modulos if m.get("objetivo")]
                )

                from datetime import datetime

                fecha = datetime.now().strftime("%Y-%m-%d")
                timestamp = datetime.now().strftime("%Y%m%d%H%M")

                prompt = MARKETING_LAUNCH_PROMPT.format(
                    curso_titulo=curso_titulo,
                    nivel=nivel,
                    modulos_info=modulos_info,
                    objetivos_info=objetivos_info,
                    duracion=duracion,
                    fecha=fecha,
                    timestamp=timestamp,
                )

                self.ai._configure(self.ai.api_key)
                response = self.ai.chat(prompt)

                json_data = None
                start = response.find("{")
                end = response.rfind("}")
                if start != -1 and end != -1 and end > start:
                    json_str = response[start : end + 1]
                    json_data = json.loads(json_str)
                else:
                    raise ValueError("No se pudo extraer el JSON del marketing plan")

                if not self._course_dir:
                    self.set_course_name(curso_titulo)

                path = os.path.join(self._course_dir, "marketing_launch_plan.json")
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(json_data, f, indent=4, ensure_ascii=False)

                print(f"[COURSE_ENGINE] Marketing plan guardado en: {path}")

                if on_success:
                    on_success(json_data, path)

            except Exception as e:
                print(f"[COURSE_ENGINE] Error marketing: {e}")
                if on_error:
                    on_error(str(e))

        threading.Thread(target=_worker, daemon=True).start()

    def generate_marketing_videos(
        self,
        on_success: Callable = None,
        on_error: Callable = None,
    ):
        """Genera 15 videos de marketing (hooks, explicativos, retención, venta)."""

        def _worker():
            try:
                if not self.master_course_structure:
                    raise ValueError("No hay estructura de curso generada.")

                curso_titulo = self.master_course_structure.get(
                    "titulo_curso", "Curso KR-CLDN"
                )
                nivel = self.master_course_structure.get("nivel", "intermedio")
                duracion = self.master_course_structure.get("duracion_total", "N/A")
                modulos = self.master_course_structure.get("modulos", [])

                modulos_info = ", ".join(
                    [
                        f"Módulo {m.get('nro', i + 1)}: {m.get('titulo', '')}"
                        for i, m in enumerate(modulos)
                    ]
                )

                pain_points = []
                objetivos = []
                if hasattr(self, "_mkt_data") and self._mkt_data:
                    pain_points = self._mkt_data.get("pain_points", [])
                    objetivos = self._mkt_data.get("objetivos_curso_marketing", [])

                from datetime import datetime

                fecha = datetime.now().strftime("%Y-%m-%d")

                prompt = MARKETING_VIDEOS_PROMPT.format(
                    curso_titulo=curso_titulo,
                    nivel=nivel,
                    duracion=duracion,
                    modulos_info=modulos_info,
                    pain_points=", ".join(pain_points)
                    if pain_points
                    else "Ver tema específico",
                    objetivos=", ".join(objetivos)
                    if objetivos
                    else "Aprender ciberseguridad",
                    fecha=fecha,
                )

                self.ai._configure(self.ai.api_key)
                response = self.ai.chat(prompt)

                json_data = None
                start = response.find("{")
                end = response.rfind("}")
                if start != -1 and end != -1 and end > start:
                    json_str = response[start : end + 1]
                    json_data = json.loads(json_str)
                else:
                    raise ValueError("No se pudo extraer el JSON de videos")

                if not self._course_dir:
                    self.set_course_name(curso_titulo)

                mkt_dir = os.path.join(self._course_dir, "marketing")
                os.makedirs(mkt_dir, exist_ok=True)

                path = os.path.join(mkt_dir, "videos_marketing.json")
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(json_data, f, indent=4, ensure_ascii=False)

                print(f"[COURSE_ENGINE] Videos marketing guardados en: {path}")

                if on_success:
                    on_success(json_data, path)

            except Exception as e:
                print(f"[COURSE_ENGINE] Error videos marketing: {e}")
                if on_error:
                    on_error(str(e))

        threading.Thread(target=_worker, daemon=True).start()

    def get_course_tts_dir(self) -> str:
        """Retorna la carpeta de TTS del curso actual."""
        if self._course_dir:
            tts_dir = os.path.join(self._course_dir, "tts")
            os.makedirs(tts_dir, exist_ok=True)
            return tts_dir
        return os.path.join(self.workspace_dir, "voces_manuales")

    def load_marketing_plan(self) -> dict:
        """Carga el marketing plan desde archivo."""
        if not self._course_dir:
            return {}
        path = os.path.join(self._course_dir, "marketing_launch_plan.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                self._mkt_data = json.load(f)
                return self._mkt_data
        return {}

    def load_marketing_videos(self) -> dict:
        """Carga los videos de marketing desde archivo."""
        if not self._course_dir:
            return {}
        path = os.path.join(self._course_dir, "marketing", "videos_marketing.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def load_course_structure(self, course_path: str) -> dict:
        """Carga la estructura del curso desde una carpeta."""
        master_path = os.path.join(course_path, "master_course_structure.json")
        if os.path.exists(master_path):
            with open(master_path, "r", encoding="utf-8") as f:
                structure = json.load(f)
                self.master_course_structure = structure
                self._course_dir = course_path
                self._modules_dir = os.path.join(course_path, "modulos")
                return structure
        return {}

    def save_marketing_descriptions(self, descriptions: dict) -> str:
        """Guarda las descripciones de marketing del curso."""
        if not self._course_dir:
            raise ValueError("No hay curso activo")
        desc_dir = os.path.join(self._course_dir, "marketing")
        os.makedirs(desc_dir, exist_ok=True)
        path = os.path.join(desc_dir, "descripciones_marketing.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(descriptions, f, indent=2, ensure_ascii=False)
        return path

    def load_marketing_descriptions(self) -> dict:
        """Carga las descripciones de marketing del curso."""
        if not self._course_dir:
            return {}
        path = os.path.join(
            self._course_dir, "marketing", "descripciones_marketing.json"
        )
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def save_chapter_description(
        self, nro_mod: int, nro_cap: int, descripcion: str
    ) -> str:
        """Guarda la descripción de un capítulo específico."""
        if not self._course_dir:
            raise ValueError("No hay curso activo")

        module_dir = None
        if self.master_course_structure:
            for mod in self.master_course_structure.get("modulos", []):
                if mod.get("nro") == nro_mod:
                    module_dir = self.get_module_dir(mod)
                    break

        if not module_dir:
            module_dir = os.path.join(self._modules_dir, f"modulo_{nro_mod}")

        desc_path = os.path.join(module_dir, f"cap_{nro_cap}_descripcion.txt")
        with open(desc_path, "w", encoding="utf-8") as f:
            f.write(descripcion)
        return desc_path

    def load_chapter_description(self, nro_mod: int, nro_cap: int) -> str:
        """Carga la descripción de un capítulo específico."""
        if not self._course_dir:
            return ""

        # Buscar en estructura de carpetas
        for mod_folder in os.listdir(self._modules_dir):
            if mod_folder.startswith(f"modulo_{nro_mod}"):
                desc_path = os.path.join(
                    self._modules_dir, mod_folder, f"cap_{nro_cap}_descripcion.txt"
                )
                if os.path.exists(desc_path):
                    with open(desc_path, "r", encoding="utf-8") as f:
                        return f.read()
        return ""

    def get_course_description_full(self) -> str:
        """Genera la descripción completa del curso para Hotmart."""
        if not self.master_course_structure:
            return ""

        parts = []
        parts.append(f"#{self.master_course_structure.get('titulo_curso', 'Curso')}")
        parts.append("")
        parts.append(
            f"**Instructor:** {self.master_course_structure.get('instructor', 'kr-clidn')}"
        )
        parts.append(
            f"**Nivel:** {self.master_course_structure.get('nivel', 'Todos los niveles')}"
        )
        parts.append(
            f"**Duración:** {self.master_course_structure.get('duracion_total', 'Por definir')}"
        )
        parts.append("")
        parts.append(f"## 🎯 Objetivo Principal")
        parts.append(self.master_course_structure.get("objetivo_principal", ""))
        parts.append("")
        parts.append("## 📚 Contenido del Curso")

        for mod in self.master_course_structure.get("modulos", []):
            nro = mod.get("nro", "?")
            titulo = mod.get("titulo", "")
            descripcion = mod.get("descripcion", "")
            capitulos = mod.get("capitulos", [])

            parts.append(f"### Módulo {nro}: {titulo}")
            if descripcion:
                parts.append(descripcion)
            parts.append("")
            parts.append("**Capítulos:**")
            for cap in capitulos:
                cap_nro = cap.get("nro", "?")
                cap_titulo = cap.get("titulo", "")
                parts.append(f"- C{cap_nro}: {cap_titulo}")
            parts.append("")

        if self.master_course_structure.get("requisitos"):
            parts.append("## 📋 Requisitos")
            for req in self.master_course_structure.get("requisitos", []):
                parts.append(f"- {req}")
            parts.append("")

        if self.master_course_structure.get("bonus"):
            parts.append("## 🎁 Bonus")
            for bonus in self.master_course_structure.get("bonus", []):
                parts.append(f"- {bonus}")

        return "\n".join(parts)

    def get_module_description(self, nro_mod: int) -> str:
        """Obtiene la descripción de un módulo específico."""
        if not self.master_course_structure:
            return ""
        for mod in self.master_course_structure.get("modulos", []):
            if mod.get("nro") == nro_mod:
                return mod.get("descripcion", "")
        return ""

    def get_chapter_description(self, nro_mod: int, nro_cap: int) -> str:
        """Obtiene la descripción de un capítulo específico."""
        if not self.master_course_structure:
            return ""
        for mod in self.master_course_structure.get("modulos", []):
            if mod.get("nro") == nro_mod:
                for cap in mod.get("capitulos", []):
                    if cap.get("nro") == nro_cap:
                        return cap.get("descripcion", "")
        return ""
