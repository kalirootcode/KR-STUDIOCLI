import subprocess
import time
import logging
import typing

logger = logging.getLogger(__name__)


class X11Controller:
    """Controlador centralizado de ventanas X11 via xdotool/wmctrl."""

    def focus_window(self, wid: str) -> bool:
        try:
            subprocess.run(
                ["xdotool", "windowactivate", "--sync", wid],
                capture_output=True,
                timeout=5,
            )
            time.sleep(0.3)
            return True
        except Exception as e:
            logger.warning(f"focus_window falló: {e}")
            return False

    def type_text(
        self,
        wid: str,
        text: str,
        speed_pct: int = 80,
        delay_ms: typing.Optional[int] = None,
    ):
        """Escribe una cadena de texto directamente en una ventana específica."""
        if speed_pct < 100:
            calculated_delay = int(120 + (100 - speed_pct) * 4)
        else:
            calculated_delay = max(5, int(120 - (speed_pct - 100)))
        delay = delay_ms if delay_ms is not None else calculated_delay

        try:
            # Comando más robusto que no depende del foco
            logger.info(f"x11: Escribiendo en WID {wid} (delay: {delay}ms)")
            result = subprocess.run(
                [
                    "xdotool",
                    "type",
                    "--window",
                    wid,
                    "--clearmodifiers",
                    "--delay",
                    str(delay),
                    text,
                ],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode != 0:
                logger.error(f"xdotool type failed (WID: {wid}): {result.stderr}")
        except Exception as e:
            logger.error(f"type_text falló: {e}")

    def send_key(self, wid: str, key: str):
        """Envía una tecla a una ventana específica."""
        try:
            logger.info(f"x11: Enviando tecla '{key}' a ventana {wid}")
            result = subprocess.run(
                ["xdotool", "key", "--window", wid, "--clearmodifiers", key],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode != 0:
                logger.error(f"xdotool key failed (WID: {wid}): {result.stderr}")
        except Exception as e:
            logger.error(f"send_key falló: {e}")

    def resize_window(self, wid: str, w: int = 450, h: int = 800):
        try:
            hex_wid = hex(int(wid))
            result = subprocess.run(
                ["wmctrl", "-i", "-r", hex_wid, "-e", f"0,-1,-1,{w},{h}"],
                capture_output=True,
                timeout=5,
            )
            if result.returncode != 0:
                raise RuntimeError("wmctrl falló")
        except Exception:
            try:
                subprocess.run(
                    ["xdotool", "windowsize", wid, str(w), str(h)],
                    capture_output=True,
                    timeout=5,
                )
            except Exception:
                pass

    def find_konsole_wids(self) -> list:
        for search_type, term in [("--class", "konsole"), ("--name", "Konsole")]:
            try:
                result = subprocess.run(
                    ["xdotool", "search", search_type, term],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                wids = [
                    w.strip() for w in result.stdout.strip().split("\n") if w.strip()
                ]
                if wids:
                    return wids
            except Exception:
                pass
        return []
