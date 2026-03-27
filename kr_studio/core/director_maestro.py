"""Director Maestro - Sistema de generación de contenido basado en memoria.

Este módulo es el cerebro central que usa la memoria vectorial
para generar cualquier tipo de contenido de forma inteligente.
"""

import json
import logging
from typing import Dict, List, Optional, Any
from kr_studio.core.vector_memory import VectorMemory
from kr_studio.core.personality import get_personality

logger = logging.getLogger(__name__)


class DirectorMaestro:
    """Director que usa la memoria para generar contenido diverso."""

    def __init__(self, vector_memories: Dict[str, VectorMemory]):
        self.vector_memories = vector_memories
        self.personality = get_personality()

    def build_post_social_prompt(self, tema: str, plataforma: str = "twitter") -> str:
        """Construye el prompt para generar un post optimizado para redes sociales."""
        contexto = self._obtener_contexto(tema, n_results=3)

        estructura = self.personality.config.get("tipos_contenido", {}).get(
            "post_social", {}
        )

        prompt = f"""Eres {self.personality.config.get("nombre_ia")} - Experto en contenido viral para {plataforma}.

CONOCIMIENTO RELEVANTE:
{contexto}

INSTRUCCIONES:
- Gáncho en las primeras palabras (debe atrapar)
- Estructura: GANCHO → VALOR → CTA
- Longitud: {estructura.get("longitud", "150-300 caracteres")}
- Usa emojis estratégicamente (máximo 2-3)
- Incluye hashtags relevantes (2-3 máximo)
- Tono: {self.personality.config.get("tono")}
- NO uses clickbait falso

Genera UN post optimizado para {plataforma} sobre: {tema}

Ejemplo de estructura:
🔥 [GANCHO QUE ATRAPA]
💡 [VALOR/CONOCIMIENTO]
👉 [CTA]

Responde SOLO con el post, sin explicaciones adicionales."""

        return prompt

    def build_articulo_prompt(self, tema: str) -> str:
        """Construye el prompt para generar un artículo completo optimizado para blog."""
        contexto = self._obtener_contexto(tema, n_results=5)

        estructura = self.personality.config.get("tipos_contenido", {}).get(
            "articulo", {}
        )

        prompt = f"""Eres {self.personality.config.get("nombre_ia")} - Creador de contenido educativo de alto impacto.

CONOCIMIENTO RELEVANTE:
{contexto}

TU IDENTIDAD:
{self._formatear_identidad()}

INSTRUCCIONES PARA ARTÍCULO:
- Estructura: Título → Intro → Desarrollo (H2/H3) → Conclusión → CTA
- Longitud: {estructura.get("longitud", "1000-1500 palabras")}
- Subtítulos optimizados para SEO
- Incluye ejemplos prácticos de tu nicho
- Bullet points donde sea relevante
- Tono: {self.personality.config.get("tono")}
- Finaliza con CTA claro

FORMATO DE SALIDA:
Devuelve el artículo en formato JSON:
{{
  "titulo": "título optimizado para SEO",
  "intro": "introducción que atrapa",
  "secciones": [
    {{"titulo": "H2", "contenido": "...", "subsecciones": [...]}}
  ],
  "conclusion": "conclusión + CTA",
  "meta": {{"descripcion_seo": "...", "palabras_clave": ["..."]}}
}}

Tema del artículo: {tema}"""

        return prompt

    def build_modulo_curso_prompt(self, tema: str, modulo_num: int = 1) -> str:
        """Construye el prompt para generar un módulo completo para curso (Hotmart/Udemy)."""
        contexto = self._obtener_contexto(tema, n_results=5)

        estructura = self.personality.config.get("tipos_contenido", {}).get(
            "curso_hotmart", {}
        )

        prompt = f"""Eres {self.personality.config.get("nombre_ia")} - Instructor y estratega de cursos online.

CONOCIMIENTO EXPERTO:
{contexto}

IDENTIDAD DE INSTRUCTOR:
{self._formatear_identidad()}

INSTRUCCIONES PARA MÓDULO DE CURSO:
- Estructura: Módulo → Lecciones → Contenido → Ejercicio → Quiz
- Cada módulo: 5-10 lecciones
- Incluir: objetivos, recursos, duración estimada
- Dificultad progresiva
- Ejercicios prácticos reales
- Quiz de validación

FORMATO DE SALIDA JSON:
{{
  "modulo": {{
    "numero": {modulo_num},
    "titulo": "título del módulo",
    "descripcion": "descripción del módulo",
    "objetivos": ["obj1", "obj2"],
    "duracion_estimada": "X horas",
    "lecciones": [
      {{
        "numero": 1,
        "titulo": "título",
        "tipo": "video|texto|ejercicio|quiz",
        "contenido": "...",
        "duracion": "X minutos",
        "recursos": ["recurso1", "recurso2"]
      }}
    ]
  }}
}}

Genera el MÓDULO {modulo_num} para un curso sobre: {tema}"""

        return prompt

    def build_serie_prompt(self, tema: str, num_episodios: int = 5) -> str:
        """Construye el prompt para generar estructura de serie de contenido."""
        contexto = self._obtener_contexto(tema, n_results=5)

        prompt = f"""Eres {self.personality.config.get("nombre_ia")} - Estratega de contenido serial.

CONOCIMIENTO:
{contexto}

INSTRUCCIONES PARA SERIE:
- Crear arco narrativo completo
- Cada episodio debe tener gancho propio
- Progresión de dificultad/valor
- Tensión y cliffhangers entre episodios
- Final satisfactorio

FORMATO JSON:
{{
  "serie": {{
    "titulo": "título de la serie",
    "tema": "{tema}",
    "total_episodios": {num_episodios},
    "episodios": [
      {{
        "numero": 1,
        "titulo": "título del episodio",
        "duracion": "X-Y min",
        "gancho_inicial": "...",
        "contenido_resumen": "...",
        "cliffhanger": "..."
      }}
    ]
  }}
}}

Genera una serie de {num_episodios} episodios sobre: {tema}"""

        return prompt

    def build_guion_video_prompt(self, tema: str, duracion_min: int = 10) -> str:
        """Construye el prompt para generar guion completo para video."""
        contexto = self._obtener_contexto(tema, n_results=5)

        estructura = self.personality.config.get("tipos_contenido", {}).get(
            "guion_video", {}
        )

        prompt = f"""Eres {self.personality.config.get("nombre_ia")} - Guionista de videos educativos virales.

CONOCIMIENTO:
{contexto}

ESTILO DE NARRACIÓN:
{self._formatear_estilo_narracion()}

INSTRUCCIONES PARA GUION:
- Estructura: Intro ({duracion_min * 0.1:.0f}min) → Desarrollo ({duracion_min * 0.7:.0f}min) → Demo práctica ({duracion_min * 0.15:.0f}min) → Outro/CTA ({duracion_min * 0.05:.0f}min)
- INTRO: Gáncho de 3-5 segundos, presentación del tema
- DESARROLLO: Explicación clara con ejemplos
- DEMO: Demostración práctica del concepto
- OUTRO: Resumen + CTA (suscribirse, comentar, siguiente video)
- Incluir timestamps sugeridos
- Notas para B-roll y gráficos
- Campo "voz" debe sonar natural, sin emojis

FORMATO JSON:
[
  {{
    "escena": 1,
    "tipo": "intro|explicacion|demo|outro",
    "duracion_seg": X,
    "voz": "texto de narración (limpio, sin emojis)",
    "visual": "descripción de lo que se ve en pantalla",
    "comando_ejecutar": "comando a mostrar si aplica",
    "timestamp": "0:00"
  }}
]

Guion para video de {duracion_min} minutos sobre: {tema}"""

        return prompt

    def build_estrategia_marketing_prompt(self, objetivo: str) -> str:
        """Construye el prompt para generar estrategia de marketing basada en conocimiento guardado."""
        marketing_knowledge = self._buscar_en_memoria(
            "marketing", objetivo, n_results=5
        )
        estrategias = self.personality.config.get("marketing", {})

        prompt = f"""Eres {self.personality.config.get("nombre_ia")} - Estratega de Marketing Digital.

CONOCIMIENTO DE MARKETING GUARDADO:
{marketing_knowledge}

ESTRATEGIAS DISPONIBLES:
- Virales: {estrategias.get("estrategias_virales", [])}
- Psicología: {estrategias.get("psicologia", [])}
- Funnel: {estrategias.get("funnel", [])}

INSTRUCCIONES:
- Analiza el objetivo y propón estrategia completa
- Incluye calendario de contenido
- Métricas a seguir
- Presupuesto estimado (si aplica)

FORMATO JSON:
{{
  "objetivo": "{objetivo}",
  "analisis": "análisis del objetivo",
  "estrategia": {{
    "fase_awareness": ["acción1", "acción2"],
    "fase_consideracion": ["acción1", "acción2"],
    "fase_conversion": ["acción1", "acción2"]
  }},
  "calendario": [
    {{"semana": 1, "acciones": ["..."]}}
  ],
  "metricas": ["métrica1", "métrica2"],
  "cta_sugeridos": ["cta1", "cta2"]
}}

Genera estrategia de marketing para: {objetivo}"""

        return prompt

    def guardar_contenido_generado(self, tipo: str, titulo: str, contenido: Any):
        """Guarda automáticamente el contenido generado en memoria."""
        try:
            doc_id = (
                f"{tipo}_{titulo[:30].replace(' ', '_')}_{hash(str(contenido))[:8]}"
            )
            contenido_str = (
                json.dumps(contenido, indent=2, ensure_ascii=False)
                if isinstance(contenido, dict)
                else str(contenido)
            )

            self.vector_memories["generado"].add_document(
                text=f"TIPO: {tipo}\n\nTITULO: {titulo}\n\nCONTENIDO:\n{contenido_str}",
                doc_id=doc_id,
            )
            logger.info(f"Contenido guardado en 'generado': {doc_id}")
        except Exception as e:
            logger.error(f"Error guardando contenido generado: {e}")

    def _obtener_contexto(self, tema: str, n_results: int = 3) -> str:
        """Obtiene contexto relevante de todas las memorias."""
        contextos = []
        for nombre, memoria in self.vector_memories.items():
            resultados = memoria.search(tema, n_results=n_results)
            if resultados:
                for res in resultados:
                    contextos.append(f"[{nombre}] {res.get('content', '')[:500]}")

        if not contextos:
            return (
                "No hay conocimiento previo sobre este tema. Usa tu expertise general."
            )

        return "\n\n".join(contextos)

    def _buscar_en_memoria(
        self, compartimento: str, query: str, n_results: int = 3
    ) -> str:
        """Busca en un compartimento específico."""
        if compartimento not in self.vector_memories:
            return f"Compartimento '{compartimento}' no disponible."

        memoria = self.vector_memories[compartimento]
        resultados = memoria.search(query, n_results=n_results)

        if not resultados:
            return f"No se encontró información en '{compartimento}' sobre: {query}"

        return "\n".join([res.get("content", "")[:500] for res in resultados])

    def _formatear_identidad(self) -> str:
        """Formatea la identidad para prompts."""
        identidad = self.personality.config.get("identidad", {})
        expertise = ", ".join(identidad.get("experto_en", []))
        contenidos = ", ".join(identidad.get("tipo_contenido", []))
        audiencia = ", ".join(identidad.get("audiencia_objetivo", []))

        return f"""EXPERTO EN: {expertise}
TIPO DE CONTENIDO: {contenidos}
AUDIENCIA: {audiencia}"""

    def _formatear_estilo_narracion(self) -> str:
        """Formatea el estilo de narración para prompts."""
        estilo = self.personality.config.get("estilo_narracion", {})
        ganchos = ", ".join(estilo.get("ganchos", []))

        return f"""VELOCIDAD: {estilo.get("velocidad", "media")}
ENTONACIÓN: {estilo.get("entonacion", "entusiasta")}
GANCHOS CARACTERÍSTICOS: {ganchos}"""

    def listar_compartimentos(self) -> List[str]:
        """Lista los compartimentos disponibles."""
        return list(self.vector_memories.keys())

    def obtener_estadisticas(self) -> Dict[str, int]:
        """Obtiene estadísticas de documentos por compartimento."""
        stats = {}
        for nombre, memoria in self.vector_memories.items():
            try:
                docs = memoria.get_documents_for_compartment(nombre)
                stats[nombre] = len(docs)
            except Exception:
                stats[nombre] = 0
        return stats
