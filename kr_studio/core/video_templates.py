"""
video_templates.py — Sistema de Plantillas de Video para KR-STUDIO
Define estructuras narrativas de alta retención para diferentes tipos de contenido.
Cada plantilla inyecta instrucciones específicas al system prompt de la IA.
"""

# ═══════════════════════════════════════════════════════════════════
#  CONOCIMIENTO BASE — inyectado siempre al system prompt
#  Técnicas de retención probadas en YouTube/TikTok
# ═══════════════════════════════════════════════════════════════════

RETENTION_KNOWLEDGE = """
═══════════════════════════════════════════════════════════════════
CONOCIMIENTO DE RETENCIÓN Y ENGAGEMENT (OBLIGATORIO APLICAR SIEMPRE)
═══════════════════════════════════════════════════════════════════

PSICOLOGÍA DE RETENCIÓN EN VIDEO:
El cerebro humano retiene contenido cuando experimenta estas 5 emociones en orden:
  1. SORPRESA    → Hook inicial que rompe expectativas (0-15s)
  2. CURIOSIDAD  → Loop abierto que solo se cierra al final (15-45s)
  3. TENSIÓN     → Momento antes del resultado clave (mitad del video)
  4. SATISFACCIÓN → El "AHA" moment cuando todo tiene sentido
  5. ANTICIPACIÓN → CTA que conecta con el próximo contenido

REGLAS DE ORO DE RETENCIÓN:
  • NUNCA empieces con "Hola, bienvenidos a mi canal". Empieza con el resultado.
  • El HOOK debe mostrar el final antes de explicar el inicio.
  • Cada 90 segundos incluir un "retention spike": dato impactante, pregunta retórica o mini-cliffhanger.
  • El espectador debe sentir que perdería algo importante si para el video.
  • Usa el patrón: PROBLEMA → AGITACIÓN → SOLUCIÓN (PAS) como columna vertebral.
  • Los loops abiertos son la herramienta más poderosa: "en 2 minutos verás por qué esto cambió todo..."

FÓRMULAS DE NARRACIÓN DE ALTO IMPACTO:
  • "La mayoría de [grupo] no sabe que [dato sorprendente]. Hoy lo vas a saber tú."
  • "Esto tardó [tiempo corto]. Eso es todo lo que necesité."
  • "Lo que estás a punto de ver afecta a [número] de personas ahora mismo."
  • "Antes de que termines este video, vas a entender por qué [afirmación impactante]."
  • "Este es el [nombre] que los expertos no quieren que conozcas."

ESTRUCTURA NARRATIVA DE 3 ACTOS PARA TECH CONTENT:
  ACTO 1 — GANCHO (0-20% del video):
    - Mostrar el resultado final ANTES de explicarlo
    - Plantear el problema con dato real o estadística
    - Loop abierto: prometer revelación al final
  ACTO 2 — DESARROLLO (20-80% del video):
    - Construir conocimiento en capas (simple → complejo)
    - Demostración práctica en tiempo real
    - Punto de tensión justo antes del resultado clave
    - Dato impactante a mitad del video para retener
  ACTO 3 — CIERRE (80-100% del video):
    - Resolver el loop abierto del inicio
    - Recapitulación que refuerza el aprendizaje
    - CTA que crea anticipación por el siguiente video

LENGUAJE QUE ACTIVA DOPAMINA:
  Usar: "secreto", "jamás lo viste venir", "en tiempo real", "esto acaba de pasar",
  "lo que nadie te enseña", "resultado inmediato", "solo [número] comandos",
  "en [tiempo corto]", "mira esto", "pero hay más", "espera el final"

RITMO NARRATIVO:
  - Frases cortas (máx 15 palabras) para secciones de acción
  - Frases más largas para explicaciones teóricas
  - Pausa dramática de 2-3s antes de revelar resultado clave
  - Cambio de ritmo cada 90s para mantener atención
"""

# ═══════════════════════════════════════════════════════════════════
#  PLANTILLAS DE TIPOS DE VIDEO
# ═══════════════════════════════════════════════════════════════════

