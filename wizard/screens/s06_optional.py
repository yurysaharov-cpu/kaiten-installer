import customtkinter as ctk
from tkinter import filedialog
from wizard.screens.base import BaseScreen

_FIELD_DEFAULTS = {
    "O": "577171", "P": "577170", "Q": "577172", "R": "577173",
    "T": "577177", "U": "577178", "V": "577179", "W": "577180",
}
_FIELD_LABELS = {
    "O": "O — Влияние на стабильность",
    "P": "P — Снижение расходов",
    "Q": "Q — Качество работы с клиентами",
    "R": "R — Скорость процессов",
    "T": "T — Уверенность в обосновании",
    "U": "U — Трудозатраты",
    "V": "V — Техническая сложность",
    "W": "W — Обязательность",
}


class OptionalScreen(BaseScreen):
    step = 6
    heading = "Дополнительные настройки"

    def build(self):
        self.note("Все поля необязательны — предзаполнены значениями по умолчанию.")

        self.section("Мониторинг")
        self._poll = self.field("Интервал опроса Kaiten, сек", default="600")

        self.section("Уведомления об инцидентах")
        self._inc_prop = self.field("Incident Property ID", default="576936")
        self._inc_opt = self.field("Incident Option ID", default="16305587")

        self.section("Google Sheet (запись оценок)")
        self._sheet_id = self.field(
            "Spreadsheet ID",
            placeholder="1dveK32toe4VExo32ZDaa3DpyFYhHmo37DhUknAOA42o",
        )
        self._sheet_gid = self.field("Sheet GID (номер вкладки)", default="771213470")

        ctk.CTkLabel(
            self._body, text="Service Account JSON",
            font=ctk.CTkFont("Helvetica Neue", 12),
            text_color="#424242", anchor="w",
        ).pack(anchor="w", pady=(6, 1))
        row = ctk.CTkFrame(self._body, fg_color="transparent")
        row.pack(fill="x")
        self._sa_path = ctk.CTkEntry(
            row, placeholder_text="путь к service_account.json", height=36,
        )
        self._sa_path.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(
            row, text="Выбрать", width=80, height=36, corner_radius=6,
            command=self._pick_sa,
        ).pack(side="left", padx=(6, 0))

        self.section("ID кастомных полей Kaiten (критерии оценки)")
        self.note("Оставьте значения по умолчанию, если не меняли структуру полей Kaiten.")
        self._criteria = {}
        for key, default in _FIELD_DEFAULTS.items():
            self._criteria[key] = self.field(_FIELD_LABELS[key], default=default)

    def _pick_sa(self):
        path = filedialog.askopenfilename(
            title="Выберите service_account.json",
            filetypes=[("JSON", "*.json")],
        )
        if path:
            self._sa_path.delete(0, "end")
            self._sa_path.insert(0, path)

    def on_next(self):
        cfg = self.app.cfg
        cfg["POLL_INTERVAL"] = self._poll.get().strip() or "600"
        cfg["INCIDENT_PROPERTY_ID"] = self._inc_prop.get().strip() or "576936"
        cfg["INCIDENT_OPTION_ID"] = self._inc_opt.get().strip() or "16305587"

        v = self._sheet_id.get().strip()
        if v:
            cfg["SPREADSHEET_ID"] = v
        cfg["SHEET_GID"] = self._sheet_gid.get().strip() or "771213470"

        sa = self._sa_path.get().strip()
        if sa:
            cfg["GOOGLE_SERVICE_ACCOUNT_FILE"] = sa

        for key, widget in self._criteria.items():
            cfg[f"KAITEN_FIELD_{key}"] = widget.get().strip() or _FIELD_DEFAULTS[key]

        self.app.next()
