"""
Laptop Control Assistant — Modern Dark UI
Run:  python app.py
"""
import tkinter as tk
from tkinter import ttk
import threading
import time
import main as engine  # import the backend

# ═══════════════════════════════════════════════════════
#  COLORS & THEME
# ═══════════════════════════════════════════════════════
BG          = "#1a1a2e"
BG_DARK     = "#16213e"
BG_CARD     = "#0f3460"
BG_INPUT    = "#1f2940"
ACCENT      = "#e94560"
ACCENT_HOVER= "#ff6b81"
TEXT        = "#eaeaea"
TEXT_DIM    = "#8899aa"
TEXT_USER   = "#53d8fb"
TEXT_BOT    = "#a8e6cf"
TEXT_ERR    = "#ff6b6b"
BORDER      = "#2a3a5c"
SUCCESS     = "#00d26a"

FONT        = ("Segoe UI", 11)
FONT_BOLD   = ("Segoe UI", 11, "bold")
FONT_TITLE  = ("Segoe UI", 16, "bold")
FONT_SMALL  = ("Segoe UI", 9)
FONT_CHAT   = ("Consolas", 11)
FONT_BTN    = ("Segoe UI", 9, "bold")


class LaptopAssistantApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Laptop Control Assistant")
        self.root.geometry("900x650")
        self.root.minsize(700, 500)
        self.root.configure(bg=BG)

        # Try to set icon (ignore if fails)
        try:
            self.root.iconbitmap(default="")
        except:
            pass

        self.model_loaded = False
        self._build_ui()
        self._add_welcome()

        # Load model in background
        threading.Thread(target=self._load_model_bg, daemon=True).start()

    # ───────────────────────────────────────────────
    #  BUILD UI
    # ───────────────────────────────────────────────
    def _build_ui(self):
        # ── Title bar ──
        title_frame = tk.Frame(self.root, bg=BG_DARK, height=50)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)

        tk.Label(title_frame, text="⚡", font=("Segoe UI", 20), bg=BG_DARK, fg=ACCENT).pack(side=tk.LEFT, padx=(15, 5))
        tk.Label(title_frame, text="Laptop Control Assistant", font=FONT_TITLE, bg=BG_DARK, fg=TEXT).pack(side=tk.LEFT)

        self.status_label = tk.Label(title_frame, text="⏳ Loading AI model...", font=FONT_SMALL, bg=BG_DARK, fg=TEXT_DIM)
        self.status_label.pack(side=tk.RIGHT, padx=15)

        # ── Main area (chat + sidebar) ──
        main_frame = tk.Frame(self.root, bg=BG)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        # ── Sidebar (quick actions) ──
        sidebar = tk.Frame(main_frame, bg=BG_DARK, width=200)
        sidebar.pack(side=tk.RIGHT, fill=tk.Y, padx=(1, 0))
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="Quick Actions", font=FONT_BOLD, bg=BG_DARK, fg=TEXT).pack(pady=(12, 8))

        # Quick action buttons
        quick_actions = [
            ("⚡ Connectivity", None, True),
            ("Bluetooth ON",    "turn on bluetooth"),
            ("Bluetooth OFF",   "turn off bluetooth"),
            ("WiFi ON",         "turn on wifi"),
            ("WiFi OFF",        "turn off wifi"),
            ("🔊 Audio", None, True),
            ("Mute / Unmute",   "mute"),
            ("Volume 50%",      "set volume to 50"),
            ("Volume 100%",     "set volume to 100"),
            ("💡 Display", None, True),
            ("Brightness 30%",  "brightness to 30"),
            ("Brightness 70%",  "brightness to 70"),
            ("Night Light",     "turn on night light"),
            ("🖥️ System", None, True),
            ("Screenshot",      "take a screenshot"),
            ("Lock Screen",     "lock my laptop"),
            ("Open Settings",   "open settings"),
        ]

        for item in quick_actions:
            if len(item) == 3:
                # Section header
                tk.Label(sidebar, text=item[0], font=FONT_SMALL, bg=BG_DARK, fg=TEXT_DIM).pack(
                    anchor=tk.W, padx=12, pady=(8, 2))
            else:
                label, cmd = item
                btn = tk.Button(
                    sidebar, text=label, font=FONT_BTN,
                    bg=BG_CARD, fg=TEXT, activebackground=ACCENT, activeforeground="white",
                    bd=0, relief=tk.FLAT, cursor="hand2", padx=8, pady=4,
                    command=lambda c=cmd: self._send_command(c)
                )
                btn.pack(fill=tk.X, padx=10, pady=2)
                btn.bind("<Enter>", lambda e, b=btn: b.config(bg=ACCENT))
                btn.bind("<Leave>", lambda e, b=btn: b.config(bg=BG_CARD))

        # ── Chat area ──
        chat_frame = tk.Frame(main_frame, bg=BG)
        chat_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Chat display
        self.chat_display = tk.Text(
            chat_frame, wrap=tk.WORD, font=FONT_CHAT,
            bg=BG, fg=TEXT, bd=0, padx=15, pady=10,
            insertbackground=TEXT, selectbackground=ACCENT,
            state=tk.DISABLED, cursor="arrow", spacing3=4
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=(5, 0))

        # Scrollbar
        scrollbar = ttk.Scrollbar(self.chat_display, orient=tk.VERTICAL, command=self.chat_display.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.chat_display.config(yscrollcommand=scrollbar.set)

        # Chat tags
        self.chat_display.tag_config("user", foreground=TEXT_USER, font=("Consolas", 11, "bold"))
        self.chat_display.tag_config("bot", foreground=TEXT_BOT)
        self.chat_display.tag_config("action", foreground=SUCCESS)
        self.chat_display.tag_config("error", foreground=TEXT_ERR)
        self.chat_display.tag_config("dim", foreground=TEXT_DIM, font=("Consolas", 9))
        self.chat_display.tag_config("welcome", foreground=TEXT_DIM, font=("Consolas", 10))

        # ── Input area ──
        input_frame = tk.Frame(self.root, bg=BG_DARK, height=55)
        input_frame.pack(fill=tk.X, side=tk.BOTTOM)
        input_frame.pack_propagate(False)

        inner = tk.Frame(input_frame, bg=BG_DARK)
        inner.pack(fill=tk.BOTH, expand=True, padx=12, pady=10)

        self.input_var = tk.StringVar()
        self.input_entry = tk.Entry(
            inner, textvariable=self.input_var,
            font=FONT, bg=BG_INPUT, fg=TEXT, bd=0,
            insertbackground=TEXT, selectbackground=ACCENT,
            relief=tk.FLAT
        )
        self.input_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, ipady=6, padx=(5, 8))
        self.input_entry.bind("<Return>", lambda e: self._on_send())

        self.send_btn = tk.Button(
            inner, text="  Send ▶  ", font=FONT_BOLD,
            bg=ACCENT, fg="white", activebackground=ACCENT_HOVER,
            bd=0, relief=tk.FLAT, cursor="hand2", padx=15,
            command=self._on_send
        )
        self.send_btn.pack(side=tk.RIGHT)
        self.send_btn.bind("<Enter>", lambda e: self.send_btn.config(bg=ACCENT_HOVER))
        self.send_btn.bind("<Leave>", lambda e: self.send_btn.config(bg=ACCENT))

        # Focus input
        self.input_entry.focus_set()

    # ───────────────────────────────────────────────
    #  WELCOME MESSAGE
    # ───────────────────────────────────────────────
    def _add_welcome(self):
        self._append_chat("  ⚡ Laptop Control Assistant\n", "user")
        self._append_chat(
            "  Type commands in plain English to control your laptop.\n"
            "  Use the quick action buttons on the right, or type things like:\n\n"
            '    "turn on bluetooth"      "turn off wifi"\n'
            '    "set volume to 70"       "mute the sound"\n'
            '    "brightness to 50"       "open chrome"\n'
            '    "search for python tips" "take a screenshot"\n'
            '    "lock my computer"       "open youtube.com"\n\n',
            "welcome"
        )

    # ───────────────────────────────────────────────
    #  MODEL LOADING
    # ───────────────────────────────────────────────
    def _load_model_bg(self):
        try:
            engine.load_model()
            self.model_loaded = True
            self.root.after(0, lambda: self.status_label.config(text="✅ AI model ready", fg=SUCCESS))
        except Exception as e:
            self.root.after(0, lambda: self.status_label.config(text=f"⚠️ Model error: {e}", fg=TEXT_ERR))

    # ───────────────────────────────────────────────
    #  SEND COMMAND
    # ───────────────────────────────────────────────
    def _on_send(self):
        text = self.input_var.get().strip()
        if not text:
            return
        self._send_command(text)

    def _send_command(self, text):
        self.input_var.set("")
        self._append_chat(f"  You ▶  {text}\n", "user")
        self.input_entry.config(state=tk.DISABLED)
        self.send_btn.config(state=tk.DISABLED, text="  ⏳...  ")
        self.status_label.config(text="⏳ Processing...", fg=TEXT_DIM)

        # Run in background thread
        threading.Thread(target=self._execute_bg, args=(text,), daemon=True).start()

    def _execute_bg(self, text):
        try:
            responses = engine.process_command(text)
            self.root.after(0, lambda: self._show_responses(responses))
        except Exception as e:
            self.root.after(0, lambda: self._show_responses([f"  ❌ Error: {e}"]))

    def _show_responses(self, responses):
        for resp in responses:
            if "->" in resp:
                self._append_chat(f"  ✅ {resp.strip()}\n", "action")
            elif "[AI" in resp or "Thinking" in resp:
                self._append_chat(f"  {resp.strip()}\n", "dim")
            elif "Error" in resp or "Unknown" in resp:
                self._append_chat(f"  {resp.strip()}\n", "error")
            else:
                self._append_chat(f"  {resp.strip()}\n", "bot")

        if not responses:
            self._append_chat("  ⚠️ No response\n", "error")

        self._append_chat("\n", "dim")
        self.input_entry.config(state=tk.NORMAL)
        self.send_btn.config(state=tk.NORMAL, text="  Send ▶  ")
        self.status_label.config(text="✅ AI model ready" if self.model_loaded else "⏳ Loading AI model...",
                                  fg=SUCCESS if self.model_loaded else TEXT_DIM)
        self.input_entry.focus_set()

    # ───────────────────────────────────────────────
    #  CHAT DISPLAY
    # ───────────────────────────────────────────────
    def _append_chat(self, text, tag=None):
        self.chat_display.config(state=tk.NORMAL)
        if tag:
            self.chat_display.insert(tk.END, text, tag)
        else:
            self.chat_display.insert(tk.END, text)
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)


# ═══════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════
if __name__ == "__main__":
    root = tk.Tk()

    # Style the scrollbar
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Vertical.TScrollbar",
                    background=BG_CARD, troughcolor=BG,
                    bordercolor=BG, arrowcolor=TEXT_DIM)

    app = LaptopAssistantApp(root)
    root.mainloop()
