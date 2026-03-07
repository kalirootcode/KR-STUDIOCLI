import google.generativeai as genai
import json
import re
import os
import logging
from kr_studio.core.memory_manager import MemoryManager
from kr_studio.core.github_tools import GitHubOSINTTools

logger = logging.getLogger(__name__)

SYSTEM_PROMPT_TEMPLATE = """Eres un guionista experto en ciberseguridad, análisis de vulnerabilidades y hacking ético.
Tu trabajo es crear guiones educativos de alto nivel técnico para videos cortos de demostración usando KR-CLI DOMINION.
TU OBJETIVO PRINCIPAL ES ENSEÑAR: Cada guion debe tener una estructura de aprendizaje clara donde se explique *qué* hace la herramienta, *por qué* se utiliza, y *cómo* interpretar los resultados obtenidos, sin inventar información. Eres libre de explicar conceptos avanzados reales de ciberseguridad.

=== SISTEMA DE MEMORIA Y OSINT (MCP) ===
1. TIENES MEMORIA A LARGO PLAZO: Si el usuario te indica que recuerdes algo o tiene una preferencia específica, usa la herramienta `save_fact` para almacenarlo permanentemente.
{memory_context}

2. TIENES CONEXIÓN DIRECTA A GITHUB Y LA WEB:
   - Si no estás 100% seguro de un comando, NO ALUCINES. Usa `search_github_repos` para encontrar la herramienta.
   - Usa `get_github_readme` para leer las instrucciones reales de instalación y uso de repositorios (ej. `rapid7/metasploit-framework`).
   - Usa `google_search` para tendencias generales.

═══════════════════════════════════════════════
CONTEXTO DEL SISTEMA
═══════════════════════════════════════════════

El sistema KR-STUDIO controla DOS terminales + OBS automáticamente:
  Terminal A → kr-clidn (DASHBOARD interactivo, ya abierto al iniciar con venv activo)
  Terminal B → Ejecución de comandos reales (comandos limpios, SIN wrapper)

Kr-clidn YA está cargando automáticamente. Tu guion empieza DESPUÉS del dashboard.

═══════════════════════════════════════════════
FLUJO AUTOMÁTICO
═══════════════════════════════════════════════

Cuando el usuario pide "créame un post sobre [TEMA]", tu guion SIEMPRE debe seguir este flujo:

1. NARRACIÓN de introducción al tema (Plantea el problema a resolver).
2. MENÚ tecla "1" → Entrar a Consola AI.
3. MENÚ tecla "N" → Crear nuevo chat.
4. MENÚ texto "[Título del tema]" → Nombrar el chat.
5. MENÚ texto "[Pregunta profunda sobre el tema]" → Preguntar a DOMINION AI.
6. PAUSA 10-15s → Esperar respuesta de DOMINION.
7. LEER terminal A → Capturar respuesta de DOMINION.
8. NARRACIÓN explicando de forma técnica y educativa lo que DOMINION respondió.
9. EJECUCIÓN en Terminal B → Ejecutar comandos relacionados al tema para aplicarlo de forma práctica.
10. NARRACIÓN de cierre épico resumiendo el aprendizaje obtenido.

═══════════════════════════════════════════════
MENÚ DEL DASHBOARD (ya visible al iniciar)
═══════════════════════════════════════════════
  1 → 🧠 CONSOLA AI         (Chat directo con DOMINION)
  2 → 🌐 WEB H4CK3R
  3 → 🔧 HERRAMIENTAS
  (NO uses la tecla 0 — NUNCA salir del programa)

SUBMENÚ CONSOLA AI (al presionar 1):
  N → Nuevo Chat
  (NO uses 0 — NUNCA volver al dashboard durante el video)

FLUJO DEL CHAT:
  1→ N → escribir título → escribir pregunta → DOMINION responde

═══════════════════════════════════════════════
TIPOS DE ESCENA
═══════════════════════════════════════════════

1. NARRACIÓN (solo audio TTS, NO tipea en terminal, kr-clidn activo):
{"tipo": "narracion", "voz": "Texto para TTS", "comando_visual": "descripción"}

2. EJECUCIÓN (comando LIMPIO en Terminal B, sin kr-cli wrapper):
{"tipo": "ejecucion", "voz": "Explicación educativa del comando para TTS", "comando_real": "nmap -sV scanme.nmap.org"}

3. MENÚ (navegar kr-clidn en Terminal A):
  Tecla: {"tipo": "menu", "voz": "Texto TTS", "tecla": "1", "espera": 3.0}
  Texto: {"tipo": "menu", "voz": "Texto TTS", "texto": "Pregunta a AI", "espera": 10.0}

4. ENTER (presiona Enter):
{"tipo": "enter", "voz": "Texto TTS", "terminal": "A", "espera": 2.0}

5. PAUSA (espera automática):
{"tipo": "pausa", "voz": "Texto TTS", "espera": 5.0}

6. LEER (captura respuesta del terminal para contexto):
{"tipo": "leer", "voz": "Texto TTS", "terminal": "A", "espera": 3.0}

7. ESPERAR (pausa manual hasta que el usuario presione CONTINUAR):
{"tipo": "esperar", "voz": "Texto TTS"}

═══════════════════════════════════════════════
TARGETS LEGALES
═══════════════════════════════════════════════
Usa el target que el usuario especifique con [TARGET LEGAL OBLIGATORIO: xxx].
Si no se especifica, usa uno de estos por defecto según el tema OBLIGATORIAMENTE para mantener la seguridad de la API:
  • scanme.nmap.org — para escaneo de puertos (nmap, ping)
  • testphp.vulnweb.com — para web hacking (nikto, sqlmap, curl, dirb)
  • rest.vulnweb.com — para APIs (curl)
  • httpbin.org — para HTTP requests (curl, wget)
  • badssl.com — para SSL/TLS (curl, openssl)
  • google.com, cloudflare.com — para DNS/OSINT (whois, dig, nslookup)

REGLAS ESTRICTAS:
1. Responde SOLO con el arreglo JSON. Nada más.
2. Los comandos en Terminal B son LIMPIOS (NO uses "kr-cli", solo el comando directo). NUNCA inventes flags de comandos, busca la herramienta si no los conoces.
3. Terminal A es EXCLUSIVA para kr-clidn.
4. SIEMPRE incluye el flujo: menú 1 → N → título → pregunta → pausa → leer.
5. La primera escena es narración de introducción.
6. La última escena es narración de cierre épico enseñando algo nuevo.
7. Usa "espera" suficiente: 3s para menús, 10-15s después de preguntar a la AI.
8. Incluye entre 10-18 escenas por guion.
9. La voz debe ser concisa, dramática pero **EDUCATIVA Y TÉCNICA** (TikTok/Reels).
10. EL TEMA DEL GUION DEBE SER EXACTAMENTE LO QUE EL USUARIO PIDE. NO cambies el tema.
11. NUNCA generes la tecla "0" en un menú. NUNCA cierres kr-clidn. NUNCA uses exit, quit, o salir.
    Kr-clidn DEBE permanecer abierto SIEMPRE durante todo el video.
12. El flujo debe ser CONTINUO y ESTRUCTURADO: Introducción → Pregunta → Explicación teórica → Ejecución práctica → Interpretación de resultados. Cada pregunta profundiza en el tema.
"""


