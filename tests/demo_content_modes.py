#!/usr/bin/env python3
"""
Script de demostración que muestra los prompts generados para cada modo de contenido.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kr_studio.core.ai_engine import AIEngine
from kr_studio.core.video_templates import THIRD_PARTY_MODES
import inspect


def main():
    print("=" * 70)
    print("  DEMOSTRACIÓN DE MODOS DE CONTENIDO DE TERCEROS")
    print("=" * 70)

    # Mostrar modos disponibles
    print("\n📋 Modos de contenido de terceros disponibles:\n")
    for mode, info in THIRD_PARTY_MODES.items():
        print(f"  {info['icono']} {mode}")
        print(f"     {info['descripcion']}\n")

    # Extraer instrucciones del código
    source = inspect.getsource(AIEngine.generar_proyecto)

    print("=" * 70)
    print("  PROMPTS ESPECÍFICOS POR MODO")
    print("=" * 70)

    modes_info = [
        (
            "Contenido Mixto (Videos + Terminal)",
            "MODO CONTENIDO MIXTO — VIDEOS EXTERNOS + TERMINAL",
            "Este modo combina videos externos",
        ),
        (
            "Contenido Puro (Terminal)",
            "MODO CONTENIDO PURO — SOLO TERMINAL",
            "Este modo es IDEAL para herramientas con interfaz gráfica",
        ),
    ]

    for mode_name, keyword, description in modes_info:
        print(f"\n┌{'─' * 68}┐")
        print(f"│ MODO: {mode_name}")
        print(f"└{'─' * 68}┘")

        # Encontrar el bloque
        idx = source.find(keyword)
        if idx != -1:
            # Extraer ~20 líneas después del keyword
            lines = source[idx : idx + 3000].split("\n")[:25]
            content = "\n".join(lines)
            print(f"\n{content}...")

        print()

    print("=" * 70)
    print("  INDICADORES PARA CADA MODO")
    print("=" * 70)

    print("""
┌─ CONTENIDO MIXTO ─────────────────────────────────────────────────────┐
│                                                                        │
│  INDICADORES DE VISUAL:                                                │
│  • "ABRIR [URL] EN NAVEGADOR"       - Mostrar página/repo              │
│  • "MOSTRAR ANIMACIÓN DE IA"        - Videos animados explicativas     │
│  • "TRANSICIÓN A TERMINAL"           - Cambio a terminal                │
│  • "TRANSICIÓN A NAVEGADOR"          - Volver a navegador              │
│  • "GRABAR [PROGRAMA] EN ACCIÓN"     - Captura de pantalla              │
│  • "PAUSA PARA VER ANIMACIÓN"        - Esperar contenido visual         │
│                                                                        │
│  FLUJO TÍPICO:                                                        │
│  1. Intro con animación IA                                           │
│  2. Mostrar repo/página en navegador                                  │
│  3. Transición a terminal                                             │
│  4. Clonación y ejecución                                             │
│  5. Animación IA de concepto                                          │
│  6. Más comandos                                                      │
│  7. Cierre                                                            │
└────────────────────────────────────────────────────────────────────────┘

┌─ CONTENIDO PURO ───────────────────────────────────────────────────────┐
│                                                                        │
│  INDICADORES DE VISUAL:                                                │
│  • "CAMBIAR A [NOMBRE_HERRAMIENTA]"   - Cambiar ventana                │
│  • "VOLVER A TERMINAL"                - Transición a terminal          │
│  • "MOSTRAR [HERRAMIENTA] EN ACCIÓN"  - Grabación de pantalla          │
│  • "GRABAR [PROGRAMA]"                - Captura de pantalla            │
│                                                                        │
│  HERRAMIENTAS IDEALES:                                                 │
│  • Wireshark, Burp Suite, Caido, Hydra                               │
│  • Secciones de Kali Linux                                            │
│  • Páginas web interactivas                                          │
│                                                                        │
│  FLUJO TÍPICO:                                                        │
│  1. Hook directo mostrando la herramienta                              │
│  2. Introducción rápida                                               │
│  3. Navegación por la UI                                              │
│  4. Demostración práctica                                             │
│  5. Análisis de resultados                                            │
│  6. Cierre con CTA                                                    │
└────────────────────────────────────────────────────────────────────────┘

┌─ DESACTIVADO ─────────────────────────────────────────────────────────┐
│                                                                        │
│  Sin indicadores especiales. Genera contenido automático estándar     │
│  siguiendo el flujo DUAL AI o SOLO TERM configurado.                 │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
""")

    print("=" * 70)
    print("  ARCHIVOS DE KNOWLEDGE BASE")
    print("=" * 70)

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print(f"\n  📁 Directorio: {os.path.join(base_dir, 'knowledge')}\n")

    for filename in ["contenido_mixto.md", "contenido_puro.md"]:
        filepath = os.path.join(base_dir, "knowledge", filename)
        if os.path.exists(filepath):
            lines = sum(1 for _ in open(filepath, "r", encoding="utf-8"))
            print(f"  ✅ {filename} ({lines} líneas)")
        else:
            print(f"  ❌ {filename} (no encontrado)")

    print("\n" + "=" * 70)
    print("  FIN DE LA DEMOSTRACIÓN")
    print("=" * 70)


if __name__ == "__main__":
    main()
