"""
Módulo de comandos del sistema: abrir apps, buscar en internet, controlar volumen.
"""

import subprocess
import webbrowser
import platform
import sys


def open_application(app_name: str) -> str:
    """Intenta abrir una aplicación por nombre."""
    app_name = app_name.strip().lower()
    system = platform.system()

    # Mapa de nombres comunes → ejecutables
    app_map = {
        "chrome": "chrome" if system != "Windows" else "chrome.exe",
        "google chrome": "chrome",
        "firefox": "firefox",
        "notepad": "notepad.exe",
        "bloc de notas": "notepad.exe",
        "calculadora": "calc.exe",
        "calculator": "calc.exe",
        "explorador": "explorer.exe",
        "explorer": "explorer.exe",
        "paint": "mspaint.exe",
        "word": "winword.exe",
        "excel": "excel.exe",
        "spotify": "spotify.exe",
        "discord": "discord.exe",
        "vscode": "code",
        "visual studio code": "code",
        "cmd": "cmd.exe",
        "terminal": "cmd.exe",
        "taskmgr": "taskmgr.exe",
        "administrador de tareas": "taskmgr.exe",
    }

    executable = app_map.get(app_name, app_name)

    try:
        if system == "Windows":
            subprocess.Popen(executable, shell=True)
        elif system == "Darwin":  # macOS
            subprocess.Popen(["open", "-a", executable])
        else:  # Linux
            subprocess.Popen([executable])
        return f"Abriendo {app_name}..."
    except Exception as e:
        return f"No pude abrir {app_name}. Error: {e}"


def web_search(query: str) -> str:
    """Abre una búsqueda en el navegador predeterminado."""
    query = query.strip()
    url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
    webbrowser.open(url)
    return f"Buscando '{query}' en el navegador..."


def control_volume(action: str) -> str:
    """Controla el volumen del sistema (Windows)."""
    action = action.strip().lower()
    system = platform.system()

    if system != "Windows":
        return "Control de volumen solo disponible en Windows."

    try:
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))

        current = volume.GetMasterVolumeLevelScalar()

        if action == "up":
            new_vol = min(1.0, current + 0.1)
            volume.SetMasterVolumeLevelScalar(new_vol, None)
            return f"Volumen subido al {int(new_vol * 100)}%"
        elif action == "down":
            new_vol = max(0.0, current - 0.1)
            volume.SetMasterVolumeLevelScalar(new_vol, None)
            return f"Volumen bajado al {int(new_vol * 100)}%"
        elif action == "mute":
            muted = volume.GetMute()
            volume.SetMute(not muted, None)
            return "Silenciado" if not muted else "Sonido activado"
    except ImportError:
        return "Instala 'pycaw' para controlar el volumen: pip install pycaw"
    except Exception as e:
        return f"Error controlando volumen: {e}"


def handle_command(response: str) -> str | None:
    """
    Detecta si la respuesta del LLM es un comando especial y lo ejecuta.
    Retorna la respuesta de texto para hablar, o None si no hubo comando.
    """
    response = response.strip()

    if response.startswith("OPEN_APP:"):
        app = response.split("OPEN_APP:", 1)[1].strip()
        return open_application(app)

    if response.startswith("WEB_SEARCH:"):
        query = response.split("WEB_SEARCH:", 1)[1].strip()
        return web_search(query)

    if response.startswith("VOLUME:"):
        action = response.split("VOLUME:", 1)[1].strip()
        return control_volume(action)

    return None