class AIEngine:
    def __init__(self, api_key: str, workspace_dir: str = None):
        self.api_key = api_key
        self.model = None
        self.chat_session = None
        
        # Iniciar módulos MCP-like
        if workspace_dir is None:
            # Fallback a directorio padre si no se provee
            self._base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            workspace_dir = os.path.join(self._base_dir, "workspace")
            
        self.memory_manager = MemoryManager(workspace_dir)
        self.github_tools = GitHubOSINTTools()
        
        if api_key:
            self._configure(api_key)

    def _configure(self, api_key: str):
        """Configura el modelo de Gemini con el System Prompt, memoria y herramientas GitHub/Web."""
        try:
            genai.configure(api_key=api_key)
            
            # Recopilar herramientas
            agent_tools = []
            if hasattr(genai, "tools") and hasattr(genai.tools, "GoogleSearch"):
                agent_tools.append(genai.tools.GoogleSearch())
                
            # Añadir herramientas locales de Memoria y GitHub
            agent_tools.extend(self.memory_manager.get_tool_functions())
            agent_tools.extend(self.github_tools.get_tool_functions())

            # Inyectar la memoria actual en el System Prompt
            memory_ctx = self.memory_manager.retrieve_memory_context()
            dynamic_system_prompt = SYSTEM_PROMPT_TEMPLATE.replace("{memory_context}", memory_ctx)

            self.model = genai.GenerativeModel(
                model_name="gemini-2.0-flash",
                system_instruction=dynamic_system_prompt,
                tools=agent_tools
            )
            
            # Inicializamos la sesión de chat con auto-calling de funciones habilitado
            self.chat_session = self.model.start_chat(history=[])
        except Exception as e:
            logger.error(f"Error al configurar Gemini API: {e}")
            raise ConnectionError(f"Error al configurar Gemini API: {e}")

    def chat(self, user_prompt: str) -> str:
        """Envía un mensaje al chat y devuelve la respuesta cruda."""
        if not self.chat_session:
            raise RuntimeError("API Key no configurada. Usa el botón 'Guardar' primero.")
        try:
            response = self.chat_session.send_message(user_prompt)
            return response.text
        except Exception as e:
            logger.error(f"Error en la API de Gemini: {e}")
            raise RuntimeError(f"Error en la API de Gemini: {e}")

    def extraer_json(self, response_text: str):
        """Intenta extraer un arreglo JSON válido de la respuesta de la IA."""
        text = response_text.strip()
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        text = text.strip()

        try:
            data = json.loads(text)
            if isinstance(data, list):
                return data
        except json.JSONDecodeError:
            pass

        # Intento de rescate: buscar el primer '[' y último ']'
        start = text.find('[')
        end = text.rfind(']')
        if start != -1 and end != -1 and end > start:
            try:
                data = json.loads(text[start:end + 1])
                if isinstance(data, list):
                    return data
            except json.JSONDecodeError:
                pass

        return None

    # ─────────────────────────────────────────────
    # OSINT RADAR — Búsqueda de Tendencias en Vivo
    # ─────────────────────────────────────────────

    def buscar_tendencias_live(self) -> list:
        """Usa Gemini con Google Search para buscar tendencias de ciberseguridad."""
        if not self.api_key:
            raise RuntimeError("API Key no configurada.")

        try:
            # Gemini 2.5 ya tiene conocimiento reciente — no necesita tool externo
            search_model = genai.GenerativeModel(
                model_name="gemini-2.0-flash"
            )

            prompt = """Busca en la web las 5 herramientas, vulnerabilidades o técnicas de hacking/ciberseguridad
más trending en las últimas 48 horas (2 días). Incluye CVEs recientes, herramientas nuevas,
o ataques notables.

Responde SOLO con un arreglo JSON puro así:
[
  {"titulo": "Nombre de la tendencia", "descripcion": "Breve descripción (1 línea)", "fuente": "URL o nombre de la fuente"},
  ...más items...
]
Solo el JSON, nada más."""

            response = search_model.generate_content(prompt)
            text = response.text.strip()
            data = self.extraer_json(text)
            return data if data else []
        except Exception as e:
            raise RuntimeError(f"Error en búsqueda OSINT: {e}")

    # ─────────────────────────────────────────────
    # GENERADOR DE PROYECTO CON TARGET LEGAL
    # ─────────────────────────────────────────────

    def generar_proyecto(self, tendencia: str, objetivo_legal: str) -> str:
        """Genera un guion inyectando el target legal en todos los comandos."""
        if not self.chat_session:
            raise RuntimeError("API Key no configurada.")

        prompt = f"""Crea un guion viral de ciberseguridad sobre: {tendencia}

IMPORTANTE: Para TODOS los comandos reales de ejecución, DEBES usar OBLIGATORIAMENTE 
el objetivo legal: {objetivo_legal}
Esto es para cumplir con las políticas de YouTube/TikTok.

Genera el guion completo siguiendo el flujo automático del sistema."""

        try:
            response = self.chat_session.send_message(prompt)
            return response.text
        except Exception as e:
            raise RuntimeError(f"Error generando proyecto: {e}")

