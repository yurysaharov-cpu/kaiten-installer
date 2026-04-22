import threading
import customtkinter as ctk
from wizard.screens.base import BaseScreen

_CHECKS = [
    ("kaiten", "Kaiten API"),
    ("pachca", "Пачка API"),
    ("anthropic", "Anthropic API"),
]


class ValidateScreen(BaseScreen):
    step = 7
    heading = "Проверка подключений"

    def build(self):
        self.note("Проверьте все сервисы перед развёртыванием.")
        self._btn_next.configure(state="disabled")
        self._rows = {}

        for name, label in _CHECKS:
            row = ctk.CTkFrame(self._body, fg_color="#F8F9FA", corner_radius=8)
            row.pack(fill="x", pady=5)
            ctk.CTkLabel(
                row, text=label,
                font=ctk.CTkFont("Helvetica Neue", 13, "bold"),
                text_color="#212121", anchor="w", width=140,
            ).pack(side="left", padx=14, pady=12)
            lbl = ctk.CTkLabel(
                row, text="—",
                font=ctk.CTkFont("Helvetica Neue", 12),
                text_color="#757575", anchor="w",
            )
            lbl.pack(side="left", padx=8, fill="x", expand=True)
            btn = ctk.CTkButton(
                row, text="Проверить", width=110, height=30, corner_radius=6,
                command=lambda n=name: self._check(n),
            )
            btn.pack(side="right", padx=14, pady=10)
            self._rows[name] = {"lbl": lbl, "btn": btn, "ok": False}

        ctk.CTkButton(
            self._body, text="Проверить все",
            height=36, corner_radius=6, fg_color="#1565C0",
            command=self._check_all,
        ).pack(fill="x", pady=(14, 0))

    def _check(self, name):
        self._rows[name]["btn"].configure(state="disabled")
        self._rows[name]["lbl"].configure(text="Проверяю...", text_color="#1565C0")
        threading.Thread(target=self._run, args=(name,), daemon=True).start()

    def _check_all(self):
        for name, _ in _CHECKS:
            self._check(name)

    def _run(self, name):
        import httpx
        cfg = self.app.cfg
        try:
            if name == "kaiten":
                r = httpx.get(
                    f"{cfg['KAITEN_BASE_URL'].rstrip('/')}/cards",
                    headers={"Authorization": f"Bearer {cfg['KAITEN_TOKEN']}"},
                    params={"limit": 1}, timeout=10,
                )
                r.raise_for_status()
                ok, msg = True, "✓ OK"

            elif name == "pachca":
                r = httpx.get(
                    f"{cfg['PACHCA_BASE_URL'].rstrip('/')}/chats",
                    headers={"Authorization": f"Bearer {cfg['PACHCA_TOKEN']}"},
                    timeout=10,
                )
                r.raise_for_status()
                ok, msg = True, "✓ OK"

            elif name == "anthropic":
                import anthropic
                c = anthropic.Anthropic(api_key=cfg["ANTHROPIC_API_KEY"])
                c.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=5,
                    messages=[{"role": "user", "content": "ping"}],
                )
                ok, msg = True, "✓ OK"

            else:
                ok, msg = False, "Неизвестная проверка"

        except Exception as e:
            ok, msg = False, f"✗ {e}"

        self._rows[name]["ok"] = ok
        color = "#2E7D32" if ok else "#C62828"
        self._rows[name]["lbl"].configure(text=msg, text_color=color)
        self._rows[name]["btn"].configure(state="normal")
        self._refresh_next()

    def _refresh_next(self):
        if all(v["ok"] for v in self._rows.values()):
            self._btn_next.configure(state="normal")
