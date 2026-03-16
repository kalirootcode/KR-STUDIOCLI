import shutil
import logging
import typing

logger = logging.getLogger(__name__)


class HealthChecker:

    REQUIRED = {
        "xdotool":  "Control de ventanas X11",
        "wmctrl":   "Redimensionar ventanas",
        "ffmpeg":   "Convertir audio TTS a WAV",
        "edge-tts": "Síntesis de voz TTS",
        "mpv":      "Reproducción de audio",
        "konsole":  "Terminal para secuencias",
    }

    OPTIONAL = {
        "docker": "Sandbox de ejecución aislada",
        "obs":    "Grabación automática",
        "script": "Logging de terminales",
        "xclip":  "Lectura de clipboard",
    }

    def run(self) -> dict:
        results: typing.Dict[str, typing.Any] = {"required": {}, "optional": {}, "ok": True}

        for tool, desc in self.REQUIRED.items():
            path = shutil.which(tool)
            results["required"][tool] = {
                "available": path is not None,
                "path": path,
                "description": desc,
            }
            if path is None:
                results["ok"] = False

        for tool, desc in self.OPTIONAL.items():
            path = shutil.which(tool)
            results["optional"][tool] = {
                "available": path is not None,
                "path": path,
                "description": desc,
            }

        return results

    def format_report(self, results: dict) -> str:
        lines = ["🔍 DIAGNÓSTICO DEL SISTEMA\n"]

        lines.append("  REQUERIDAS:")
        for tool, info in results["required"].items():
            icon = "✅" if info["available"] else "❌"
            lines.append(f"    {icon} {tool} — {info['description']}")

        lines.append("\n  OPCIONALES:")
        for tool, info in results["optional"].items():
            icon = "✅" if info["available"] else "⚠"
            lines.append(f"    {icon} {tool} — {info['description']}")

        if not results["ok"]:
            lines.append("\n  ❌ Faltan dependencias requeridas.")
            lines.append("  Ejecuta: sudo apt install xdotool wmctrl ffmpeg konsole")
            lines.append("           pip install edge-tts")
        else:
            lines.append("\n  ✅ Sistema listo para producción.")

        return "\n".join(lines)
