"""
Interfaz gráfica principal de JARVIS usando customtkinter.
"""

import threading
import customtkinter as ctk
from datetime import datetime
import time

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
        self.geometry("700x600")
        self.resizable(True, True)
        self.minsize(500, 450)

        self._is_listening = False
        self._is_processing = False
        self._wake_mode = False
        self._wake_thread: threading.Thread | None = None
        self._tts_thread: threading.Thread | None = None

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._build_ui()
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
        header = ctk.CTkFrame(main, height=60, corner_radius=0, fg_color="#1a1a2e")
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)

        ctk.CTkLabel(
            header,
            text=f"● {ASSISTANT_NAME}",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#00d4ff",
        ).pack(side="left", padx=20, pady=10)

        ctk.CTkButton(
            header,
            text="Limpiar",
            width=80,
            height=30,
            command=self._clear_chat,
            fg_color="#2d2d44",
            hover_color="#3d3d5c",
        ).pack(side="right", padx=10)

        self.wake_btn = ctk.CTkButton(
            header,
            text="Wake OFF",
            width=100,
            height=30,
            command=self._toggle_wake_mode,
            fg_color="#3a2d44",
            hover_color="#4d3a5c",
        )
        self.wake_btn.pack(side="right", padx=(0, 8))

        # ── Área de chat ──
        self.chat_box = ctk.CTkScrollableFrame(main, corner_radius=10, fg_color="#0d0d1a")
        self.chat_box.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        self.chat_box.grid_columnconfigure(0, weight=1)

        # ── Barra de estado ──
        self.status_label = ctk.CTkLabel(
            main, text="Listo", font=ctk.CTkFont(size=12),
            text_color="#888888"
        )
        self.status_label.grid(row=2, column=0, sticky="w", padx=15)

        # ── Panel de entrada ──
        input_frame = ctk.CTkFrame(main, height=60, corner_radius=0, fg_color="#111122")
        input_frame.grid(row=3, column=0, sticky="ew", padx=0, pady=0)
        input_frame.grid_columnconfigure(0, weight=1)
        input_frame.grid_propagate(False)

        self.input_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="Escribe un mensaje...",
            font=ctk.CTkFont(size=14),
            height=40,
            corner_radius=20,
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
        )
        self.send_btn.grid(row=0, column=1, padx=(0, 5), pady=10)

        self.voice_btn = ctk.CTkButton(
            input_frame,
            text="🎤",
            width=50,
            height=40,
            corner_radius=20,
            fg_color="#1a3a4a",
            hover_color="#2a5a6a",
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
        threading.Thread(target=self._listen_worker, daemon=True).start()

    def _listen_worker(self):
        text = listen()
        self._is_listening = False
        self.after(0, lambda: self.voice_btn.configure(text="🎤", fg_color="#1a3a4a"))
        if text:
            self.after(0, lambda: self._process_input(text))
        else:
            self.after(0, lambda: self._set_status("No entendí. Intenta de nuevo."))

    # ── Procesar input (texto o voz) ─────────────────────────────────────────

    def _process_input(self, user_text: str):
        if self._is_processing:
            return
        self._is_processing = True
        self._add_message("Tú", user_text, is_bot=False)
        self._set_status("Pensando...")
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
        except Exception as e:
            error_msg = f"Error: {e}"
            self.after(0, lambda: self._add_message(ASSISTANT_NAME, error_msg, is_bot=True))
            self.after(0, lambda: self._set_status("Error"))
        finally:
            self._is_processing = False
            self.after(0, lambda: self.send_btn.configure(state="normal"))

    # ── Wake word / manos libres ─────────────────────────────────────────────

    def _toggle_wake_mode(self):
        self._wake_mode = not self._wake_mode
        if self._wake_mode:
            self.wake_btn.configure(text="Wake ON", fg_color="#1a4a2d", hover_color="#2a6a3d")
            self._set_status("Wake mode activo. Di: Jarvis")
            self._add_message(ASSISTANT_NAME, "Modo manos libres activado. Di 'Jarvis' y luego tu orden.", is_bot=True)
            self._wake_thread = threading.Thread(target=self._wake_worker, daemon=True)
            self._wake_thread.start()
        else:
            self.wake_btn.configure(text="Wake OFF", fg_color="#3a2d44", hover_color="#4d3a5c")
            self._set_status("Wake mode desactivado")

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
            command_text = listen(timeout=5, phrase_limit=9)
            if command_text:
                self.after(0, lambda txt=command_text: self._process_input(txt))
            else:
                self.after(0, lambda: self._set_status("No escuché el comando tras la palabra clave."))

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