VIDEO_TEMPLATES = {

    # ──────────────────────────────────────────────
    "viral_short": {
        "nombre":      "Video Viral (Shorts/Reels)",
        "icono":       "🔥",
        "descripcion": "5-90 segundos. Hook brutal, resultado inmediato, máximo impacto.",
        "duracion_recomendada": "1-2 min",
        "escenas_recomendadas": "5-8",
        "estructura": """
[TIPO DE VIDEO: VIRAL SHORT — MÁXIMA RETENCIÓN EN MÍNIMO TIEMPO]

ESTRUCTURA OBLIGATORIA (5-8 escenas):
  Escena 1 — HOOK VISUAL (0-5s):
    Mostrar el resultado final funcionando SIN explicación previa.
    Voz: frase corta y brutal. Ejemplo: "Esto tardó 3 comandos."
    
  Escena 2 — CONTEXTO RÁPIDO (5-15s):
    Una sola frase que explica POR QUÉ importa.
    Incluir dato real: CVE, empresa afectada, número de sistemas vulnerables.
    
  Escenas 3-6 — EL PROCESO (15-75s):
    Cada escena = un comando o acción con su resultado inmediato.
    Narración: solo lo esencial. Sin relleno. Cada segundo cuenta.
    
  Escena Final — IMPACTO + CTA (75-90s):
    Revelar la implicación completa de lo demostrado.
    Última frase: crear curiosidad por el siguiente video.

REGLAS VIRALES ESTRICTAS:
  - CERO introducciones genéricas
  - CERO agradecimientos al inicio
  - CADA escena avanza la historia
  - Máximo 20 palabras por narración
  - Terminar con pregunta que genere comentarios
""",
    },

    # ──────────────────────────────────────────────
    "tutorial_profundo": {
        "nombre":      "Tutorial Profundo",
        "icono":       "📚",
        "descripcion": "Enseñanza paso a paso. El espectador sale sabiendo hacerlo solo.",
        "duracion_recomendada": "8-15 min",
        "escenas_recomendadas": "15-25",
        "estructura": """
[TIPO DE VIDEO: TUTORIAL PROFUNDO — APRENDIZAJE REAL Y RETENCIÓN ALTA]

FILOSOFÍA: El espectador debe poder reproducir exactamente lo que ve.
           Cada concepto se explica 3 veces: QUÉ es, POR QUÉ existe, CÓMO se usa.

ESTRUCTURA OBLIGATORIA:
  FASE 1 — PROMESA (10% del video):
    Escena 1: Mostrar el estado FINAL que alcanzará el espectador.
    Escena 2: "Antes de empezar" — qué necesita saber el espectador.
    Escena 3: Loop abierto — "al final hay un truco que el 90% no conoce."
    
  FASE 2 — FUNDAMENTOS (20% del video):
    Explicar el concepto teórico con analogía del mundo real.
    Conectar con problema cotidiano que el espectador reconozca.
    
  FASE 3 — DEMOSTRACIÓN GUIADA (50% del video):
    Cada comando: ANTES (qué va a pasar) → DURANTE (ejecutar) → DESPUÉS (interpretar).
    Momento de tensión a mitad: "aquí es donde la mayoría comete el error fatal."
    Dato impactante para retener: estadística real, CVE, caso de empresa conocida.
    
  FASE 4 — CASO REAL (15% del video):
    Aplicar lo aprendido a escenario real del laboratorio Docker.
    Mostrar qué pasa cuando algo sale MAL y cómo solucionarlo.
    
  FASE 5 — CIERRE Y PROFUNDIZACIÓN (5% del video):
    Revelar el "truco prometido" del inicio.
    Recapitulación de 3 puntos clave.
    Teaser del siguiente tutorial de la serie.

REGLAS DE PEDAGOGÍA:
  - Nunca asumir que el espectador sabe algo sin explicarlo primero
  - Cada término técnico: primero en español, luego en inglés entre paréntesis
  - Errores son oportunidades: si algo falla, explicar por qué y arreglarlo en vivo
  - Checkpoints: cada 3 minutos resumir lo aprendido hasta ese punto
""",
    },

    # ──────────────────────────────────────────────
    "curso_capitulo": {
        "nombre":      "Capítulo de Curso",
        "icono":       "🎓",
        "descripcion": "Parte de una serie estructurada. Construye sobre el capítulo anterior.",
        "duracion_recomendada": "10-20 min",
        "escenas_recomendadas": "18-30",
        "estructura": """
[TIPO DE VIDEO: CAPÍTULO DE CURSO — APRENDIZAJE PROGRESIVO EN SERIE]

FILOSOFÍA: Cada capítulo es una unidad completa de conocimiento que también
           necesita del capítulo anterior. El espectador debe sentir progreso.

ESTRUCTURA OBLIGATORIA:
  INTRO — RECAPITULACIÓN (5% del video):
    Escena 1: "En el capítulo anterior aprendiste X. Hoy vas a ir más allá."
    Escena 2: Objetivo concreto del capítulo. Una sola frase.
    Escena 3: Preview de lo que se va a lograr al final.
    
  BLOQUE A — TEORÍA APLICADA (25% del video):
    Concepto nuevo conectado al conocimiento previo.
    Analogía visual que ancle el concepto en la memoria.
    Por qué este concepto es crítico en el mundo real.
    
  BLOQUE B — PRÁCTICA INCREMENTAL (50% del video):
    Ejercicio 1: Versión simple del concepto (nivel básico).
    Ejercicio 2: Versión con complejidad real (nivel intermedio).
    Ejercicio 3: Caso de uso avanzado con laboratorio Docker (nivel pro).
    Cada ejercicio incluye qué observar, qué significa cada output.
    
  BLOQUE C — INTEGRACIÓN (15% del video):
    Combinar lo aprendido hoy con lo del capítulo anterior.
    Demostrar cómo los conceptos se potencian mutuamente.
    
  CIERRE — PRÓXIMO CAPÍTULO (5% del video):
    Los 3 aprendizajes clave de este capítulo.
    Qué habilidades nuevas tiene ahora el espectador.
    Teaser específico del siguiente capítulo: "la próxima vez usarás esto para..."

ELEMENTOS DE FIDELIZACIÓN:
  - Jerga del curso que crea identidad de comunidad
  - Referencia a un concepto de un capítulo anterior para recompensar a suscriptores
  - Reto de práctica al final: "prueba hacer esto y comenta tu resultado"
""",
    },

    # ──────────────────────────────────────────────
    "exposicion_vulnerabilidad": {
        "nombre":      "Exposición de Vulnerabilidad",
        "icono":       "💀",
        "descripcion": "Revelar una vulnerabilidad real con impacto dramático y educativo.",
        "duracion_recomendada": "5-10 min",
        "escenas_recomendadas": "12-18",
        "estructura": """
[TIPO DE VIDEO: EXPOSICIÓN DE VULNERABILIDAD — DRAMA + EDUCACIÓN]

FILOSOFÍA: Cada vulnerabilidad tiene una historia. El espectador debe sentir
           el riesgo real antes de ver la solución.

ESTRUCTURA OBLIGATORIA:
  ACTO 1 — EL IMPACTO (Hook dramático, 15% del video):
    Escena 1: Mostrar el exploit funcionando SIN contexto previo.
              "Esto acaba de comprometer completamente el sistema."
    Escena 2: Número de sistemas afectados en el mundo. CVE real si existe.
              Empresa o caso real que fue víctima de esta vulnerabilidad.
    Escena 3: Loop abierto — "en 5 minutos verás exactamente cómo funciona."
    
  ACTO 2 — LA ANATOMÍA (Cómo funciona, 40% del video):
    Escena: Explicar por qué existe la vulnerabilidad (error de diseño/código).
    Escena: Condiciones necesarias para que sea explotable.
    Escena: Reconocimiento — cómo detectar si el sistema es vulnerable (nmap, etc).
    PUNTO DE TENSIÓN: "Ahora vamos a explotarla en vivo."
    
  ACTO 3 — LA EXPLOTACIÓN (Demo en laboratorio, 30% del video):
    Escena por escena del proceso de explotación.
    Narrar lo que está pasando internamente, no solo los comandos.
    Mostrar el momento exacto en que el sistema cede.
    Post-explotación: qué puede hacer el atacante ahora.
    
  ACTO 4 — LA DEFENSA (Siempre incluir, 15% del video):
    Patch o mitigación específica.
    Cómo detectar si ya fuiste comprometido.
    Una sola línea de comando para comprobar si estás protegido.

REGLAS DE IMPACTO:
  - La vulnerabilidad debe tener nombre y apellido (CVE, nombre, descubridor)
  - Siempre mostrar primero el ataque, luego la defensa
  - Disclaimer legal visible pero breve: "laboratorio controlado"
  - Terminar con "¿qué otras vulnerabilidades quieres que examinemos?"
""",
    },

    # ──────────────────────────────────────────────
    "marketing_herramienta": {
        "nombre":      "Marketing de Herramienta/Producto",
        "icono":       "🚀",
        "descripcion": "Presentar una herramienta mostrando su valor real en acción.",
        "duracion_recomendada": "3-8 min",
        "escenas_recomendadas": "10-16",
        "estructura": """
[TIPO DE VIDEO: MARKETING DE HERRAMIENTA — MOSTRAR VALOR REAL]

FILOSOFÍA: No vender características. Vender transformación.
           "Antes de esta herramienta hacías X. Ahora haces X en 10 segundos."

ESTRUCTURA OBLIGATORIA (fórmula BEFORE-AFTER-BRIDGE):
  BEFORE — El problema sin la herramienta (20% del video):
    Escena 1: Mostrar el proceso LENTO/DIFÍCIL que la herramienta reemplaza.
              Hacerlo visible y doloroso. "¿Cuánto tiempo perdías haciendo esto?"
    Escena 2: El costo real: tiempo, errores, complejidad.
    
  BRIDGE — La herramienta como solución (15% del video):
    Escena 3: Presentación de la herramienta. Una frase. Su propósito exacto.
    Escena 4: Por qué esta y no las alternativas (diferenciador clave).
    
  AFTER — La transformación en acción (50% del video):
    Demostración en vivo en el laboratorio.
    Caso 1: Uso básico — resultado en segundos.
    Caso 2: Uso avanzado — resultado que antes era imposible.
    Caso 3: Integración con otras herramientas del stack.
    Métrica concreta: "esto que tardaba 20 minutos ahora tarda 8 segundos."
    
  CALL TO ACTION (15% del video):
    Dónde conseguirla (repositorio, comando de instalación).
    El único comando necesario para empezar.
    "En el próximo video vamos a usar esta herramienta para [caso avanzado]."

REGLAS DE MARKETING TÉCNICO:
  - NUNCA mentir sobre capacidades. La credibilidad técnica es el activo más valioso.
  - Mostrar TAMBIÉN las limitaciones — esto aumenta la confianza
  - Comparar con alternativas honestamente
  - El espectador debe poder instalarla y usarla DURANTE el video
  - Métrica de impacto obligatoria: velocidad, precisión, o cobertura
""",
    },

    # ──────────────────────────────────────────────
    "osint_investigacion": {
        "nombre":      "OSINT / Investigación en Vivo",
        "icono":       "🔍",
        "descripcion": "Investigación de inteligencia abierta en tiempo real. Narrativa detectivesca.",
        "duracion_recomendada": "8-15 min",
        "escenas_recomendadas": "15-22",
        "estructura": """
[TIPO DE VIDEO: OSINT / INVESTIGACIÓN EN VIVO — NARRATIVA DETECTIVESCA]

FILOSOFÍA: El espectador es el co-investigador. Cada hallazgo es una revelación compartida.

ESTRUCTURA OBLIGATORIA:
  APERTURA — EL CASO (10% del video):
    Escena 1: "Hoy vamos a investigar [objetivo]. Solo con información pública."
    Escena 2: Las reglas: qué es legal, qué buscamos, qué no haremos.
    Escena 3: Estado inicial — qué sabemos antes de empezar (casi nada).
    
  FASE 1 — RECONOCIMIENTO PASIVO (25% del video):
    whois, DNS, certificados SSL, subdominios.
    Cada hallazgo narrado como pista que lleva a la siguiente.
    "Este resultado nos dice que... lo que significa que..."
    
  FASE 2 — ANÁLISIS DE SUPERFICIE (35% del video):
    Shodan, headers HTTP, tecnologías expuestas.
    Momento de tensión: "encontramos algo que no deberían tener expuesto."
    Dato impactante a mitad de la investigación.
    
  FASE 3 — SÍNTESIS (20% del video):
    Construir el perfil completo del objetivo con todo lo hallado.
    Mostrar visualmente qué información estaba pública sin que nadie lo supiera.
    
  CIERRE — LECCIONES (10% del video):
    Qué debería hacer el objetivo para protegerse.
    Qué aprendiste tú como defensor al ver esto.
    "¿Qué objetivo investigamos la próxima semana? Comenta."

TÉCNICAS NARRATIVAS DETECTIVESCAS:
  - Cada herramienta es "la próxima pista"
  - Los hallazgos se conectan como una cadena lógica
  - El espectador debe sentir que está descubriendo junto con el presentador
  - Usa "interesante...", "mira esto", "no esperaba encontrar esto aquí"
""",
    },

    # ──────────────────────────────────────────────
    "comparativa_batalla": {
        "nombre":      "Comparativa / Batalla de Herramientas",
        "icono":       "⚔️",
        "descripcion": "Dos herramientas, mismo objetivo. ¿Cuál gana? Alta retención por el suspenso.",
        "duracion_recomendada": "6-12 min",
        "escenas_recomendadas": "14-20",
        "estructura": """
[TIPO DE VIDEO: COMPARATIVA / BATALLA — SUSPENSO Y CONCLUSIÓN DEFINITIVA]

FILOSOFÍA: El debate es el motor de engagement. El espectador toma partido.
           La conclusión debe ser clara, argumentada y sorprendente.

ESTRUCTURA OBLIGATORIA:
  PRESENTACIÓN DEL RING (10% del video):
    Escena 1: "Hoy solo uno puede ganar." Presentar las dos herramientas.
    Escena 2: Las 3 métricas de comparación (velocidad, precisión, facilidad).
    Escena 3: "Vota en los comentarios cuál crees que va a ganar."
    
  ROUND 1 — VELOCIDAD (25% del video):
    Mismo objetivo. Herramienta A. Medir tiempo exacto.
    Herramienta B. Misma tarea. Mismo objetivo.
    Veredicto Round 1: ganador con argumento técnico.
    
  ROUND 2 — PROFUNDIDAD DE RESULTADO (30% del video):
    Calidad del output de cada herramienta.
    Qué detecta una que la otra no.
    Momento de sorpresa: "esto es inesperado."
    
  ROUND 3 — CASO EXTREMO (20% del video):
    Escenario difícil donde una de las dos falla.
    La que sobrevive gana puntos extra.
    
  VEREDICTO FINAL (15% del video):
    Tabla de puntuación clara.
    "La ganadora es X, pero usa Y cuando..."
    Caso de uso específico para cada una.
    "¿Estás de acuerdo? Comenta qué herramienta usas tú."

REGLAS DE ENTRETENIMIENTO TÉCNICO:
  - El suspenso del ganador debe mantenerse hasta el final
  - Nunca favorecer una desde el inicio (fake neutrality hasta el veredicto)
  - Los comentarios de "yo prefiero X" son el objetivo de engagement
  - Incluir una herramienta "dark horse" poco conocida para sorprender
""",
    },
}

