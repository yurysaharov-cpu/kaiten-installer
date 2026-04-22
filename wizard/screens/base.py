import customtkinter as ctk

TOTAL = 9
HEADER_COLOR = "#1565C0"


class BaseScreen(ctk.CTkFrame):
    step: int = 0
    heading: str = ""

    def __init__(self, app):
        super().__init__(app, fg_color="#ffffff", corner_radius=0)
        self.app = app
        self._err_label = None
        self._build_header()
        # footer пакуется с side="bottom" ДО body — иначе body вытесняет его за экран
        self._build_footer()
        # фиксированная зона для ошибок (между body и footer, всегда видна)
        self._err_bar = ctk.CTkFrame(self, fg_color="#FFF3F3", height=0, corner_radius=0)
        self._err_bar.pack(fill="x", side="bottom")
        self._err_bar.pack_propagate(False)
        self._err_label = ctk.CTkLabel(
            self._err_bar, text="",
            font=ctk.CTkFont("Helvetica Neue", 12),
            text_color="#C62828", anchor="w",
        )
        self._err_label.pack(anchor="w", padx=22, pady=6)
        self._body = ctk.CTkScrollableFrame(self, fg_color="#ffffff", corner_radius=0)
        self._body.pack(fill="both", expand=True, padx=30, pady=10)
        self.build()

    def _build_header(self):
        bar = ctk.CTkFrame(self, fg_color=HEADER_COLOR, height=62, corner_radius=0)
        bar.pack(fill="x")
        bar.pack_propagate(False)
        ctk.CTkLabel(
            bar, text=self.heading,
            font=ctk.CTkFont("Helvetica Neue", 17, "bold"),
            text_color="white", anchor="w",
        ).pack(side="left", padx=22, pady=18)
        ctk.CTkLabel(
            bar, text=f"Шаг {self.step} из {TOTAL}",
            font=ctk.CTkFont("Helvetica Neue", 12),
            text_color="#90CAF9",
        ).pack(side="right", padx=22)

    def _build_footer(self):
        bar = ctk.CTkFrame(self, fg_color="#F5F5F5", height=58, corner_radius=0)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)

        btns = ctk.CTkFrame(bar, fg_color="transparent")
        btns.pack(side="right", padx=22, pady=12)

        if self.step > 1:
            ctk.CTkButton(
                btns, text="← Назад", width=100,
                fg_color="#E0E0E0", hover_color="#BDBDBD",
                text_color="#212121", corner_radius=6,
                command=self.app.back,
            ).pack(side="left", padx=(0, 8))

        self._btn_next = ctk.CTkButton(
            btns,
            text="Закрыть" if self.step == TOTAL else "Далее →",
            width=120, corner_radius=6,
            command=self.on_next,
        )
        self._btn_next.pack(side="left")

    def build(self):
        pass

    def on_next(self):
        self.app.next()

    # ── helpers ──────────────────────────────────────────────────────────────

    def section(self, text):
        ctk.CTkLabel(
            self._body, text=text,
            font=ctk.CTkFont("Helvetica Neue", 13, "bold"),
            text_color="#1565C0", anchor="w",
        ).pack(anchor="w", pady=(14, 2))

    def field(self, label, required=False, placeholder="", show="", default=""):
        lbl = ("* " if required else "") + label
        ctk.CTkLabel(
            self._body, text=lbl,
            font=ctk.CTkFont("Helvetica Neue", 12),
            text_color="#424242", anchor="w",
        ).pack(anchor="w", pady=(6, 1))
        e = ctk.CTkEntry(
            self._body, placeholder_text=placeholder,
            show=show, height=36, corner_radius=6,
            font=ctk.CTkFont("Helvetica Neue", 13),
        )
        if default:
            e.insert(0, default)
        e.pack(fill="x")
        return e

    def note(self, text, color="#757575"):
        ctk.CTkLabel(
            self._body, text=text,
            font=ctk.CTkFont("Helvetica Neue", 11),
            text_color=color, anchor="w", wraplength=580,
        ).pack(anchor="w", pady=(2, 0))

    def error(self, text):
        self._err_label.configure(text=text)
        self._err_bar.configure(height=34 if text else 0)
