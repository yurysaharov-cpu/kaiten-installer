import customtkinter as ctk
from wizard.screens.base import BaseScreen


class AnthropicScreen(BaseScreen):
    step = 5
    heading = "Anthropic API"

    def build(self):
        self.note("* — обязательные поля", color="#C62828")
        self._key = self.field("API Key", required=True,
                                placeholder="sk-ant-...", show="●")
        self.note("Используется Claude Haiku для проверки оформления и оценки карточек.")

        self._show_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            self._body, text="Показать ключ",
            variable=self._show_var, command=self._toggle,
            font=ctk.CTkFont("Helvetica Neue", 12),
        ).pack(anchor="w", pady=(6, 0))

    def _toggle(self):
        self._key.configure(show="" if self._show_var.get() else "●")

    def on_next(self):
        v = self._key.get().strip()
        if not v:
            self.error("Заполните API Key")
            return
        self.app.cfg["ANTHROPIC_API_KEY"] = v
        self.app.next()
