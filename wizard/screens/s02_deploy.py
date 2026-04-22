import threading
import customtkinter as ctk
from wizard.screens.base import BaseScreen


class DeployScreen(BaseScreen):
    step = 2
    heading = "Где развернуть сервис?"

    def build(self):
        self._target = ctk.StringVar(value="local")

        ctk.CTkRadioButton(
            self._body,
            text="Локально (Docker Desktop на этом Mac)",
            variable=self._target, value="local",
            command=self._on_toggle,
            font=ctk.CTkFont("Helvetica Neue", 13),
        ).pack(anchor="w", pady=(16, 2))
        self.note("Docker Desktop должен быть запущен во время установки.")

        ctk.CTkRadioButton(
            self._body,
            text="На VPS (через SSH)",
            variable=self._target, value="vps",
            command=self._on_toggle,
            font=ctk.CTkFont("Helvetica Neue", 13),
        ).pack(anchor="w", pady=(14, 2))

        self._vps_frame = ctk.CTkFrame(self._body, fg_color="#F8F9FA", corner_radius=8)

        self._host_e = self._vfield(self._vps_frame, "Хост / IP", required=True,
                                    placeholder="111.88.213.65")
        self._port_e = self._vfield(self._vps_frame, "Порт SSH", default="22")
        self._user_e = self._vfield(self._vps_frame, "Логин", required=True, placeholder="root")
        self._pass_e = self._vfield(self._vps_frame, "Пароль", required=True, show="●")
        self._path_e = self._vfield(self._vps_frame, "Путь на VPS",
                                    default="/opt/kaiten-watcher")

        self._test_btn = ctk.CTkButton(
            self._vps_frame, text="Проверить соединение",
            width=190, height=34, corner_radius=6,
            command=self._test_ssh,
        )
        self._test_btn.pack(anchor="w", padx=16, pady=(10, 4))

        self._test_lbl = ctk.CTkLabel(
            self._vps_frame, text="",
            font=ctk.CTkFont("Helvetica Neue", 12), anchor="w",
        )
        self._test_lbl.pack(anchor="w", padx=16, pady=(0, 12))

        self._on_toggle()

    def _vfield(self, parent, label, required=False, placeholder="", show="", default=""):
        lbl = ("* " if required else "") + label
        ctk.CTkLabel(
            parent, text=lbl,
            font=ctk.CTkFont("Helvetica Neue", 12),
            text_color="#424242", anchor="w",
        ).pack(anchor="w", padx=16, pady=(8, 1))
        e = ctk.CTkEntry(
            parent, placeholder_text=placeholder,
            show=show, height=34, corner_radius=6,
            font=ctk.CTkFont("Helvetica Neue", 13),
        )
        if default:
            e.insert(0, default)
        e.pack(fill="x", padx=16)
        return e

    def _on_toggle(self):
        if self._target.get() == "vps":
            self._vps_frame.pack(fill="x", pady=(10, 4))
        else:
            self._vps_frame.pack_forget()

    def _test_ssh(self):
        self._test_lbl.configure(text="Проверяю...", text_color="#1565C0")
        self._test_btn.configure(state="disabled")

        def run():
            try:
                import paramiko
                c = paramiko.SSHClient()
                c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                c.connect(
                    self._host_e.get().strip(),
                    port=int(self._port_e.get().strip() or 22),
                    username=self._user_e.get().strip(),
                    password=self._pass_e.get(),
                    timeout=10,
                )
                c.close()
                self._test_lbl.configure(text="✓ Соединение успешно", text_color="#2E7D32")
            except Exception as ex:
                self._test_lbl.configure(text=f"✗ Ошибка: {ex}", text_color="#C62828")
            finally:
                self._test_btn.configure(state="normal")

        threading.Thread(target=run, daemon=True).start()

    def on_next(self):
        target = self._target.get()
        self.app.cfg["deploy_target"] = target

        if target == "vps":
            host = self._host_e.get().strip()
            user = self._user_e.get().strip()
            pwd = self._pass_e.get()
            if not host or not user or not pwd:
                self._test_lbl.configure(
                    text="✗ Заполните обязательные поля (хост, логин, пароль)",
                    text_color="#C62828",
                )
                return
            self.app.cfg["vps_host"] = host
            self.app.cfg["vps_port"] = int(self._port_e.get().strip() or 22)
            self.app.cfg["vps_user"] = user
            self.app.cfg["vps_pass"] = pwd
            self.app.cfg["vps_path"] = self._path_e.get().strip() or "/opt/kaiten-watcher"

        self.app.next()
