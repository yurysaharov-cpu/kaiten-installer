import customtkinter as ctk
from wizard.screens.base import BaseScreen


class DoneScreen(BaseScreen):
    step = 9
    heading = "Установка завершена"

    def build(self):
        ctk.CTkLabel(
            self._body, text="✓",
            font=ctk.CTkFont("Helvetica Neue", 64),
            text_color="#2E7D32",
        ).pack(pady=(24, 6))

        ctk.CTkLabel(
            self._body, text="Kaiten Watcher запущен",
            font=ctk.CTkFont("Helvetica Neue", 18, "bold"),
            text_color="#212121",
        ).pack()

        ctk.CTkLabel(
            self._body,
            text="Сервис работает в фоне и автоматически перезапускается при рестарте Docker.",
            font=ctk.CTkFont("Helvetica Neue", 13),
            text_color="#555", wraplength=520,
        ).pack(pady=(8, 0))

        cfg = self.app.cfg
        if cfg.get("deploy_target") == "vps":
            loc = f"VPS {cfg.get('vps_host', '')}  {cfg.get('vps_path', '')}"
        else:
            loc = "Локальный Docker  (~/.kaiten-watcher/)"

        ctk.CTkLabel(
            self._body, text=f"Место развёртывания: {loc}",
            font=ctk.CTkFont("Helvetica Neue", 12),
            text_color="#757575",
        ).pack(pady=(10, 0))

    def on_next(self):
        self.app.destroy()
