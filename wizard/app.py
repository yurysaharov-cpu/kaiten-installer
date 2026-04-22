import customtkinter as ctk
from pathlib import Path

INSTALL_MARKER = Path.home() / ".kaiten-watcher" / ".installed"

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class WizardApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Kaiten Watcher — Установка")
        self.geometry("660x560")
        self.resizable(False, False)

        self.cfg = {}
        self._frame = None

        from wizard.screens.s01_welcome import WelcomeScreen
        from wizard.screens.s02_deploy import DeployScreen
        from wizard.screens.s03_kaiten import KaitenScreen
        from wizard.screens.s04_pachca import PachcaScreen
        from wizard.screens.s05_anthropic import AnthropicScreen
        from wizard.screens.s06_optional import OptionalScreen
        from wizard.screens.s07_validate import ValidateScreen
        from wizard.screens.s08_progress import ProgressScreen
        from wizard.screens.s09_done import DoneScreen

        self._screens = [
            WelcomeScreen, DeployScreen, KaitenScreen, PachcaScreen,
            AnthropicScreen, OptionalScreen, ValidateScreen,
            ProgressScreen, DoneScreen,
        ]
        self._idx = 0
        self._show(0)

    def _show(self, idx):
        if self._frame:
            self._frame.destroy()
        self._idx = idx
        self._frame = self._screens[idx](self)
        self._frame.pack(fill="both", expand=True)

    def next(self):
        self._show(self._idx + 1)

    def back(self):
        self._show(self._idx - 1)

    @property
    def already_installed(self):
        return INSTALL_MARKER.exists()
