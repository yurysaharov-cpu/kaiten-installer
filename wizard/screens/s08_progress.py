import threading
import customtkinter as ctk
from wizard.screens.base import BaseScreen


class ProgressScreen(BaseScreen):
    step = 8
    heading = "Развёртывание"

    def build(self):
        self._btn_next.configure(state="disabled")
        self._log = ctk.CTkTextbox(
            self._body, height=360,
            font=ctk.CTkFont("Courier New", 12),
            state="disabled",
        )
        self._log.pack(fill="both", expand=True)
        self.after(400, self._start)

    def _append(self, text, color=None):
        # UI обновляется только из главного потока через after()
        self.after(0, self._append_main, text)

    def _append_main(self, text):
        self._log.configure(state="normal")
        self._log.insert("end", text + "\n")
        self._log.see("end")
        self._log.configure(state="disabled")

    def _start(self):
        threading.Thread(target=self._deploy, daemon=True).start()

    def _deploy(self):
        cfg = self.app.cfg
        try:
            if cfg.get("deploy_target") == "vps":
                from deployer.vps import deploy_vps
                deploy_vps(cfg, self._append)
            else:
                from deployer.local import deploy_local
                deploy_local(cfg, self._append)
            self._append("\n✓ Установка завершена успешно!")
            self.after(0, lambda: self._btn_next.configure(state="normal"))  # noqa: main thread
        except Exception as e:
            self._append(f"\n✗ Ошибка: {e}")
            self._append("Исправьте проблему и запустите installer заново.")