# ═══════════════════════════════════════════════════════════════════
#  CONFIGURACIÓN DE PERSONALIDAD DEL PRESENTADOR
# ═══════════════════════════════════════════════════════════════════

PRESENTER_STYLES = {
    "experto_tecnico": {
        "nombre": "Experto Técnico",
        "descripcion": "Preciso, riguroso, datos siempre verificados.",
        "instruccion": "Habla como un ingeniero de seguridad senior con 10 años de experiencia. Usa terminología técnica precisa pero siempre explícala. Prioriza la exactitud sobre la simplificación.",
    },
    "mentor_accesible": {
        "nombre": "Mentor Accesible",
        "descripcion": "Cercano, paciente, hace lo complejo simple.",
        "instruccion": "Habla como un amigo que sabe mucho y quiere que tú también aprendas. Usa analogías del mundo cotidiano. Si hay dos formas de decir algo, elige la más simple.",
    },
    "investigador_periodista": {
        "nombre": "Investigador / Periodista",
        "descripcion": "Narrativa detectivesca, revela verdades, tono de urgencia.",
        "instruccion": "Habla como un periodista de investigación especializado en tecnología. Cada hallazgo es una revelación. Usa frases como 'lo que encontramos a continuación es perturbador' y 'esto afecta a millones de personas ahora mismo'.",
    },
    "hacker_etico": {
        "nombre": "Hacker Ético",
        "descripcion": "Directo, práctico, deja claro que el conocimiento es poder.",
        "instruccion": "Habla como un pentester profesional certificado. Directo al punto. Sin relleno. Cada segundo del video tiene propósito. Usa frases cortas y contundentes.",
    },
}

