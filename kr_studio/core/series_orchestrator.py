import json
import logging
import threading
import time
import os
import re
import typing
from typing import Callable, List

logger = logging.getLogger(__name__)

class SeriesOrchestrator:
    """
    Orquestador de Series y Películas.
    Encargado de la lógica de negocio (Fase 1: Planner, Fase 2: Writer)
    y del flujo de encadenamiento (Renderizar Serie Completa).
    """
    def __init__(self, ai_engine, workspace_dir: str):
        self.ai = ai_engine
        self.workspace_dir = workspace_dir
        self.projects_dir = os.path.join(workspace_dir, "projects")
        os.makedirs(self.projects_dir, exist_ok=True)
        
        self.master_structure: typing.Any = None
        self._series_dir: typing.Optional[str] = None
        self._is_rendering = False
        
    def set_series_name(self, topic: str):
        """
        Normaliza el nombre de la serie para carpeta.
        IMPORTANTE: limita a 40 chars para evitar [Errno 36] File name too long.
        El path base ya puede ser largo (/home/user/.../workspace/projects/).
        """
        # Quitar caracteres especiales y acentos
        import unicodedata
        topic_norm = unicodedata.normalize("NFKD", topic)
        topic_ascii = topic_norm.encode("ascii", "ignore").decode("ascii")
        clean_topic = re.sub(r"[^a-zA-Z0-9_\-]", "_", topic_ascii.replace(" ", "_"))
        # Colapsar guiones bajos múltiples y truncar a 40 chars
        clean_topic = re.sub(r"_+", "_", clean_topic).strip("_")[:40]  # type: ignore
        if not clean_topic:
            clean_topic = "Serie_Sin_Titulo"
        self._series_dir = os.path.join(self.projects_dir, clean_topic)
        os.makedirs(self._series_dir, exist_ok=True)
        logger.info(f"Series dir: {self._series_dir}")
        return self._series_dir

    def generate_master_structure(self, topic: str, num_chapters: int, mode: str, aspect: str, on_success: Callable, on_error: Callable):
        """Fase 1 (Planner): Crea la estructura JSON de la serie en un thread."""
        def _worker():
            try:
                mode_hint = " (El enfoque técnico será 100% Terminal de Comandos, sin interfaces, sin navegar el dashboard)." if mode == "SOLO TERM" else " (Formato dual con chat inicial y posterior ejecución)."
                format_hint = " IMPORTANTE: El formato de video será VERTICAL (9:16) para Reels/TikTok, los comandos planificados deben imprimir resultados compactos, evita herramientas de texto muy grande." if "9:16" in aspect else ""
                
                system_prompt = (
                    "Actúa como un Director Profesional de Series de Ciberseguridad y Experto en Copywriting Viral. "
                    "Se te dará un TEMA y un NÚMERO DE CAPÍTULOS. "
                    f"Tu objetivo es crear una estructura lógica y progresiva para la serie{mode_hint}{format_hint}\n"
                    "REGLAS DE PSICOLOGÍA Y RETENCIÓN:\n"
                    "1. Ganchos (Hooks): Cada capítulo debe tener un objetivo que suene irresistible.\n"
                    "2. Continuidad: El capítulo N debe sentirse como la secuela directa del N-1.\n"
                    "3. CTAs Dinámicos: Planea llamados a la acción (ej: 'Guarda este reel', 'Sígueme para ver la parte 2').\n"
                    "CADA CAPÍTULO debe tener un objetivo claro, accionable y diseñado para retener al espectador.\n\n"
                    "DEVUELVE ÚNICAMENTE un JSON válido con esta estructura estricta:\n"
                    "{\n"
                    "  \"titulo_serie\": \"El mejor título para la serie (Atractivo y corto)\",\n"
                    "  \"capitulos\": [\n"
                    "    {\"nro\": 1, \"titulo\": \"...\", \"objetivo\": \"... (incluir gancho y CTA propuesto)\"},\n"
                    "    {\"nro\": 2, \"titulo\": \"...\", \"objetivo\": \"...\"}\n"
                    "  ]\n"
                    "}\n"
                    "Asegúrate de no incluir texto fuera del JSON (sin markdown blocks)."
                )
                
                # Configurar modelo para que se adhiera al prompt planner
                self.ai._configure(self.ai.api_key) 
                # (Forzamos temporalmente la instrucción del sistema del AI)
                original_sys = self.ai.model._system_instruction if hasattr(self.ai.model, '_system_instruction') else None
                
                prompt = f"TEMA DE LA SERIE: {topic}\nNÚMERO DE CAPÍTULOS: {num_chapters}"
                
                # Usar el chat de AI Engine normalmente, pero con un prompt muy fuerte
                response = self.ai.chat(system_prompt + "\n\n" + prompt)
                
                # Intentar extraer JSON de forma manual (buscando { y })
                json_data = None
                start = response.find('{')
                end = response.rfind('}')
                
                if start != -1 and end != -1 and end > start:
                    json_data = json.loads(response[start:end+1])
                else:
                    raise ValueError(f"No se pudo extraer el JSON de la respuesta: {response}")
                    
                self.master_structure = json_data
                self.set_series_name(json_data.get("titulo_serie", topic))
                
                # Guardar master structure
                path = os.path.join(self._series_dir, "master_structure.json") if self._series_dir else ""  # type: ignore
                if path:
                    with open(path, "w", encoding="utf-8") as f:
                        json.dump(json_data, f, indent=4)
                    
                on_success(json_data)
                
            except Exception as e:
                on_error(str(e))

        threading.Thread(target=_worker, daemon=True).start()

    def generate_chapter_json(self, target_ip: str, chapter: dict, mode: str, aspect: str, on_success: Callable, on_error: Callable):
        """Fase 2 (Writer): Genera el JSON ejecutable de un capítulo específico."""
        def _worker():
            try:
                # El objetivo es integrar el prompt original de `AIEngine.generar_proyecto` 
                # pero enfocado a este único capítulo.
                nro = chapter.get("nro", 0)
                titulo = chapter.get("titulo", "")
                objetivo = chapter.get("objetivo", "")
                
                solo_instruction = ""
                if mode == "SOLO TERM":
                    solo_instruction = (
                        "\n\n[MODO SOLO TERM ACTIVADO]\n"
                        "OBLIGATORIO: Estás generando/modificando un guion para MODO SOLO (SOLO TERMINAL DE COMANDOS).\n"
                        "REGLAS ESTRICTAS PARA MODO SOLO:\n"
                        "1. IGNORA EL FLUJO DE 'MENU'. NO uses el tipo de escena 'menu' ni 'leer'.\n"
                        "2. Empieza directamente con una 'narracion' introduciendo el tema y el problema a resolver.\n"
                        "3. Usa escenas de 'ejecucion' para mostrar los comandos reales en la Terminal B.\n"
                        "   IMPORTANTE: Toda escena de tipo 'ejecucion' DEBE OBLIGATORIAMENTE incluir la clave 'comando_visual' con el comando exacto a tipear en la terminal.\n"
                        "4. Intercala 'narracion' explicando EDUCATIVAMENTE qué hace cada comando y cómo interpretar los resultados.\n"
                        "5. Puedes usar 'pausa' de 2 a 3 segundos si es necesario.\n"
                        "6. Cierra con una 'narracion' de despedida resumiendo lo aprendido.\n"
                        "ESTRUCTURA JSON REQUERIDA:\n"
                        "[\n"
                        "  {\"tipo\": \"narracion\", \"voz\": \"Texto a hablar\"},\n"
                        "  {\"tipo\": \"ejecucion\", \"comando_visual\": \"nmap -sV target\", \"voz\": \"Explicación en audio...\"}\n"
                        "]\n"
                        "El JSON debe contener toda la interacción técnica directa con la terminal."
                    )
                
                format_instruction = ""
                if "9:16" in aspect:
                    format_instruction = (
                        "\n\n[FORMATO 9:16 (VERTICAL) DETECTADO]\n"
                        "La ventana de ejecución será muy angosta. \n"
                        "Usa utilidades como `| head -n 15` o flags para reducir la cantidad de líneas de output\n"
                        "de comandos escandalosos para que no inunden la pantalla, ya que se grabará para Shorts/Reels."
                    )
                
                # EXTRACTO DEL CAPITULO ANTERIOR (MEMORIA SERIAL)
                contexto_previo = ""
                if nro > 1 and self._series_dir:
                    prev_file = os.path.join(self._series_dir, f"capitulo_{nro-1}.json")  # type: ignore
                    if os.path.exists(prev_file):
                        try:
                            with open(prev_file, "r", encoding="utf-8") as f:
                                prev_data = json.load(f)
                            
                            comandos_ejecutados = [step.get("comando_visual") for step in prev_data if step.get("tipo") == "ejecucion" and step.get("comando_visual")]
                            narrativas = [step.get("voz") for step in prev_data if step.get("tipo") == "narracion" and step.get("voz")]
                            
                            resumen_comandos = ", ".join(comandos_ejecutados) if comandos_ejecutados else "Ninguno"
                            resumen_narrativa = " ".join(narrativas)[:200] + "..." if narrativas else "Sin narrativa"  # type: ignore
                            
                            contexto_previo = (
                                f"\n\n[MEMORIA DE CONTINUIDAD - CAPÍTULO ANTERIOR ({nro-1})]\n"
                                f"Para que este capítulo se sienta como una secuela directa (PARTE {nro}), "
                                f"aquí tienes el contexto de lo que hiciste en la parte {nro-1}:\n"
                                f"- Comandos usados: {resumen_comandos}\n"
                                f"- Tema narrado: {resumen_narrativa}\n"
                                f"INSTRUCCIÓN: TU PRIMERA LÍNEA NARRATIVA DEBE CONECTAR O MENCIONAR BREVEMENTE LO LOGRADO EN LA PARTE ANTERIOR.\n"
                            )
                        except Exception as e:
                            logger.error(f"Error cargando contexto previo: {e}")
                            
                # INSTRUCCIONES DE PSICOLOGÍA Y SEGURIDAD
                psicologia_seguridad_instruction = (
                    "\n\n[DIRECTIVAS DE RETENCIÓN, PSICOLOGÍA Y SEGURIDAD]\n"
                    "1. Eres un creador viral: Inicia los primeros 3 segundos con un gancho hipnótico ('Hoy vamos a hackear...').\n"
                    "2. CTA Dinámico: Durante la narración, pide que guarden el reel/video, o que te sigan para la siguiente parte, de forma natural.\n"
                    "3. Entornos Controlados y Seguros: Estás en una máquina Host real. USA LABORATORIOS DOCKER LOCALES si el tema lo requiere. "
                    "NUNCA borres archivos del sistema base (`rm -rf /*`), NUNCA uses comandos destructivos en el host. "
                    "Usa `sudo` SOLO si la herramienta de red lo requiere estrictamente (ej: `sudo nmap`)."
                )
                prompt = (
                    f"TARGET LEGAL OBLIGATORIO: {target_ip}\n"
                    f"CONTEXTO: Eres el guionista de la fase {nro} de una serie.\n"
                    f"CAPÍTULO {nro}: {titulo}\n"
                    f"OBJETIVO: {objetivo}\n\n"
                    "Genera el JSON de ejecución para KR-STUDIO siguiendo ESTRICTAMENTE "
                    "las reglas de tu System Prompt base (tipo: narracion, ejecucion, menu, enter, pausa). "
                    "El JSON de salida DEBE ser de alta calidad, profundo en la explicación técnica "
                    f"y enfocado solo y exclusivamente en cumplir este objetivo del capítulo."
                    f"{contexto_previo}{psicologia_seguridad_instruction}{solo_instruction}{format_instruction}"
                )
                
                response = self.ai.chat(prompt)
                json_array = self.ai.extraer_json(response)
                
                if not json_array:
                    raise ValueError("La IA no devolvió un JSONArray válido para el capítulo.")
                
                # VALIDACIÓN DE SEGURIDAD BÁSICA (PREVENTIVA)
                for step in json_array:
                    cmd = step.get("comando_visual", "")
                    if cmd:
                        forbidden_patterns = ["rm -rf /", "chmod 777 -R /", "mkfs", "dd if=/dev/zero of=/dev/sda"]
                        for pattern in forbidden_patterns:
                            if pattern in cmd:
                                logger.warning(f"¡ALERTA DE SEGURIDAD! Comando bloqueado por patrón destructivo: {cmd}")
                                step["comando_visual"] = f"echo 'COMANDO BLOQUEADO: Se detectó un patrón inseguro ({pattern})'"
                                step["voz"] = "Un momento. He detectado un patrón inseguro en el comando generado y lo he bloqueado por seguridad. Las prácticas éticas primero."
                
                # Guardar el JSON del capítulo en disco
                if not self._series_dir:
                    self.set_series_name("Serie_Desconocida")
                    
                filename = f"capitulo_{nro}.json"
                path = os.path.join(self._series_dir, filename) if self._series_dir else ""  # type: ignore
                if path:
                    with open(path, "w", encoding="utf-8") as f:
                        json.dump(json_array, f, indent=4)
                    
                on_success(nro, json_array, path)
                
            except Exception as e:
                on_error(chapter.get("nro", 0), str(e))

        threading.Thread(target=_worker, daemon=True).start()

    def process_series_loop(self, main_app, target_ip: str, mode: str, aspect: str, on_progress: Callable, on_finish: Callable, on_error: Callable):
        """Tarea 4: Renderizar Serie Completa. Ejecuta MasterDirector secuencialmente."""
        if self._is_rendering:
            on_error("Ya hay un renderizado en curso.")
            return
            
        if not self.master_structure or "capitulos" not in self.master_structure:
            on_error("No hay una estructura maestra." )
            return
            
        self._is_rendering = True
        
        def _worker():
            try:
                from kr_studio.core.master_director import MasterDirector, DirectorMode  # type: ignore

                capitulos = self.master_structure.get("capitulos", [])
                
                for idx, cap in enumerate(capitulos):
                    if not self._is_rendering:
                        break  # Cancelado
                        
                    nro = cap.get("nro", idx + 1)
                    path = os.path.join(self._series_dir, f"capitulo_{nro}.json") if self._series_dir else ""  # type: ignore
                    
                    if not os.path.exists(path):
                        on_error(f"Falta el JSON del capítulo {nro}. Genera todos primero.")
                        self._is_rendering = False
                        return
                    
                    with open(path, "r", encoding="utf-8") as f:
                        json_data = json.load(f)
                        
                    on_progress(f"Renderizando Capítulo {nro}: {cap.get('titulo')}")
                    
                    director_mode = DirectorMode.SOLO_TERM if mode == "SOLO TERM" else DirectorMode.DUAL_AI
                    
                    director = MasterDirector(
                        guion         = json_data,
                        mode          = director_mode,
                        workspace_dir = main_app.workspace_dir,
                        typing_speed  = main_app.typing_speed_pct,
                        wid_a         = main_app.wid_a,
                        wid_b         = main_app.wid_b,
                        project_name  = cap.get("titulo", f"cap_{nro}"),
                        aspect_ratio  = aspect,
                        obs_password  = main_app._load_env_value("OBS_PASSWORD", ""),
                        auto_record   = True,
                    )
                    director.floating_ctrl = main_app._floating_ctrl
                    
                    # Limpiar terminal antes de cada capítulo
                    if main_app.wid_b:
                        director.x11.focus_window(main_app.wid_b)
                        director.x11.type_text(main_app.wid_b, "clear", delay_ms=20)
                        director.x11.send_key(main_app.wid_b, "Return")
                        time.sleep(1)
                    
                    main_app._active_director = director
                    # Run bloqueante en este hilo del orquestador
                    director.run()
                    
                    # Pequeña pausa entre capítulos
                    time.sleep(3.0)
                    
                on_finish("Renderizado de serie completado exitosamente.")
                
            except Exception as e:
                on_error(str(e))
            finally:
                self._is_rendering = False
                
        threading.Thread(target=_worker, daemon=True).start()

    def cancel_render(self):
        self._is_rendering = False
