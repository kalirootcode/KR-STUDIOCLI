"""
record_engine.py — Grabación de pantalla automática (mss + cv2)
Captura SOLO la región de una ventana Konsole a 30 FPS.
"""
import subprocess
import threading
import time
import os
import logging

logger = logging.getLogger(__name__)


class ScreenRecorder:
    """Graba una ventana específica usando mss + cv2."""

    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.output_path = os.path.join(output_dir, "raw_video.mp4")
        self.is_recording = False
        self.fps = 30
        self._thread = None
        self._region = None  # {"left": x, "top": y, "width": w, "height": h}

    def _get_window_geometry(self, wid: str) -> dict:
        """Obtiene la posición y tamaño de una ventana X11."""
        try:
            result = subprocess.run(
                ['xdotool', 'getwindowgeometry', '--shell', wid],
                capture_output=True, text=True, timeout=5
            )
            geo = {}
            for line in result.stdout.strip().split('\n'):
                if '=' in line:
                    k, v = line.split('=', 1)
                    geo[k.strip()] = int(v.strip())

            # xdotool da X, Y, WIDTH, HEIGHT
            return {
                "left": geo.get("X", 0),
                "top": geo.get("Y", 0),
                "width": geo.get("WIDTH", 450),
                "height": geo.get("HEIGHT", 800)
            }
        except Exception as e:
            logger.warning(f"Error obteniendo geometría: {e}")
            return {"left": 0, "top": 0, "width": 450, "height": 800}

    def start(self, wid: str):
        """Inicia grabación de la ventana especificada en un hilo separado."""
        if self.is_recording:
            logger.warning("Ya hay una grabación en curso")
            return

        self._region = self._get_window_geometry(wid)
        self.is_recording = True
        self._thread = threading.Thread(target=self._record_loop, daemon=True)
        self._thread.start()
        logger.info(f"🔴 Grabación iniciada: {self._region}")

    def stop(self) -> str:
        """Detiene la grabación y retorna la ruta del archivo."""
        self.is_recording = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info(f"⏹ Grabación detenida: {self.output_path}")
        return self.output_path

    def _record_loop(self):
        """Loop principal de captura de pantalla."""
        try:
            import mss
            import cv2
            import numpy as np

            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            w = self._region["width"]
            h = self._region["height"]
            out = cv2.VideoWriter(self.output_path, fourcc, self.fps, (w, h))

            frame_interval = 1.0 / self.fps

            with mss.mss() as sct:
                monitor = {
                    "left": self._region["left"],
                    "top": self._region["top"],
                    "width": w,
                    "height": h
                }

                while self.is_recording:
                    t_start = time.monotonic()

                    frame = np.array(sct.grab(monitor))
                    # mss captura en BGRA, convertir a BGR para cv2
                    frame_bgr = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

                    # Asegurar tamaño correcto
                    if frame_bgr.shape[1] != w or frame_bgr.shape[0] != h:
                        frame_bgr = cv2.resize(frame_bgr, (w, h))

                    out.write(frame_bgr)

                    # Mantener FPS constante
                    elapsed = time.monotonic() - t_start
                    sleep_time = frame_interval - elapsed
                    if sleep_time > 0:
                        time.sleep(sleep_time)

            out.release()
            logger.info(f"✅ Video guardado: {self.output_path}")

        except ImportError as e:
            logger.error(f"Dependencia faltante: {e}. pip install mss opencv-python numpy")
        except Exception as e:
            logger.error(f"Error en grabación: {e}")