# ═══════════════════════════════════════════════════════════════════
#  CONFIGURACIÓN DE AUDIENCIA OBJETIVO
# ═══════════════════════════════════════════════════════════════════

AUDIENCE_CONFIGS = {
    "principiante": {
        "nombre": "Principiante (0-1 año)",
        "instruccion": "La audiencia nunca ha tocado una terminal de Linux. Explicar ABSOLUTAMENTE TODO. Cada comando desde cero. Analogías simples obligatorias. Evitar jerga sin explicación.",
    },
    "intermedio": {
        "nombre": "Intermedio (1-3 años)",
        "instruccion": "La audiencia conoce Linux básico, sabe qué es nmap y Metasploit pero nunca los ha usado en pentesting real. Puede usarse terminología básica sin explicarla pero siempre contextualizar el 'por qué'.",
    },
    "avanzado": {
        "nombre": "Avanzado (3+ años)",
        "instruccion": "La audiencia son profesionales de seguridad o estudiantes avanzados. Ir directo a los conceptos sin explicar lo básico. Profundizar en detalles técnicos internos. Mencionar alternativas y edge cases.",
    },
    "mixto": {
        "nombre": "Audiencia Mixta",
        "instruccion": "La audiencia tiene niveles variados. Explica los conceptos fundamentales brevemente para los nuevos, pero añade capas de profundidad para los avanzados. Usa la fórmula: explicación simple → detalle técnico avanzado → aplicación práctica.",
    },
}

