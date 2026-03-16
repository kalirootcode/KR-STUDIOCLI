import os
import json
import shutil
import time
from datetime import datetime
import typing
from typing import cast

class WorkspaceManager:
    """
    Gestiona workspaces aislados por proyecto/capítulo.
    Estructura:
      workspace/
        projects/
          {serie_slug}/
            master_structure.json
            capitulo_1/
              guion.json
              audio/
              logs/
              exports/
            capitulo_2/
              ...
        sessions/
          {timestamp}_{tema}/
            guion.json
            audio/
            logs/
    """
    
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.projects_dir = os.path.join(base_dir, "projects")
        self.sessions_dir = os.path.join(base_dir, "sessions")
        os.makedirs(self.projects_dir, exist_ok=True)
        os.makedirs(self.sessions_dir, exist_ok=True)
        self._active_session: typing.Optional[dict] = None
    
    def create_session(self, topic: str, chapter: typing.Optional[int] = None) -> dict:
        """Crea un workspace temporal para una sesión de grabación."""
        import re
        slug = re.sub(r'[^a-zA-Z0-9]', '_', topic)[:40]  # type: ignore
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = f"{ts}_{slug}"
        if chapter is not None:
            name += f"_cap{chapter}"
        
        session_dir = os.path.join(self.sessions_dir, name)
        session = {
            "name": name,
            "topic": topic,
            "chapter": chapter,
            "created_at": ts,
            "dir": session_dir,
            "audio_dir": os.path.join(session_dir, "audio"),
            "logs_dir": os.path.join(session_dir, "logs"),
            "exports_dir": os.path.join(session_dir, "exports"),
        }
        
        for d in [session["dir"], session["audio_dir"],
                  session["logs_dir"], session["exports_dir"]]:
            if d:
                os.makedirs(str(d), exist_ok=True)
        
        # Guardar metadata de la sesión
        with open(os.path.join(session_dir, "session.json"), "w") as f:
            json.dump(session, f, indent=2)
        
        self._active_session = session
        return session
    
    def get_active_session(self) -> dict:
        return cast(dict, self._active_session) if self._active_session else {}
    
    def save_guion(self, json_data: list, session: typing.Optional[dict] = None) -> str:
        """Guarda el JSON del guion en el workspace de la sesión."""
        target = session or self._active_session
        if not target:
            return ""
        path = os.path.join(target["dir"], "guion.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=4, ensure_ascii=False)
        return path
    
    def get_audio_path(self, index: int, text_hash: str, 
                        session: typing.Optional[dict] = None) -> str:
        """Retorna la ruta de audio para una escena dentro del workspace."""
        target = session or self._active_session
        if not target:
            return ""
        return os.path.join(target["audio_dir"], 
                            f"audio_{index:03d}_{text_hash}.wav")
    
    def list_sessions(self, count: int = 20) -> list:
        """Lista todas las sesiones existentes."""
        sessions = []
        for name in sorted(os.listdir(self.sessions_dir), reverse=True):
            meta_path = os.path.join(self.sessions_dir, name, "session.json")
            if os.path.exists(meta_path):
                try:
                    with open(meta_path, "r", encoding="utf-8") as f:
                        sessions.append(json.load(f))
                except Exception:
                    pass
        return sessions[:count]  # type: ignore
    
    def cleanup_old_sessions(self, keep_days: int = 7):
        """Elimina sesiones más antiguas de X días."""
        cutoff = time.time() - (keep_days * 86400)
        for name in os.listdir(self.sessions_dir):
            session_dir = os.path.join(self.sessions_dir, name)
            if os.path.getmtime(session_dir) < cutoff:
                shutil.rmtree(session_dir, ignore_errors=True)
