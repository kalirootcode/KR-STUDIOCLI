import json
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class MemoryManager:
    """Gestor de memoria persistente para la IA (estilo MCP Memory Server)."""

    def __init__(self, workspace_dir: str):
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
            recent_facts = sorted(self.memory["facts"], key=lambda k: k['timestamp'], reverse=True)[:15]
            for fact in recent_facts:
                context += f"- HECHO: {fact['content']} (Guardado el: {fact['timestamp'][:10]})\n"
                
        return context

    def get_tool_functions(self):
        """Devuelve las funciones que el agente IA (Gemini) puede usar como 'tools'."""
        # Se expone `save_fact` estructurada para genai
        return [self.save_fact]