# ═══════════════════════════════════════════════════════════════════
#  FUNCIÓN: Construir el bloque de instrucciones para el prompt
# ═══════════════════════════════════════════════════════════════════

def build_video_config_block(
    video_type:     str = "tutorial_profundo",
    presenter_style: str = "experto_tecnico",
    audience:       str = "intermedio",
    extra_notes:    str = "",
) -> str:
    """
    Construye el bloque completo de configuración de video para inyectar al prompt.
    """
    template   = VIDEO_TEMPLATES.get(video_type, VIDEO_TEMPLATES["tutorial_profundo"])
    presenter  = PRESENTER_STYLES.get(presenter_style, PRESENTER_STYLES["experto_tecnico"])
    aud_config = AUDIENCE_CONFIGS.get(audience, AUDIENCE_CONFIGS["intermedio"])

    block = f"""
{RETENTION_KNOWLEDGE}

═══════════════════════════════════════════════
CONFIGURACIÓN ACTIVA DE ESTE VIDEO
═══════════════════════════════════════════════

TIPO DE VIDEO: {template['icono']} {template['nombre']}
DURACIÓN RECOMENDADA: {template['duracion_recomendada']}
ESCENAS RECOMENDADAS: {template['escenas_recomendadas']}

ESTILO DEL PRESENTADOR: {presenter['nombre']}
{presenter['instruccion']}

NIVEL DE AUDIENCIA: {aud_config['nombre']}
{aud_config['instruccion']}

{template['estructura']}
"""

    if extra_notes.strip():
        block += f"""
NOTAS ADICIONALES DEL CREADOR:
{extra_notes}
"""

    block += """
APLICACIÓN OBLIGATORIA:
Toda la estructura anterior DEBE reflejarse en el JSON generado.
Las narraciónes del campo "voz" deben implementar las técnicas de retención descritas.
El ritmo, la tensión y los loops abiertos son TAN IMPORTANTES como el contenido técnico.
Un guion sin retención es un guion fallido, independientemente de su precisión técnica.
"""

    return block


