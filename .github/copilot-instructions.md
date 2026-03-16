# Project Guidelines

## Code Style
Python code formatted with Black. Docstrings and UI elements in Spanish. Exemplified in [kr_studio/core/ai_engine.py](kr_studio/core/ai_engine.py) and [kr_studio/ui/main_window.py](kr_studio/ui/main_window.py).

## Architecture
Modular design with core engines (AI, Director, TTS, Video, OBS) in `kr_studio/core/`. UI components in `kr_studio/ui/`. Data flows from AI-generated `guion.json` through DirectorEngine for terminal automation and OBS recording. CleverHans provides adversarial ML attacks/defenses.

## Build and Test
- KR-Studio: `python kr_studio/main.py`
- CleverHans: `pip install -e "."` then `pip install -r requirements/requirements.txt`
- Tests: Run individual `test_*.py` files manually

## Conventions
- Spanish-first prompts and UI; inject context from MemoryManager into AI requests
- sys.path manipulation in main.py for imports
- Threading in video recording; avoid concurrent recordings
- Projects auto-generated in `kr_studio/projects/` (git-ignored)
- System dependencies checked via health_check.py: xdotool, wmctrl, ffmpeg, edge-tts, mpv, konsole required</content>
<parameter name="filePath">/home/rk13/RK13CODE/SCRIPTVIRAL/.github/copilot-instructions.md