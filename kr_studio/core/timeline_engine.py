"""
timeline_engine.py — Motor de timeline para el editor de video profesional.
Gestiona clips de video y audio como objetos con posición, duración y track.
"""
import os
import logging
import copy
from dataclasses import dataclass, field
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class Clip:
    """Representa un clip (video o audio) en el timeline."""
    clip_id: int
    source_path: str           # Ruta al archivo original
    track: str                 # "V1", "A1", "A2"
    start: float               # Posición de inicio en el timeline (segundos)
    duration: float            # Duración del clip (segundos)
    source_start: float = 0.0  # Offset dentro del archivo fuente (para subclips)
    muted: bool = False
    label: str = ""

    @property
    def end(self) -> float:
        return self.start + self.duration

    def __repr__(self):
        return f"Clip({self.clip_id}, {self.label}, track={self.track}, {self.start:.1f}s-{self.end:.1f}s)"


class TimelineEngine:
    """Motor del timeline: gestiona clips, soporta split/move/delete/undo."""

    def __init__(self, workspace_dir: str):
        self.workspace_dir = workspace_dir
        self.clips: List[Clip] = []
        self._next_id = 1
        self._undo_stack: List[List[Clip]] = []
        self._max_undo = 20

    # ─── Estado ───

    def _save_undo(self):
        """Guarda una copia profunda del estado actual para deshacer."""
        snapshot = copy.deepcopy(self.clips)
        self._undo_stack.append(snapshot)
        if len(self._undo_stack) > self._max_undo:
            self._undo_stack.pop(0)

    def undo(self) -> bool:
        """Deshace la última acción. Retorna True si se pudo deshacer."""
        if not self._undo_stack:
            return False
        self.clips = self._undo_stack.pop()
        return True

    # ─── CRUD de Clips ───

    def add_clip(self, source_path: str, track: str, start: float,
                 duration: float, label: str = "", source_start: float = 0.0) -> Clip:
        """Añade un clip al timeline."""
        self._save_undo()
        clip = Clip(
            clip_id=self._next_id,
            source_path=source_path,
            track=track,
            start=start,
            duration=duration,
            source_start=source_start,
            label=label or os.path.basename(source_path)
        )
        self._next_id += 1
        self.clips.append(clip)
        logger.info(f"➕ Clip añadido: {clip}")
        return clip

    def remove_clip(self, clip_id: int) -> bool:
        """Elimina un clip por su ID."""
        self._save_undo()
        before = len(self.clips)
        self.clips = [c for c in self.clips if c.clip_id != clip_id]
        removed = len(self.clips) < before
        if removed:
            logger.info(f"🗑 Clip {clip_id} eliminado.")
        return removed

    def get_clip_by_id(self, clip_id: int) -> Optional[Clip]:
        for c in self.clips:
            if c.clip_id == clip_id:
                return c
        return None

    def get_clip_at(self, track: str, time_pos: float) -> Optional[Clip]:
        """Obtiene el clip en una pista y posición temporal específica."""
        for c in self.clips:
            if c.track == track and c.start <= time_pos < c.end:
                return c
        return None

    def get_clips_on_track(self, track: str) -> List[Clip]:
        """Retorna todos los clips de una pista, ordenados por start."""
        return sorted([c for c in self.clips if c.track == track], key=lambda c: c.start)

    # ─── Edición ───

    def to_dict(self) -> dict:
        """Serializa el estado actual del timeline a un diccionario."""
        return {
            "version": "1.0",
            "total_duration": self.total_duration,
            "next_id": self._next_id,
            "clips": [
                {
                    "clip_id": c.clip_id,
                    "source_path": c.source_path,
                    "track": c.track,
                    "start": c.start,
                    "end": c.end,
                    "source_start": c.source_start,
                    "duration": c.duration,
                    "label": c.label,
                    "muted": c.muted
                }
                for c in self.clips
            ]
        }

    def from_dict(self, data: dict):
        """Reconstruye el timeline a partir de un diccionario."""
        self.clips.clear()
        self._undo_stack.clear()
        self._next_id = data.get("next_id", 1)
        self.total_duration = data.get("total_duration", 0.0)
        
        for cdict in data.get("clips", []):
            clip = Clip(
                clip_id=cdict["clip_id"],
                source_path=cdict["source_path"],
                track=cdict["track"],
                start=cdict["start"],
                duration=cdict["duration"],
                label=cdict["label"],
                source_start=cdict.get("source_start", 0.0),
                muted=cdict.get("muted", False)
            )
            # Asegurar end manual si está pre-dictated
            if "end" in cdict:
                clip.end = cdict["end"]
            self.clips.append(clip)
        
        self.total_duration = max([c.end for c in self.clips] + [0.0])

    def split_clip_at(self, clip_id: int, split_time: float) -> bool:
        """Divide un clip en dos en la posición dada (tiempo absoluto del timeline)."""
        clip = self.get_clip_by_id(clip_id)
        if not clip:
            return False
        if split_time <= clip.start or split_time >= clip.end:
            return False  # No se puede dividir fuera del clip

        self._save_undo()

        # Duración de cada parte
        left_dur = split_time - clip.start
        right_dur = clip.end - split_time
        right_source_start = clip.source_start + left_dur

        # Modificar el clip original (parte izquierda)
        clip.duration = left_dur

        # Crear la parte derecha
        right_clip = Clip(
            clip_id=self._next_id,
            source_path=clip.source_path,
            track=clip.track,
            start=split_time,
            duration=right_dur,
            source_start=right_source_start,
            label=clip.label + " (R)",
            muted=clip.muted
        )
        self._next_id += 1
        self.clips.append(right_clip)
        logger.info(f"✂ Clip {clip.clip_id} dividido en {split_time:.1f}s → L:{left_dur:.1f}s R:{right_dur:.1f}s")
        return True

    def move_clip(self, clip_id: int, new_start: float) -> bool:
        """Mueve un clip a una nueva posición de inicio."""
        clip = self.get_clip_by_id(clip_id)
        if not clip:
            return False
        if new_start < 0:
            new_start = 0.0

        self._save_undo()
        old_start = clip.start
        clip.start = new_start
        logger.info(f"↔ Clip {clip_id} movido de {old_start:.1f}s a {new_start:.1f}s")
        return True

    def toggle_mute(self, clip_id: int) -> bool:
        """Alterna el mute de un clip de audio."""
        clip = self.get_clip_by_id(clip_id)
        if not clip:
            return False
        self._save_undo()
        clip.muted = not clip.muted
        logger.info(f"🔇 Clip {clip_id} muted={clip.muted}")
        return True

    # ─── Duración total ───

    @property
    def total_duration(self) -> float:
        """Duración total del timeline (hasta el final del último clip)."""
        if not self.clips:
            return 0.0
        return max(c.end for c in self.clips)

    def get_source_time_at(self, track: str, timeline_pos: float):
        """
        Dado un tiempo en el timeline, retorna (source_path, source_time, clip)
        del clip activo en esa posición, o None si hay un gap (sin clip).
        """
        clip = self.get_clip_at(track, timeline_pos)
        if clip is None:
            return None
        # Calcular posición dentro del archivo fuente
        offset_in_clip = timeline_pos - clip.start
        source_time = clip.source_start + offset_in_clip
        return (clip.source_path, source_time, clip)

    def get_top_video_clip_at(self, timeline_pos: float):
        """
        Busca de arriba hacia abajo (V3 -> V2 -> V1) el primer clip de video visible.
        Retorna (source_path, source_time, clip) o None.
        """
        for track in ["V3", "V2", "V1"]:
            res = self.get_source_time_at(track, timeline_pos)
            if res:
                return res
        return None

    def get_next_video_clip_start(self, timeline_pos: float) -> float:
        """Encuentra el inicio del próximo clip de video en CUALQUIER pista (V1/V2/V3)."""
        next_starts = []
        for track in ["V3", "V2", "V1"]:
            ns = self.get_next_clip_start(track, timeline_pos)
            if ns > 0:
                next_starts.append(ns)
        return min(next_starts) if next_starts else -1.0

    def get_next_clip_start(self, track: str, timeline_pos: float) -> float:
        """Retorna el inicio del siguiente clip después de timeline_pos, o -1 si no hay más."""
        clips = self.get_clips_on_track(track)
        for c in clips:
            if c.start > timeline_pos:
                return c.start
        return -1.0

    # ─── Auto-detección de Audios TTS ───

    def auto_load_tts_audios(self, audio_dir: str, timestamps: dict = None):
        """
        Detecta archivos .wav en audio_dir y los añade automáticamente
        a la pista A1 con posiciones basadas en timestamps.
        """
        if not os.path.isdir(audio_dir):
            return

        audio_files = sorted([f for f in os.listdir(audio_dir) if f.endswith('.wav')])
        if not audio_files:
            return

        # Limpiar audios previos de A1
        self.clips = [c for c in self.clips if c.track != "A1"]

        # Obtener timestamps de audio
        audio_ts = []
        if timestamps:
            audio_ts = sorted([
                (k, v) for k, v in timestamps.items()
                if "audio" in k.lower() or "tts" in k.lower() or "narr" in k.lower()
            ], key=lambda x: x[1])

        for idx, audio_file in enumerate(audio_files):
            audio_path = os.path.join(audio_dir, audio_file)

            # Obtener duración real del archivo
            dur = self._get_audio_duration(audio_path)

            # Posicionar según timestamps o distribuir equitativamente
            if idx < len(audio_ts):
                start = audio_ts[idx][1]
            else:
                start = idx * 5.0  # Fallback: cada 5 segundos

            self.add_clip(
                source_path=audio_path,
                track="A1",
                start=start,
                duration=dur,
                label=audio_file
            )

        logger.info(f"🎧 Auto-cargados {len(audio_files)} audios TTS en pista A1")

    def auto_load_video(self, video_path: str):
        """Carga un video en la pista V1, detectando su duración."""
        # Limpiar clips previos de V1
        self.clips = [c for c in self.clips if c.track != "V1"]

        dur = self._get_video_duration(video_path)
        self.add_clip(
            source_path=video_path,
            track="V1",
            start=0.0,
            duration=dur,
            label=os.path.basename(video_path)
        )
        logger.info(f"📹 Video cargado en V1: {dur:.1f}s")

    # ─── Helpers ───

    def _get_audio_duration(self, path: str) -> float:
        """Obtiene duración de un archivo de audio (WAV o MP3)."""
        try:
            import wave
            with wave.open(path, 'r') as wf:
                return wf.getnframes() / float(wf.getframerate())
        except Exception:
            pass
        try:
            from mutagen.mp3 import MP3
            audio = MP3(path)
            return audio.info.length
        except Exception:
            pass
        try:
            from moviepy import AudioFileClip
            clip = AudioFileClip(path)
            dur = clip.duration
            clip.close()
            return dur
        except Exception:
            return 4.0  # Fallback

    def _get_video_duration(self, path: str) -> float:
        """Obtiene duración de un archivo de video o imagen."""
        if path.lower().endswith(('.png', '.jpg', '.jpeg')):
            return 5.0  # Default duration for images
        try:
            from moviepy import VideoFileClip
            clip = VideoFileClip(path)
            dur = clip.duration
            clip.close()
            return dur
        except Exception:
            return 60.0  # Fallback: 1 minuto
