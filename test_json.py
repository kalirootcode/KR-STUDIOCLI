import sys
sys.path.insert(0, '/home/rk13/RK13CODE/SCRIPTVIRAL')
from kr_studio.ui.main_window import MainWindow
import tkinter as tk

root = tk.Tk()
app = MainWindow(root)

# Simulate _active_tab="b", editor_b containing valid JSON, and launch_solo
app._active_tab = "b"
app.editor_b.insert("end", '[{"tipo": "narracion", "voz": "prueba"}]')
print("JSON parsed:", app._parse_editor_json())

def mock_get_last_user_topic(): return "Tema Prueba"
app._get_last_user_topic = mock_get_last_user_topic

app.launch_solo()
import time
time.sleep(2)
