import ctypes
import os
import json
from PyQt5.QtWidgets import QFileDialog

def prevent_sleep():
    ctypes.windll.kernel32.SetThreadExecutionState(0x80000002)

def restore_sleep():
    ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)

def choose_manga():
    file_path, _ = QFileDialog.getOpenFileName(None, "Open Manga File", "", "JSON Files (*.json);;All Files (*)")
    if not file_path:
        return {}
    
    with open(file_path, "r") as f:
        return json.load(f)
