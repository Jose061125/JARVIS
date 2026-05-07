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


class JarvisApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"{ASSISTANT_NAME} - Asistente IA")
        self.geometry("980x700")
        self.resizable(True, True)
        self.minsize(500, 450)

        self._is_listening = False
        self._is_processing = False
        self._wake_mode = False
        self._wake_thread: threading.Thread | None = None
        self._tts_thread: threading.Thread | None = None
        self._hud_mode = "idle"
        self._hud_phase = 0.0
        self._welcome_phase = 0.0
        self._welcome_active = True
        self._start_transition_step = 0

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._build_welcome_screen()

    def _build_welcome_screen(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.welcome_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="#050912")
        self.welcome_frame.grid(row=0, column=0, sticky="nsew")
        self.welcome_frame.grid_columnconfigure(0, weight=1)
        self.welcome_frame.grid_rowconfigure(0, weight=1)

        self.welcome_canvas = tk.Canvas(
            self.welcome_frame,
            bg="#040914",
            highlightthickness=0,
            bd=0,
        )
        self.welcome_canvas.grid(row=0, column=0, sticky="nsew")
        self.welcome_canvas.bind("<Configure>", lambda _e: self._draw_welcome_background())

        self.left_panel = ctk.CTkFrame(self.welcome_frame, fg_color="#06102a", corner_radius=18, border_width=1, border_color="#1a315a")
        self.left_panel.place(relx=0.12, rely=0.5, relwidth=0.16, relheight=0.88, anchor="center")
        self.left_panel.bind("<Enter>", lambda _e: self._set_panel_hover(self.left_panel, True))
        self.left_panel.bind("<Leave>", lambda _e: self._set_panel_hover(self.left_panel, False))

        self.logo_canvas = tk.Canvas(self.left_panel, width=120, height=120, bg="#06102a", highlightthickness=0, bd=0)
        self.logo_canvas.place(relx=0.5, rely=0.08, anchor="center")

        ctk.CTkLabel(
            self.left_panel,
            text=ASSISTANT_NAME,
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#2ee6a6",
        ).place(relx=0.5, rely=0.18, anchor="center")

        menu_items = ["Inicio", "Voz", "Navegador", "Configuracion", "Acerca de"]
        for idx, item in enumerate(menu_items):
            y = 0.22 + idx * 0.1
            active = item == "Inicio"
            ctk.CTkButton(
                self.left_panel,
                text=item,
                width=130,
                height=36,
                corner_radius=18,
                fg_color="#2a47b8" if active else "#101f47",
                hover_color="#3557cf" if active else "#173061",
                text_color="#d8e5ff" if active else "#9eb3df",
                command=lambda: None,
            ).place(relx=0.5, rely=y, anchor="center")

        ctk.CTkLabel(
            self.left_panel,
            text="SISTEMA ACTIVO",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#4ee39a",
        ).place(relx=0.5, rely=0.9, anchor="center")

        self.welcome_card = ctk.CTkFrame(self.welcome_frame, fg_color="#0a142a", corner_radius=22, border_width=1, border_color="#1c3e73")
        self.welcome_card.place(relx=0.5, rely=0.5, relwidth=0.5, relheight=0.66, anchor="center")

        ctk.CTkLabel(
            self.welcome_card,
            text="ENTERPRISE AI CORE",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#4fb8ff",
        ).place(relx=0.5, rely=0.12, anchor="center")

        self.welcome_title_label = ctk.CTkLabel(
            self.welcome_card,
            text=f"{ASSISTANT_NAME}",
            font=ctk.CTkFont(size=62, weight="bold"),
            text_color="#2ee6a6",
        )
        self.welcome_title_label.place(relx=0.5, rely=0.32, anchor="center")

        ctk.CTkLabel(
            self.welcome_card,
            text="Asistente inteligente para tu PC",
            font=ctk.CTkFont(size=20),
            text_color="#90a3cf",
        ).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            self.welcome_card,
            text="Voz, comandos del sistema y navegador en tiempo real",
            font=ctk.CTkFont(size=14),
            text_color="#6e81ad",
        ).place(relx=0.5, rely=0.58, anchor="center")

        self.start_btn = ctk.CTkButton(
            self.welcome_card,
            text="Iniciar JARVIS",
            width=230,
            height=50,
            corner_radius=24,
            fg_color="#1c8cff",
            hover_color="#36a0ff",
            command=self._start_jarvis,
        )
        self.start_btn.place(relx=0.5, rely=0.78, anchor="center")

        self.right_panel = ctk.CTkFrame(self.welcome_frame, fg_color="#06102a", corner_radius=18, border_width=1, border_color="#1a315a")
        self.right_panel.place(relx=0.88, rely=0.5, relwidth=0.16, relheight=0.88, anchor="center")
        self.right_panel.bind("<Enter>", lambda _e: self._set_panel_hover(self.right_panel, True))
        self.right_panel.bind("<Leave>", lambda _e: self._set_panel_hover(self.right_panel, False))

        ctk.CTkLabel(
            self.right_panel,
            text="ESTADO DEL SISTEMA",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#a5b8e9",
        ).place(relx=0.5, rely=0.08, anchor="center")

        ctk.CTkLabel(
            self.right_panel,
            text="Optimo",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#2ee6a6",
        ).place(relx=0.5, rely=0.16, anchor="center")

        ctk.CTkLabel(
            self.right_panel,
            text="ACERCA DE",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#a5b8e9",
        ).place(relx=0.5, rely=0.36, anchor="center")

        about_text = (
            f"{ASSISTANT_NAME} escucha tu voz,\n"
            "ejecuta comandos del sistema,\n"
            "abre apps y sitios web,\n"
            "y responde con IA en tiempo real."
        )
        ctk.CTkLabel(
            self.right_panel,
            text=about_text,
            font=ctk.CTkFont(size=12),
            justify="left",
            text_color="#8ea4d3",
        ).place(relx=0.5, rely=0.56, anchor="center")

        self._animate_welcome()

    def _draw_welcome_background(self):
        if not getattr(self, "welcome_canvas", None):
            return

        canvas = self.welcome_canvas
        canvas.delete("all")
        w = max(700, canvas.winfo_width())
        h = max(500, canvas.winfo_height())
        phase = self._welcome_phase

        # Rejilla de fondo
        for x in range(0, w, 56):
            canvas.create_line(x, 0, x, h, fill="#081531", width=1)
        for y in range(0, h, 56):
            canvas.create_line(0, y, w, y, fill="#081531", width=1)

        # Dos núcleos brillantes laterales
        left_x, right_x, cy = int(w * 0.2), int(w * 0.8), int(h * 0.52)
        pulse_a = 1.0 + 0.08 * math.sin(phase * 1.8)
        pulse_b = 1.0 + 0.08 * math.cos(phase * 1.6)

        self._draw_welcome_core(canvas, left_x, cy, int(130 * pulse_a), "#1ed7ff")
        self._draw_welcome_core(canvas, right_x, cy, int(130 * pulse_b), "#2ee6a6")

        # Nucleo central animado principal
        center_x, center_y = int(w * 0.5), int(h * 0.58)
        core_r = int(min(w, h) * 0.2 * (1.0 + 0.04 * math.sin(phase * 2.3)))
        self._draw_welcome_core(canvas, center_x, center_y, core_r, "#ae58ff")

        # Orbita y onda para dar sensacion de movimiento continuo
        orbit_w = int(core_r * 2.6)
        orbit_h = int(core_r * 0.8)
        canvas.create_arc(
            center_x - orbit_w,
            center_y - orbit_h,
            center_x + orbit_w,
            center_y + orbit_h,
            start=(phase * 40) % 360,
            extent=220,
            style=tk.ARC,
            outline="#3f83ff",
            width=2,
        )

        wave_y = center_y
        wave_start = int(w * 0.34)
        wave_end = int(w * 0.66)
        prev_x, prev_y = wave_start, wave_y
        for x in range(wave_start + 6, wave_end, 6):
            rel = (x - wave_start) / max(1, (wave_end - wave_start))
            amp = 20 * (0.3 + 0.7 * math.sin(rel * math.pi))
            y = wave_y + int(amp * math.sin(phase * 5.0 + rel * 20.0))
            canvas.create_line(prev_x, prev_y, x, y, fill="#45d3ff", width=2)
            prev_x, prev_y = x, y

        # Barras decorativas superiores
        for i in range(7):
            bar_h = 18 + int(26 * (0.5 + 0.5 * math.sin(phase * 2.1 + i)))
            x0 = int(w * 0.88) + i * 10
            canvas.create_rectangle(x0, int(h * 0.12) - bar_h, x0 + 6, int(h * 0.12), fill="#18cfff", outline="")

    def _draw_welcome_core(self, canvas: tk.Canvas, x: int, y: int, r: int, color: str):
        canvas.create_oval(x - r, y - r, x + r, y + r, outline="#103455", width=2)
        canvas.create_oval(x - int(r * 0.72), y - int(r * 0.72), x + int(r * 0.72), y + int(r * 0.72), outline=color, width=2)
        canvas.create_oval(x - int(r * 0.44), y - int(r * 0.44), x + int(r * 0.44), y + int(r * 0.44), outline="#2a5d8b", width=2)

    def _draw_logo_orb(self):
        if not getattr(self, "logo_canvas", None):
            return
        c = self.logo_canvas
        c.delete("all")
        phase = self._welcome_phase
        cx, cy = 60, 60
        r = int(42 + 4 * math.sin(phase * 2.4))

        c.create_oval(cx - (r + 9), cy - (r + 9), cx + (r + 9), cy + (r + 9), outline="#173a63", width=2)
        c.create_oval(cx - r, cy - r, cx + r, cy + r, outline="#49d8ff", width=2)
        c.create_arc(cx - (r + 14), cy - (r + 14), cx + (r + 14), cy + (r + 14), start=(phase * 55) % 360, extent=200, style=tk.ARC, outline="#b665ff", width=2)
        c.create_text(cx, cy, text=ASSISTANT_NAME[:1].upper(), fill="#78e2ff", font=("Segoe UI", 34, "bold"))

    def _set_panel_hover(self, panel: ctk.CTkFrame, active: bool):
        if active:
            panel.configure(border_color="#49b9ff", fg_color="#08173a")
        else:
            panel.configure(border_color="#1a315a", fg_color="#06102a")

    def _animate_welcome(self):
        if not self._welcome_active:
            return
        self._welcome_phase += 0.08
        self._draw_welcome_background()
        self._draw_logo_orb()

        # Pulso neon para el titulo principal
        if getattr(self, "welcome_title_label", None):
            glow = 0.5 + 0.5 * math.sin(self._welcome_phase * 2.0)
            r = int(90 + 80 * glow)
            g = int(90 + 130 * glow)
            b = 255
            self.welcome_title_label.configure(text_color=f"#{r:02x}{g:02x}{b:02x}")

        self.after(45, self._animate_welcome)

    def _start_jarvis(self):
        self.start_btn.configure(state="disabled", text="Inicializando...")
        self._run_start_transition()

    def _run_start_transition(self):
        self._start_transition_step += 1
        t = self._start_transition_step

        # Mini transición: card asciende y reduce levemente mientras "inicializa"
        if getattr(self, "welcome_card", None):
            rely = 0.5 - (t * 0.004)
            relwidth = 0.5 - (t * 0.004)
            relheight = 0.66 - (t * 0.005)
            self.welcome_card.place(relx=0.5, rely=max(0.38, rely), relwidth=max(0.34, relwidth), relheight=max(0.40, relheight), anchor="center")

        if t < 18:
            self.after(22, self._run_start_transition)
            return

        self._welcome_active = False
        self.welcome_frame.destroy()
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
        main.grid_rowconfigure(1, weight=1)
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
        hud_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(6, 5))
        hud_frame.grid_columnconfigure(0, weight=1)
        hud_frame.grid_rowconfigure(0, weight=1)
        self.hud_canvas = tk.Canvas(
            hud_frame,
            bg="#060a17",
            highlightthickness=0,
            bd=0,
        )
        self.hud_canvas.grid(row=0, column=0, sticky="nsew")
        self.hud_canvas.bind("<Configure>", lambda _e: self._draw_hud())

        # ── Área de chat ──
        self.chat_box = ctk.CTkScrollableFrame(main, corner_radius=10, fg_color="#070b18", height=140)
        self.chat_box.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 5))
        self.chat_box.grid_columnconfigure(0, weight=1)

        # ── Barra de estado ──
        self.status_label = ctk.CTkLabel(
            main, text="Listo", font=ctk.CTkFont(size=12),
            text_color="#8b98ba"
        )
        self.status_label.grid(row=3, column=0, sticky="w", padx=15)

        # ── Panel de entrada ──
        input_frame = ctk.CTkFrame(main, height=60, corner_radius=0, fg_color="#0b1022")
        input_frame.grid(row=4, column=0, sticky="ew", padx=0, pady=0)
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
        w = max(500, canvas.winfo_width())
        h = max(320, canvas.winfo_height())
        cx, cy = w // 2, h // 2
        radius = int(min(w, h) * 0.34)

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

        # Fondo técnico
        for x in range(0, w, 48):
            canvas.create_line(x, 0, x, h, fill="#081128", width=1)
        for y in range(0, h, 48):
            canvas.create_line(0, y, w, y, fill="#081128", width=1)

        # Anillos principales escalados
        canvas.create_oval(cx - int(radius * 1.08), cy - int(radius * 1.08), cx + int(radius * 1.08), cy + int(radius * 1.08), outline="#12304d", width=2)
        canvas.create_oval(cx - int(radius * 0.82), cy - int(radius * 0.82), cx + int(radius * 0.82), cy + int(radius * 0.82), outline="#143a5f", width=2)
        canvas.create_oval(cx - int(radius * 0.56), cy - int(radius * 0.56), cx + int(radius * 0.56), cy + int(radius * 0.56), outline=color, width=3)

        # Segmentos exteriores tipo ecualizador radial
        bars = 54
        for i in range(bars):
            angle = (2 * math.pi * i / bars) + (self._hud_phase * 0.28)
            wave = 0.5 + 0.5 * math.sin(self._hud_phase * 2.8 + i * 0.35)
            jitter = random.uniform(0.0, 0.12)
            amp = (9 + pulse) * (wave + jitter)
            if self._hud_mode in ("idle", "wake"):
                amp *= 0.55

            r1 = int(radius * 1.15)
            r2 = r1 + amp
            x1 = cx + math.cos(angle) * r1
            y1 = cy + math.sin(angle) * r1
            x2 = cx + math.cos(angle) * r2
            y2 = cy + math.sin(angle) * r2
            canvas.create_line(x1, y1, x2, y2, fill=color, width=2)

        # Arco de progreso animado
        extent = 70 + 40 * math.sin(self._hud_phase)
        canvas.create_arc(
            cx - int(radius * 1.35),
            cy - int(radius * 1.35),
            cx + int(radius * 1.35),
            cy + int(radius * 1.35),
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
        canvas.create_text(cx, cy - 10, text=ASSISTANT_NAME, fill="#b7c7e8", font=("Segoe UI", 18, "bold"))
        canvas.create_text(cx, cy + 20, text=label_by_mode.get(self._hud_mode, "IDLE"), fill=color, font=("Segoe UI", 13, "bold"))
        canvas.create_text(int(w * 0.15), int(h * 0.16), text="HI-TECH INTERFACE", fill="#1ed7ff", font=("Segoe UI", 15))
        canvas.create_text(int(w * 0.84), int(h * 0.18), text="43%", fill="#28d7ff", font=("Segoe UI", 24))
        canvas.create_text(int(w * 0.12), int(h * 0.84), text="71%", fill="#28d7ff", font=("Segoe UI", 24))

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
