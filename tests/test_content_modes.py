#!/usr/bin/env python3
"""
Test script para verificar la generación de prompts según el modo de contenido.

Este script verifica que los prompts de contenido mixto y puro se generan
correctamente con las instrucciones específicas para cada modo.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kr_studio.core.ai_engine import AIEngine
from kr_studio.core.video_templates import THIRD_PARTY_MODES, get_third_party_modes


def test_third_party_modes_config():
    """Verifica que los modos de contenido de terceros están correctamente configurados."""
    print("=" * 60)
    print("TEST: Configuración de modos de contenido de terceros")
    print("=" * 60)

    modes = get_third_party_modes()
    expected_modes = [
        "Desactivado",
        "Contenido Mixto (Videos + Terminal)",
        "Contenido Puro (Terminal)",
    ]

    print(f"\nModos disponibles: {modes}")
    print(f"Modos esperados: {expected_modes}")

    assert modes == expected_modes, f"Modos incorrectos. Obtenido: {modes}"

    for mode in modes:
        info = THIRD_PARTY_MODES.get(mode)
        assert info is not None, f"No se encontró info para modo: {mode}"
        assert "nombre" in info, f"Modo {mode} falta 'nombre'"
        assert "icono" in info, f"Modo {mode} falta 'icono'"
        assert "descripcion" in info, f"Modo {mode} falta 'descripcion'"
        print(f"  ✅ {mode}: {info['icono']} {info['descripcion']}")

    print("\n✅ Todos los modos están correctamente configurados\n")
    return True


def test_ai_engine_has_content_modes():
    """Verifica que AIEngine tiene soporte para modos de contenido string."""
    print("=" * 60)
    print("TEST: AI Engine soporta modos de contenido como string")
    print("=" * 60)

    import inspect

    source = inspect.getsource(AIEngine.generar_proyecto)

    # Verificar que el parámetro third_party_content es de tipo str
    assert "third_party_content: str" in source, (
        "third_party_content no es str en AIEngine.generar_proyecto"
    )
    print("  ✅ third_party_content es tipo str")

    # Verificar que contiene las instrucciones para cada modo
    assert "Contenido Mixto (Videos + Terminal)" in source, "Falta modo mixto"
    print("  ✅ Incluye instrucciones para 'Contenido Mixto'")

    assert "Contenido Puro (Terminal)" in source, "Falta modo puro"
    print("  ✅ Incluye instrucciones para 'Contenido Puro'")

    print("\n✅ AI Engine soporta los modos de contenido correctamente\n")
    return True


def test_prompt_generation():
    """Verifica que los prompts se generan correctamente para cada modo."""
    print("=" * 60)
    print("TEST: Generación de prompts por modo de contenido")
    print("=" * 60)

    # Leer el código fuente de generar_proyecto para verificar las instrucciones
    import inspect

    source = inspect.getsource(AIEngine.generar_proyecto)

    # Test modo mixto
    print("\n--- Modo: Contenido Mixto (Videos + Terminal) ---")
    assert "[MODO CONTENIDO MIXTO" in source, "Faltan instrucciones para modo mixto"
    assert "ABRIR [URL] EN NAVEGADOR" in source, (
        "Falta indicador ABRIR URL para modo mixto"
    )
    assert "TRANSICIÓN A TERMINAL" in source, (
        "Falta indicador TRANSICIÓN para modo mixto"
    )
    assert "MOSTRAR ANIMACIÓN DE IA" in source, (
        "Falta indicador ANIMACIÓN para modo mixto"
    )
    print("  ✅ Incluye indicadores: ABRIR URL, TRANSICIÓN, ANIMACIÓN")

    # Test modo puro
    print("\n--- Modo: Contenido Puro (Terminal) ---")
    assert "[MODO CONTENIDO PURO" in source, "Faltan instrucciones para modo puro"
    assert "Wireshark" in source and "Burp Suite" in source, (
        "Falta lista de herramientas"
    )
    assert "CAMBIAR A [NOMBRE_HERRAMIENTA]" in source, "Falta indicador CAMBIAR A"
    assert "VOLVER A TERMINAL" in source, "Falta indicador VOLVER A TERMINAL"
    print(
        "  ✅ Incluye indicadores: Wireshark, Burp Suite, CAMBIAR A, VOLVER A TERMINAL"
    )

    # Test modo desactivado
    print("\n--- Modo: Desactivado ---")
    assert "[REGLAS PARA GENERACIÓN DE GUION]" in source, (
        "Faltan instrucciones para modo desactivado"
    )
    print("  ✅ Incluye instrucciones básicas para modo desactivado")

    print("\n✅ Prompts generados correctamente para todos los modos\n")
    return True


def test_knowledge_files_exist():
    """Verifica que los archivos de knowledge base existen."""
    print("=" * 60)
    print("TEST: Archivos de knowledge base")
    print("=" * 60)

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    knowledge_dir = os.path.join(base_dir, "knowledge")

    files = {
        "contenido_mixto.md": "Contenido Mixto (Videos + Terminal)",
        "contenido_puro.md": "Contenido Puro (Terminal)",
        "contenido_tercero.md": "Template original",
    }

    for filename, description in files.items():
        filepath = os.path.join(knowledge_dir, filename)
        exists = os.path.exists(filepath)
        status = "✅" if exists else "❌"
        print(f"  {status} {filename}: {description}")
        if not exists:
            print(f"      ⚠️  Archivo no encontrado: {filepath}")

    # Verificar contenido mixto
    mixto_path = os.path.join(knowledge_dir, "contenido_mixto.md")
    if os.path.exists(mixto_path):
        with open(mixto_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "INTRO hook" in content, "Falta INTRO hook en contenido_mixto.md"
        assert "REPOSITORIO" in content, "Falta ejemplo de repositorio"
        assert "TRANSICIÓN A TERMINAL" in content, "Falta transición"
        print("  ✅ contenido_mixto.md tiene estructura correcta")

    # Verificar contenido puro
    puro_path = os.path.join(knowledge_dir, "contenido_puro.md")
    if os.path.exists(puro_path):
        with open(puro_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "Wireshark" in content, "Falta Wireshark en contenido_puro.md"
        assert "Burp Suite" in content, "Falta Burp Suite"
        assert "CAMBIAR A" in content, "Falta indicador CAMBIAR A"
        print("  ✅ contenido_puro.md tiene estructura correcta")

    print("\n✅ Knowledge files verificados\n")
    return True


def main():
    print("\n" + "=" * 60)
    print("  PRUEBAS DE MODOS DE CONTENIDO DE TERCEROS")
    print("=" * 60 + "\n")

    tests = [
        ("Configuración de modos", test_third_party_modes_config),
        ("AI Engine soporte", test_ai_engine_has_content_modes),
        ("Generación de prompts", test_prompt_generation),
        ("Archivos de knowledge", test_knowledge_files_exist),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except AssertionError as e:
            print(f"  ❌ FALLO: {e}")
            failed += 1
        except Exception as e:
            print(f"  ❌ ERROR: {e}")
            failed += 1

    print("=" * 60)
    print(f"  RESULTADO: {passed} passed, {failed} failed")
    print("=" * 60 + "\n")

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
