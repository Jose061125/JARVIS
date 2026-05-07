"""
Interfaz gráfica principal de JARVIS usando customtkinter.
"""

import threading
import customtkinter as ctk
from datetime import datetime
import time
import math
import random
import tkinter as tk

from jarvis.brain import chat, clear_history
from jarvis.tts import speak_async
from jarvis.stt import listen
from jarvis.commands import handle_command
from jarvis.config import ASSISTANT_NAME, WAKE_WORDS

# ── Tema ────────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

QUICK_ACTIONS = [
    ("Spotify", "abre spotify"),
    ("Edge", "abre microsoft edge"),
    ("YouTube", "busca musica lo-fi en youtube"),
    ("Vol +", "sube el volumen"),
    ("Vol -", "baja el volumen"),
    ("Bloquear", "bloquea la pantalla"),
]


class JarvisApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"{ASSISTANT_NAME} - Asistente IA")
        self.geometry("880x650")
        self.resizable(True, True)
        self.minsize(500, 450)

        self._is_listening = False
        self._is_processing = False
        self._wake_mode = False
        self._wake_thread: threading.Thread | None = None
        self._tts_thread: threading.Thread | None = None
        self._hud_mode = "idle"
        self._hud_phase = 0.0

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._build_ui()
        self._animate_hud()
        self._add_message("JARVIS", f"Hola, soy {ASSISTANT_NAME}. ¿En qué puedo ayudarte?", is_bot=True)

    # ── Construcción de la UI ────────────────────────────────────────────────

    def _build_ui(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # ── Marco principal ──
        main = ctk.CTkFrame(self, corner_radius=0)
        main.grid(row=0, column=0, sticky="nsew")
        main.grid_rowconfigure(2, weight=1)
        main.grid_columnconfigure(0, weight=1)

        # ── Header ──
        header = ctk.CTkFrame(main, height=60, corner_radius=0, fg_color="#0c1226")
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)

        ctk.CTkLabel(
            header,
            text=f"● {ASSISTANT_NAME}",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#2ee6a6",
        ).pack(side="left", padx=20, pady=10)

        ctk.CTkLabel(
            header,
            text="Pilot Build",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#8fa2d4",
        ).pack(side="left", padx=(0, 10), pady=10)

        ctk.CTkButton(
            header,
            text="Limpiar",
            width=80,
            height=30,
            command=self._clear_chat,
            fg_color="#27314f",
            hover_color="#344064",
        ).pack(side="right", padx=10)

        self.wake_btn = ctk.CTkButton(
            header,
            text="Wake OFF",
            width=100,
            height=30,
            command=self._toggle_wake_mode,
            fg_color="#3b2d58",
            hover_color="#4c3a70",
        )
        self.wake_btn.pack(side="right", padx=(0, 8))

        # ── HUD reactivo ──
        hud_frame = ctk.CTkFrame(main, corner_radius=10, fg_color="#060a17")
        hud_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(6, 5))
        hud_frame.grid_columnconfigure(0, weight=1)
        self.hud_canvas = tk.Canvas(
            hud_frame,
            height=210,
            bg="#060a17",
            highlightthickness=0,
            bd=0,
        )
        self.hud_canvas.grid(row=0, column=0, sticky="ew")
        self.hud_canvas.bind("<Configure>", lambda _e: self._draw_hud())

        # ── Área de chat ──
        self.chat_box = ctk.CTkScrollableFrame(main, corner_radius=10, fg_color="#070b18")
        self.chat_box.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
        self.chat_box.grid_columnconfigure(0, weight=1)

        # ── Barra de estado ──
        self.status_label = ctk.CTkLabel(
            main, text="Listo", font=ctk.CTkFont(size=12),
            text_color="#8b98ba"
        )
        self.status_label.grid(row=3, column=0, sticky="w", padx=15)

        # ── Acciones rápidas ──
        actions_frame = ctk.CTkFrame(main, height=56, corner_radius=0, fg_color="#0d1328")
        actions_frame.grid(row=4, column=0, sticky="ew")
        actions_frame.grid_columnconfigure(0, weight=1)

        actions_row = ctk.CTkFrame(actions_frame, fg_color="transparent")
        actions_row.grid(row=0, column=0, sticky="w", padx=10, pady=8)

        ctk.CTkLabel(
            actions_row,
            text="Acciones rápidas",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#9fb0d9",
        ).pack(side="left", padx=(0, 8))

        for label, prompt in QUICK_ACTIONS:
            ctk.CTkButton(
                actions_row,
                text=label,
                width=88,
                height=30,
                corner_radius=16,
                fg_color="#1f2d52",
                hover_color="#294075",
                command=lambda p=prompt: self._process_input(p),
            ).pack(side="left", padx=4)

        # ── Panel de entrada ──
        input_frame = ctk.CTkFrame(main, height=60, corner_radius=0, fg_color="#0b1022")
        input_frame.grid(row=5, column=0, sticky="ew", padx=0, pady=0)
        input_frame.grid_columnconfigure(0, weight=1)
        input_frame.grid_propagate(False)

        self.input_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="Escribe un mensaje...",
            font=ctk.CTkFont(size=14),
            height=40,
            corner_radius=20,
            fg_color="#121a33",
            border_color="#2a3b70",
        )
        self.input_entry.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.input_entry.bind("<Return>", lambda _: self._send_text())

        self.send_btn = ctk.CTkButton(
            input_frame,
            text="Enviar",
            width=80,
            height=40,
            corner_radius=20,
            command=self._send_text,
            fg_color="#2f52b0",
            hover_color="#4268c8",
        )
        self.send_btn.grid(row=0, column=1, padx=(0, 5), pady=10)

        self.voice_btn = ctk.CTkButton(
            input_frame,
            text="🎤",
            width=50,
            height=40,
            corner_radius=20,
            fg_color="#1f4b3a",
            hover_color="#28624b",
            command=self._toggle_voice,
        )
        self.voice_btn.grid(row=0, column=2, padx=(0, 10), pady=10)

    # ── Lógica de mensajes ───────────────────────────────────────────────────

    def _add_message(self, sender: str, text: str, is_bot: bool = False):
        """Agrega un bubble de mensaje al chat."""
        row = len(self.chat_box.winfo_children())

        time_str = datetime.now().strftime("%H:%M")
        align = "w" if is_bot else "e"
        bg = "#1e2a3a" if is_bot else "#1a3a1a"
        name_color = "#00d4ff" if is_bot else "#88cc88"

        bubble = ctk.CTkFrame(self.chat_box, corner_radius=12, fg_color=bg)
        bubble.grid(row=row, column=0, sticky=align, padx=10, pady=4, ipadx=8, ipady=6)

        ctk.CTkLabel(
            bubble,
            text=f"{sender}  {time_str}",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=name_color,
        ).pack(anchor="w", padx=8, pady=(4, 0))

        ctk.CTkLabel(
            bubble,
            text=text,
            font=ctk.CTkFont(size=13),
            wraplength=440,
            justify="left",
        ).pack(anchor="w", padx=8, pady=(0, 4))

        # Auto-scroll al final
        self.after(50, lambda: self.chat_box._parent_canvas.yview_moveto(1.0))

    def _set_status(self, text: str):
        self.status_label.configure(text=text)

    def _set_hud_mode(self, mode: str):
        self._hud_mode = mode

    def _draw_hud(self):
        canvas = self.hud_canvas
        canvas.delete("all")
        w = max(420, canvas.winfo_width())
        h = max(190, canvas.winfo_height())
        cx, cy = w // 2, h // 2

        mode_colors = {
            "idle": "#28d7ff",
            "listen": "#3dff9a",
            "think": "#ffcf4a",
            "speak": "#2ee6a6",
            "wake": "#c17cff",
        }
        color = mode_colors.get(self._hud_mode, "#28d7ff")

        pulse = 7 + 8 * (0.5 + 0.5 * math.sin(self._hud_phase * 2.0))
        if self._hud_mode == "idle":
            pulse *= 0.45
        elif self._hud_mode == "wake":
            pulse *= 0.7
        elif self._hud_mode == "think":
            pulse *= 1.15
        elif self._hud_mode == "speak":
            pulse *= 1.3
        elif self._hud_mode == "listen":
            pulse *= 1.45

        # Anillos principales
        canvas.create_oval(cx - 88, cy - 88, cx + 88, cy + 88, outline="#12304d", width=2)
        canvas.create_oval(cx - 70, cy - 70, cx + 70, cy + 70, outline="#143a5f", width=2)
        canvas.create_oval(cx - 48, cy - 48, cx + 48, cy + 48, outline=color, width=3)

        # Segmentos exteriores tipo ecualizador radial
        bars = 54
        for i in range(bars):
            angle = (2 * math.pi * i / bars) + (self._hud_phase * 0.28)
            wave = 0.5 + 0.5 * math.sin(self._hud_phase * 2.8 + i * 0.35)
            jitter = random.uniform(0.0, 0.12)
            amp = (9 + pulse) * (wave + jitter)
            if self._hud_mode in ("idle", "wake"):
                amp *= 0.55

            r1 = 95
            r2 = r1 + amp
            x1 = cx + math.cos(angle) * r1
            y1 = cy + math.sin(angle) * r1
            x2 = cx + math.cos(angle) * r2
            y2 = cy + math.sin(angle) * r2
            canvas.create_line(x1, y1, x2, y2, fill=color, width=2)

        # Arco de progreso animado
        extent = 70 + 40 * math.sin(self._hud_phase)
        canvas.create_arc(
            cx - 110,
            cy - 110,
            cx + 110,
            cy + 110,
            start=(self._hud_phase * 45) % 360,
            extent=extent,
            style=tk.ARC,
            outline=color,
            width=3,
        )

        label_by_mode = {
            "idle": "IDLE",
            "listen": "ESCUCHANDO",
            "think": "PROCESANDO",
            "speak": "HABLANDO",
            "wake": "WAKE MODE",
        }
        canvas.create_text(cx, cy - 6, text=ASSISTANT_NAME, fill="#b7c7e8", font=("Segoe UI", 14, "bold"))
        canvas.create_text(cx, cy + 18, text=label_by_mode.get(self._hud_mode, "IDLE"), fill=color, font=("Segoe UI", 11, "bold"))

    def _animate_hud(self):
        self._hud_phase += 0.11
        self._draw_hud()
        self.after(45, self._animate_hud)

    def _monitor_tts(self):
        if self._tts_thread and self._tts_thread.is_alive():
            self._set_hud_mode("speak")
            self.after(120, self._monitor_tts)
            return
        self._set_hud_mode("wake" if self._wake_mode else "idle")

    # ── Enviar texto ─────────────────────────────────────────────────────────

    def _send_text(self):
        text = self.input_entry.get().strip()
        if not text:
            return
        self.input_entry.delete(0, "end")
        self._process_input(text)

    # ── Voz ──────────────────────────────────────────────────────────────────

    def _toggle_voice(self):
        if self._is_listening:
            return
        if self._is_processing:
            self._set_status("Espera a que termine la respuesta actual...")
            return
        self._is_listening = True
        self.voice_btn.configure(text="⏹", fg_color="#4a1a1a")
        self._set_status("Escuchando...")
        self._set_hud_mode("listen")
        threading.Thread(target=self._listen_worker, daemon=True).start()

    def _listen_worker(self):
        text = listen()
        self._is_listening = False
        self.after(0, lambda: self.voice_btn.configure(text="🎤", fg_color="#1a3a4a"))
        if text:
            self.after(0, lambda: self._process_input(text))
        else:
            self.after(0, lambda: self._set_status("No entendí. Intenta de nuevo."))
            self.after(0, lambda: self._set_hud_mode("wake" if self._wake_mode else "idle"))

    # ── Procesar input (texto o voz) ─────────────────────────────────────────

    def _process_input(self, user_text: str):
        if self._is_processing:
            return
        self._is_processing = True
        self._add_message("Tú", user_text, is_bot=False)
        self._set_status("Pensando y ejecutando...")
        self._set_hud_mode("think")
        self.send_btn.configure(state="disabled")
        threading.Thread(target=self._bot_reply_worker, args=(user_text,), daemon=True).start()

    def _bot_reply_worker(self, user_text: str):
        try:
            reply = chat(user_text)

            # ¿Es un comando del sistema?
            command_result = handle_command(reply)
            display_text = command_result if command_result else reply

            self.after(0, lambda: self._add_message(ASSISTANT_NAME, display_text, is_bot=True))
            self.after(0, lambda: self._set_status("Listo"))

            # Hablar la respuesta
            self._tts_thread = speak_async(display_text)
            self.after(0, self._monitor_tts)
        except Exception as e:
            error_msg = f"Error: {e}"
            self.after(0, lambda: self._add_message(ASSISTANT_NAME, error_msg, is_bot=True))
            self.after(0, lambda: self._set_status("Error"))
            self.after(0, lambda: self._set_hud_mode("wake" if self._wake_mode else "idle"))
        finally:
            self._is_processing = False
            self.after(0, lambda: self.send_btn.configure(state="normal"))

    # ── Wake word / manos libres ─────────────────────────────────────────────

    def _toggle_wake_mode(self):
        self._wake_mode = not self._wake_mode
        if self._wake_mode:
            self.wake_btn.configure(text="Wake ON", fg_color="#1a4a2d", hover_color="#2a6a3d")
            self._set_status("Wake mode activo. Di: Jarvis")
            self._set_hud_mode("wake")
            self._add_message(ASSISTANT_NAME, "Modo manos libres activado. Di 'Jarvis' y luego tu orden.", is_bot=True)
            self._wake_thread = threading.Thread(target=self._wake_worker, daemon=True)
            self._wake_thread.start()
        else:
            self.wake_btn.configure(text="Wake OFF", fg_color="#3a2d44", hover_color="#4d3a5c")
            self._set_status("Wake mode desactivado")
            self._set_hud_mode("idle")

    def _wake_worker(self):
        while self._wake_mode:
            if self._is_listening or self._is_processing:
                time.sleep(0.2)
                continue

            heard = listen(timeout=2, phrase_limit=4)
            if not heard:
                continue

            heard_lower = heard.lower()
            if not any(w in heard_lower for w in WAKE_WORDS):
                continue

            self.after(0, lambda: self._set_status("Wake detectado. Te escucho..."))
            self.after(0, lambda: self._set_hud_mode("listen"))
            command_text = listen(timeout=5, phrase_limit=9)
            if command_text:
                self.after(0, lambda txt=command_text: self._process_input(txt))
            else:
                self.after(0, lambda: self._set_status("No escuché el comando tras la palabra clave."))
                self.after(0, lambda: self._set_hud_mode("wake" if self._wake_mode else "idle"))

    def _on_close(self):
        self._wake_mode = False
        self.destroy()

    # ── Limpiar chat ─────────────────────────────────────────────────────────

    def _clear_chat(self):
        for widget in self.chat_box.winfo_children():
            widget.destroy()
        clear_history()
        self._add_message(ASSISTANT_NAME, "Historial limpiado. ¿En qué puedo ayudarte?", is_bot=True)


def run():
    app = JarvisApp()
    app.mainloop()
