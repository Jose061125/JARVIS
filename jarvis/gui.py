"""
Interfaz gráfica principal de ECHONEX usando customtkinter.
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

        self.left_panel = ctk.CTkFrame(self.welcome_frame, fg_color="#06102a", corner_radius=24, border_width=1, border_color="#22457f")
        self.left_panel.place(relx=0.11, rely=0.5, relwidth=0.19, relheight=0.92, anchor="center")
        self.left_panel.bind("<Enter>", lambda _e: self._set_panel_hover(self.left_panel, True))
        self.left_panel.bind("<Leave>", lambda _e: self._set_panel_hover(self.left_panel, False))

        self.logo_canvas = tk.Canvas(self.left_panel, width=132, height=132, bg="#071333", highlightthickness=0, bd=0)
        self.logo_canvas.place(relx=0.5, rely=0.11, anchor="center")

        ctk.CTkLabel(
            self.left_panel,
            text=ASSISTANT_NAME,
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#2ee6a6",
        ).place(relx=0.5, rely=0.24, anchor="center")

        menu_items = [
            ("⌂", "Inicio"),
            ("◉", "Voz"),
            ("⊞", "Comandos"),
            ("◎", "Navegador"),
            ("⚙", "Configuracion"),
            ("i", "Acerca de"),
        ]
        for idx, (icon, item) in enumerate(menu_items):
            y = 0.30 + idx * 0.087
            active = idx == 0
            ctk.CTkButton(
                self.left_panel,
                text=f"{icon}   {item}",
                width=168,
                height=40,
                corner_radius=19,
                fg_color="#2f4ec6" if active else "#0f214a",
                hover_color="#3c64dd" if active else "#193466",
                text_color="#eef4ff" if active else "#abc1ee",
                font=ctk.CTkFont(size=14, weight="bold" if active else "normal"),
                command=lambda: None,
            ).place(relx=0.5, rely=y, anchor="center")

        ctk.CTkFrame(self.left_panel, width=168, height=1, fg_color="#254b86").place(relx=0.5, rely=0.85, anchor="center")

        ctk.CTkLabel(
            self.left_panel,
            text="SISTEMA ACTIVO",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#4ee39a",
        ).place(relx=0.5, rely=0.90, anchor="center")

        ctk.CTkLabel(
            self.left_panel,
            text="● Conectado",
            font=ctk.CTkFont(size=11),
            text_color="#73f0ba",
        ).place(relx=0.5, rely=0.94, anchor="center")

        self.welcome_card = ctk.CTkFrame(self.welcome_frame, fg_color="#0a142a", corner_radius=22, border_width=1, border_color="#1c3e73")
        self.welcome_card.place(relx=0.5, rely=0.5, relwidth=0.50, relheight=0.84, anchor="center")

        ctk.CTkLabel(
            self.welcome_card,
            text="ENTERPRISE AI CORE",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#4fb8ff",
        ).place(relx=0.5, rely=0.08, anchor="center")

        self.welcome_title_label = ctk.CTkLabel(
            self.welcome_card,
            text=f"{ASSISTANT_NAME}",
            font=ctk.CTkFont(size=68, weight="bold"),
            text_color="#2ee6a6",
        )
        self.welcome_title_label.place(relx=0.5, rely=0.19, anchor="center")

        self.welcome_title_glow = ctk.CTkLabel(
            self.welcome_card,
            text=f"{ASSISTANT_NAME}",
            font=ctk.CTkFont(size=68, weight="bold"),
            text_color="#4a4ad9",
        )
        self.welcome_title_glow.place(relx=0.5, rely=0.193, anchor="center")
        self.welcome_title_glow.lower(self.welcome_title_label)

        ctk.CTkLabel(
            self.welcome_card,
            text="Asistente inteligente para tu PC",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#90a3cf",
        ).place(relx=0.5, rely=0.29, anchor="center")

        subtitle_row = ctk.CTkFrame(self.welcome_card, fg_color="transparent")
        subtitle_row.place(relx=0.5, rely=0.35, anchor="center")

        ctk.CTkLabel(
            subtitle_row,
            text="✦",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#d24dff",
        ).pack(side="left", padx=(0, 8))

        ctk.CTkLabel(
            subtitle_row,
            text="Voz, comandos del sistema y navegador en tiempo real",
            font=ctk.CTkFont(size=16),
            text_color="#67e6ff",
        ).pack(side="left")

        self.center_orb_canvas = tk.Canvas(self.welcome_card, width=420, height=320, bg="#0a142a", highlightthickness=0, bd=0)
        self.center_orb_canvas.place(relx=0.5, rely=0.58, anchor="center")

        self.wave_canvas = tk.Canvas(self.welcome_card, width=420, height=100, bg="#0a142a", highlightthickness=0, bd=0)
        self.wave_canvas.place(relx=0.5, rely=0.68, anchor="center")

        ctk.CTkLabel(
            self.welcome_card,
            text="Presiona el microfono para hablar",
            font=ctk.CTkFont(size=14),
            text_color="#9ba8c7",
        ).place(relx=0.5, rely=0.93, anchor="center")

        self.start_btn = ctk.CTkButton(
            self.welcome_card,
            text=f"🤖  Iniciar {ASSISTANT_NAME}",
            width=280,
            height=56,
            corner_radius=28,
            fg_color="#7a2dff",
            hover_color="#1ca4ff",
            font=ctk.CTkFont(size=24, weight="bold"),
            command=self._start_jarvis,
        )
        self.start_btn.place(relx=0.5, rely=0.84, anchor="center")

        self.right_panel = ctk.CTkFrame(self.welcome_frame, fg_color="#06102a", corner_radius=18, border_width=1, border_color="#1a315a")
        self.right_panel.place(relx=0.89, rely=0.5, relwidth=0.20, relheight=0.90, anchor="center")
        self.right_panel.bind("<Enter>", lambda _e: self._set_panel_hover(self.right_panel, True))
        self.right_panel.bind("<Leave>", lambda _e: self._set_panel_hover(self.right_panel, False))

        info_cards = [
            {
                "title": "Estado del sistema",
                "icon": "◉",
                "status": "ONLINE",
                "desc": "Todos los nucleos funcionando correctamente.",
                "metrics": ["CPU", "RAM", "VOICE"],
            },
            {
                "title": "Capacidades activas",
                "icon": "✦",
                "status": "ACTIVE",
                "desc": "Modulos inteligentes ejecutandose en tiempo real.",
                "metrics": ["NLP", "AUTOMATION", "WEB CONTROL"],
            },
            {
                "title": "Acceso rapido",
                "icon": "⬢",
                "status": "READY",
                "desc": "Herramientas inteligentes disponibles.",
                "metrics": ["SEARCH", "COMMANDS", "ANALYTICS"],
            },
        ]

        for idx, card_data in enumerate(info_cards):
            y = 0.16 + idx * 0.24
            card = ctk.CTkFrame(self.right_panel, fg_color="#0c1a3d", corner_radius=22, border_width=1, border_color="#1e4a89")
            card.place(relx=0.5, rely=y, relwidth=0.90, relheight=0.20, anchor="center")

            top_row = ctk.CTkFrame(card, fg_color="transparent")
            top_row.pack(fill="x", padx=10, pady=(9, 4))

            icon_box = ctk.CTkFrame(top_row, width=34, height=34, fg_color="#153463", corner_radius=12, border_width=1, border_color="#2b67a9")
            icon_box.pack(side="left", padx=(0, 8))
            ctk.CTkLabel(icon_box, text=card_data["icon"], font=ctk.CTkFont(size=16, weight="bold"), text_color="#67e6ff").place(relx=0.5, rely=0.5, anchor="center")

            ctk.CTkLabel(top_row, text=card_data["title"], font=ctk.CTkFont(size=14, weight="bold"), text_color="#67e6ff").pack(side="left")
            ctk.CTkLabel(top_row, text=f"● {card_data['status']}", font=ctk.CTkFont(size=10, weight="bold"), text_color="#59f0c5").pack(side="right")

            ctk.CTkLabel(card, text=card_data["desc"], font=ctk.CTkFont(size=11), text_color="#c0cdef", wraplength=230, justify="left").pack(anchor="w", padx=12, pady=(0, 6))

            chip_holder = ctk.CTkFrame(card, fg_color="transparent")
            chip_holder.pack(anchor="w", padx=12, pady=(0, 8))
            for metric in card_data["metrics"]:
                chip = ctk.CTkFrame(chip_holder, width=max(54, 12 + len(metric) * 6), height=22, fg_color="#13366a", corner_radius=9, border_width=1, border_color="#2a5a9c")
                chip.pack(side="left", padx=(0, 6))
                ctk.CTkLabel(chip, text=metric, font=ctk.CTkFont(size=9), text_color="#70e7ff").place(relx=0.5, rely=0.5, anchor="center")

        quote = ctk.CTkFrame(self.right_panel, fg_color="#10204c", corner_radius=16, border_width=1, border_color="#2a5dab")
        quote.place(relx=0.5, rely=0.90, relwidth=0.90, relheight=0.12, anchor="center")
        ctk.CTkLabel(
            quote,
            text="Escucha. Entiende. Conecta.",
            font=ctk.CTkFont(size=14, slant="italic"),
            text_color="#d4def7",
        ).place(relx=0.5, rely=0.35, anchor="center")
        ctk.CTkLabel(
            quote,
            text=f"- {ASSISTANT_NAME}",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#6ce7ff",
        ).place(relx=0.88, rely=0.74, anchor="e")

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
        cx, cy = 66, 66
        r = int(45 + 5 * math.sin(phase * 2.4))

        c.create_oval(cx - (r + 12), cy - (r + 12), cx + (r + 12), cy + (r + 12), outline="#173a63", width=2)
        c.create_oval(cx - r, cy - r, cx + r, cy + r, outline="#49d8ff", width=2)
        c.create_arc(cx - (r + 16), cy - (r + 16), cx + (r + 16), cy + (r + 16), start=(phase * 55) % 360, extent=220, style=tk.ARC, outline="#b665ff", width=2)
        c.create_text(cx, cy, text=ASSISTANT_NAME[:1].upper(), fill="#78e2ff", font=("Segoe UI", 34, "bold"))

    def _set_panel_hover(self, panel: ctk.CTkFrame, active: bool):
        if active:
            panel.configure(border_color="#49b9ff", fg_color="#08173a")
        else:
            panel.configure(border_color="#1a315a", fg_color="#06102a")

    def _draw_welcome_wave(self):
        if not getattr(self, "wave_canvas", None):
            return
        c = self.wave_canvas
        c.delete("all")
        phase = self._welcome_phase
        bars = 17
        center_x = 180
        base_y = 58
        gap = 18

        for i in range(bars):
            rel = i - (bars // 2)
            x = center_x + rel * gap
            env = 1.0 - (abs(rel) / (bars // 2 + 1))
            h = int(18 + 52 * env * (0.45 + 0.55 * abs(math.sin(phase * 2.8 + i * 0.9))))
            color = "#d24dff" if i % 2 == 0 else "#3ae4ff"
            c.create_line(x, base_y, x, base_y - h, fill=color, width=6)

    def _draw_center_orb(self):
        if not getattr(self, "center_orb_canvas", None):
            return
        c = self.center_orb_canvas
        c.delete("all")
        phase = self._welcome_phase
        w = int(c.winfo_width() or 420)
        h = int(c.winfo_height() or 320)
        cx, cy = w // 2, h // 2

        core_r = int(72 + 6 * math.sin(phase * 2.1))
        outer_r = int(146 + 10 * math.sin(phase * 1.4))

        # Halo suave multicapa
        for i in range(5):
            halo_r = outer_r + 24 + i * 10
            halo_color = ["#10284f", "#0f2b57", "#0e2a4f", "#0d2645", "#0b203a"][i]
            c.create_oval(cx - halo_r, cy - halo_r, cx + halo_r, cy + halo_r, outline=halo_color, width=2)

        # Glow exterior
        c.create_oval(cx - (outer_r + 18), cy - (outer_r + 18), cx + (outer_r + 18), cy + (outer_r + 18), outline="#112b52", width=2)
        c.create_oval(cx - outer_r, cy - outer_r, cx + outer_r, cy + outer_r, outline="#35dbff", width=2)

        # Dos anillos grandes contra-rotando (estilo framer)
        c.create_arc(cx - int(outer_r * 1.04), cy - int(outer_r * 1.04), cx + int(outer_r * 1.04), cy + int(outer_r * 1.04),
                 start=(phase * 35) % 360, extent=250, style=tk.ARC, outline="#5de6ff", width=3)
        c.create_arc(cx - int(outer_r * 0.86), cy - int(outer_r * 0.86), cx + int(outer_r * 0.86), cy + int(outer_r * 0.86),
                 start=(phase * -52) % 360, extent=210, style=tk.ARC, outline="#cf63ff", width=3)

        # Arcos rotatorios
        c.create_arc(cx - (outer_r + 6), cy - (outer_r + 6), cx + (outer_r + 6), cy + (outer_r + 6),
                     start=(phase * 50) % 360, extent=220, style=tk.ARC, outline="#b053ff", width=3)
        c.create_arc(cx - (outer_r - 16), cy - (outer_r - 16), cx + (outer_r - 16), cy + (outer_r - 16),
                     start=(phase * -70) % 360, extent=170, style=tk.ARC, outline="#44e7ff", width=3)

        # Segmentos brillantes tipo HUD
        for i in range(14):
            a0 = (phase * 22 + i * 24) % 360
            ext = 10 + (i % 3) * 4
            col = "#5ceaff" if i % 2 == 0 else "#d06bff"
            c.create_arc(
                cx - (outer_r - 4),
                cy - (outer_r - 4),
                cx + (outer_r - 4),
                cy + (outer_r - 4),
                start=a0,
                extent=ext,
                style=tk.ARC,
                outline=col,
                width=2,
            )

        # Nube de particulas dinamicas alrededor
        for i in range(26):
            a = phase * 0.7 + i * (2 * math.pi / 26)
            pr = outer_r + 16 + 10 * math.sin(phase * 2.2 + i)
            px = cx + int(math.cos(a) * pr)
            py = cy + int(math.sin(a) * pr)
            col = "#5be9ff" if i % 2 == 0 else "#c56bff"
            c.create_oval(px - 2, py - 2, px + 2, py + 2, outline=col, fill=col)

        # Particulas internas flotantes
        for i in range(20):
            a = (i * 0.9) + phase * (1.0 + i * 0.02)
            pr = int(core_r * 1.15 * (0.35 + 0.65 * ((i % 5) / 4)))
            px = cx + int(math.cos(a) * pr)
            py = cy + int(math.sin(a * 1.2) * pr * 0.75)
            col = "#8cf1ff" if i % 2 == 0 else "#f39bff"
            c.create_oval(px - 1, py - 1, px + 1, py + 1, outline=col, fill=col)

        # Núcleo
        c.create_oval(cx - int(core_r * 1.45), cy - int(core_r * 1.45), cx + int(core_r * 1.45), cy + int(core_r * 1.45), outline="#1f4b7f", width=2)
        c.create_oval(cx - core_r, cy - core_r, cx + core_r, cy + core_r, outline="#56e6ff", width=3)

        # Degradado por capas del nucleo
        grad_layers = [
            (0.86, "#223c7f"),
            (0.74, "#2a3ea1"),
            (0.62, "#3c3ea8"),
            (0.50, "#5343ad"),
            (0.38, "#4b6bc8"),
            (0.26, "#2ea9d6"),
        ]
        for ratio, col in grad_layers:
            rr = int(core_r * ratio)
            c.create_oval(cx - rr, cy - rr, cx + rr, cy + rr, outline=col, fill=col)

        c.create_oval(cx - int(core_r * 0.14), cy - int(core_r * 0.14), cx + int(core_r * 0.14), cy + int(core_r * 0.14), outline="#91f0ff", fill="#91f0ff")

        # Letra central
        c.create_text(cx, cy + 1, text=ASSISTANT_NAME[:1].upper(), fill="#2a1d4f", font=("Segoe UI", 52, "bold"))
        c.create_text(cx, cy, text=ASSISTANT_NAME[:1].upper(), fill="#baf6ff", font=("Segoe UI", 52, "bold"))

    def _animate_welcome(self):
        if not self._welcome_active:
            return
        self._welcome_phase += 0.08
        self._draw_welcome_background()
        self._draw_logo_orb()
        self._draw_center_orb()
        self._draw_welcome_wave()

        # Pulso neon para el titulo principal
        if getattr(self, "welcome_title_label", None):
            glow = 0.5 + 0.5 * math.sin(self._welcome_phase * 2.0)
            r = int(90 + 80 * glow)
            g = int(90 + 130 * glow)
            b = 255
            self.welcome_title_label.configure(text_color=f"#{r:02x}{g:02x}{b:02x}")
            self.welcome_title_glow.configure(text_color=f"#{max(20, r-55):02x}3cff")

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
        self._add_message(ASSISTANT_NAME, f"Hola, soy {ASSISTANT_NAME}. ¿En qué puedo ayudarte?", is_bot=True)

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
