import json
import os
import logging
from datetime import datetime
import typing

logger = logging.getLogger(__name__)

class MemoryManager:
    """Gestor de memoria persistente para la IA (estilo MCP Memory Server)."""

    def __init__(self, workspace_dir: str):
        self.memory: typing.Dict[str, typing.Any] = {}
        self.memory_dir = os.path.join(workspace_dir, ".memory")
        os.makedirs(self.memory_dir, exist_ok=True)
        self.memory_file = os.path.join(self.memory_dir, "ai_memory.json")
        self._load_memory()

    def _load_memory(self):
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    self.memory = json.load(f)
            except Exception as e:
                logger.error(f"Error cargando memoria: {e}")
                self.memory = {"preferences": {}, "facts": [], "tools_used": {}}
        else:
            self.memory = {"preferences": {}, "facts": [], "tools_used": {}}

    def _save_memory(self):
        try:
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(self.memory, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error guardando memoria: {e}")

    def _save_entry(self, category: str, key: str, value: typing.Any, timestamp: bool = True):
        """Guarda una entrada genérica en una categoría de memoria."""
        if category not in self.memory:
            self.memory[category] = {} if not timestamp else []

        if timestamp:
            entry = {"timestamp": datetime.now().isoformat(), "content": value}
            self.memory[category].append(entry)  # type: ignore
        else:
            self.memory[category][key] = value  # type: ignore

        self._save_memory()

    def save_fact(self, fact: str) -> str:
        """
        Guarda un hecho o preferencia importante sobre el usuario en la memoria persistente a largo plazo.
        Útil para recordar el estilo de edición, el tono de voz preferido o herramientas favoritas.
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "content": fact
        }
        self.memory["facts"].append(entry)
        self._save_memory()
        logger.info(f"🧠 Memoria guardada: {fact}")
        return f"Éxito: El hecho '{fact}' ha sido guardado permanentemente en memoria."

    def retrieve_memory_context(self) -> str:
        """Obtiene todo el contexto de memoria formateado para inyectarlo en el System Prompt."""
        if not self.memory["facts"] and not self.memory["preferences"]:
            return "No hay memorias almacenadas aún."
        
        context = "MEMORIA PERSISTENTE DEL USUARIO (Recuerda estas preferencias y hechos en tus respuestas y guiones):\n"
        
        if self.memory["preferences"]:
            for k, v in self.memory["preferences"].items():
                context += f"- PREFERENCIA ({k}): {v}\n"
                
        if self.memory["facts"]:
            # Obtener los 15 hechos más recientes
            recent_facts = sorted(self.memory["facts"], key=lambda k: k['timestamp'], reverse=True)[:15]  # type: ignore
            for fact in recent_facts:
                context += f"- HECHO: {fact['content']} (Guardado el: {fact['timestamp'][:10]})\n"
                
        return context

    def save_content_preference(self, content_type: str):
        """Guarda la preferencia de tipo de contenido usado por el usuario."""
        if "content_preferences" not in self.memory:
            self.memory["content_preferences"] = {}

        if content_type not in self.memory["content_preferences"]:
            self.memory["content_preferences"][content_type] = 0

        self.memory["content_preferences"][content_type] += 1
        self._save_memory()
        logger.info(f"🧠 Preferencia de contenido guardada: {content_type}")

    def save_ui_preference(self, key: str, value: typing.Any):
        """Guarda una preferencia de UI."""
        self._save_entry("ui_preferences", key, value, timestamp=False)
        logger.info(f"💾 UI Preference guardada: {key} = {value}")

    def get_ui_preference(self, key: str, default: typing.Any = None) -> typing.Any:
        """Obtiene una preferencia de UI."""
        return self.memory.get("ui_preferences", {}).get(key, default)

    def get_content_preferences(self) -> dict:
        """Obtiene las preferencias de tipos de contenido."""
        return self.memory.get("content_preferences", {})

    def get_tool_functions(self):
        """Devuelve las funciones que el agente IA (Gemini) puede usar como 'tools'."""
        # Se expone `save_fact` estructurada para genai
        return [self.save_fact]
