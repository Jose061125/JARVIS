"""
Módulo de comandos del sistema: abrir apps, buscar en internet, controlar volumen, apagar PC.
"""

import subprocess
import webbrowser
import platform
import os


def open_application(app_name: str) -> str:
    """Intenta abrir una aplicación por nombre."""
    app_name = app_name.strip().lower()
    system = platform.system()

    # Mapa de nombres comunes → ejecutables
    app_map = {
        # Navegadores
        "chrome": "chrome.exe",
        "google chrome": "chrome.exe",
        "edge": "msedge.exe",
        "microsoft edge": "msedge.exe",
        "firefox": "firefox.exe",
        "brave": "brave.exe",
        "opera": "opera.exe",
        # Música / entretenimiento
        "spotify": "spotify.exe",
        "vlc": "vlc.exe",
        # Comunicación
        "discord": "discord.exe",
        "whatsapp": "whatsapp.exe",
        "telegram": "telegram.exe",
        "zoom": "zoom.exe",
        "teams": "teams.exe",
        "microsoft teams": "teams.exe",
        "skype": "skype.exe",
        # Ofimática
        "word": "winword.exe",
        "excel": "excel.exe",
        "powerpoint": "powerpnt.exe",
        "outlook": "outlook.exe",
        # Herramientas del sistema
        "notepad": "notepad.exe",
        "bloc de notas": "notepad.exe",
        "calculadora": "calc.exe",
        "calculator": "calc.exe",
        "explorador": "explorer.exe",
        "explorador de archivos": "explorer.exe",
        "explorer": "explorer.exe",
        "paint": "mspaint.exe",
        "cmd": "cmd.exe",
        "terminal": "cmd.exe",
        "administrador de tareas": "taskmgr.exe",
        "task manager": "taskmgr.exe",
        "panel de control": "control.exe",
        "configuracion": "ms-settings:",
        "configuración": "ms-settings:",
        # Desarrollo
        "vscode": "code",
        "visual studio code": "code",
        # Juegos
        "steam": "steam.exe",
        "epic games": "epicgameslauncher.exe",
    }

    executable = app_map.get(app_name, app_name)

    try:
        if system == "Windows":
            # En Windows, varios navegadores no siempre están en PATH.
            # Usamos protocolos/START para que el sistema resuelva la app instalada.
            if executable == "msedge.exe":
                os.startfile("microsoft-edge:")
            elif executable in ("chrome.exe", "firefox.exe", "brave.exe", "opera.exe"):
                subprocess.Popen(["cmd", "/c", "start", "", executable], shell=True)
            elif executable == "ms-settings:":
                os.startfile("ms-settings:")
            else:
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


def open_website(target: str) -> str:
    """Abre un sitio web directo en el navegador predeterminado."""
    target = target.strip().lower()

    site_map = {
        "instagram": "https://www.instagram.com",
        "facebook": "https://www.facebook.com",
        "whatsapp": "https://web.whatsapp.com",
        "whatsapp web": "https://web.whatsapp.com",
        "gmail": "https://mail.google.com",
        "youtube": "https://www.youtube.com",
        "x": "https://x.com",
        "twitter": "https://x.com",
        "tiktok": "https://www.tiktok.com",
        "linkedin": "https://www.linkedin.com",
        "github": "https://github.com",
        "netflix": "https://www.netflix.com",
    }

    url = site_map.get(target, target)
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    webbrowser.open(url)
    return f"Abriendo {target} en el navegador..."


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


def system_power(action: str) -> str:
    """Controla el estado del sistema: apagar, reiniciar, suspender, bloquear."""
    action = action.strip().lower()
    system = platform.system()

    if system != "Windows":
        return "Control de energía solo disponible en Windows."

    if action == "shutdown":
        subprocess.Popen("shutdown /s /t 10 /c \"ECHONEX: Apagando el equipo...\"", shell=True)
        return "Apagando el equipo en 10 segundos. Escribe 'shutdown /a' en CMD para cancelar."
    elif action == "restart":
        subprocess.Popen("shutdown /r /t 10 /c \"ECHONEX: Reiniciando el equipo...\"", shell=True)
        return "Reiniciando el equipo en 10 segundos. Escribe 'shutdown /a' en CMD para cancelar."
    elif action == "sleep":
        subprocess.Popen("rundll32.exe powrprof.dll,SetSuspendState 0,1,0", shell=True)
        return "Suspendiendo el equipo..."
    elif action == "lock":
        subprocess.Popen("rundll32.exe user32.dll,LockWorkStation", shell=True)
        return "Bloqueando la pantalla..."
    elif action == "unlock":
        return (
            "Windows no permite desbloquear automaticamente sin credenciales (PIN/huella/password). "
            "Por seguridad, debes desbloquear manualmente."
        )
    elif action == "cancel_shutdown":
        subprocess.Popen("shutdown /a", shell=True)
        return "Apagado/reinicio cancelado."
    return f"Acción de energía no reconocida: {action}"


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

    if response.startswith("WEB_OPEN:"):
        target = response.split("WEB_OPEN:", 1)[1].strip()
        return open_website(target)

    if response.startswith("VOLUME:"):
        action = response.split("VOLUME:", 1)[1].strip()
        return control_volume(action)

    if response.startswith("POWER:"):
        action = response.split("POWER:", 1)[1].strip()
        return system_power(action)

    return None