def get_template_list() -> list:
    """Retorna lista de plantillas para mostrar en la UI."""
    return [
        {
            "key":         k,
            "nombre":      v["nombre"],
            "icono":       v["icono"],
            "descripcion": v["descripcion"],
            "duracion":    v["duracion_recomendada"],
        }
        for k, v in VIDEO_TEMPLATES.items()
    ]


def get_presenter_list() -> list:
    return [{"key": k, "nombre": v["nombre"], "descripcion": v["descripcion"]}
            for k, v in PRESENTER_STYLES.items()]


def get_audience_list() -> list:
    return [{"key": k, "nombre": v["nombre"]}
            for k, v in AUDIENCE_CONFIGS.items()]


def get_content_types():
    return list(VIDEO_TEMPLATES.keys())


def get_content_prompt(content_type: str, tema: str, labs_context: str = "", memory_context: str = "") -> str:
    if content_type not in VIDEO_TEMPLATES:
        raise ValueError(f"Tipo de contenido '{content_type}' no encontrado")
    template = VIDEO_TEMPLATES[content_type]
    return f"""
TIPO DE VIDEO: {template['icono']} {template['nombre']}
DESCRIPCIÓN: {template['descripcion']}
DURACIÓN RECOMENDADA: {template['duracion_recomendada']}

{template['estructura']}

LABORATORIOS: {labs_context}
{memory_context}
"""
