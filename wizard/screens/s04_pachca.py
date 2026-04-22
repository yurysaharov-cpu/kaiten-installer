from wizard.screens.base import BaseScreen


class PachcaScreen(BaseScreen):
    step = 4
    heading = "Настройки Пачки"

    def build(self):
        self.note("* — обязательные поля", color="#C62828")
        self._token = self.field("API-токен Пачки", required=True,
                                  placeholder="ваш токен", show="●")
        self._base_url = self.field("Base URL", required=True,
                                     default="https://api.pachca.com/api/shared/v1")
        self._chat_id = self.field("Chat ID", required=True, placeholder="12345678")
        self.note("ID группового чата для уведомлений о новых карточках и оценках.")

    def on_next(self):
        mapping = [
            ("PACHCA_TOKEN", self._token),
            ("PACHCA_BASE_URL", self._base_url),
            ("PACHCA_CHAT_ID", self._chat_id),
        ]
        for key, widget in mapping:
            v = widget.get().strip()
            if not v:
                self.error(f"Заполните поле: {key}")
                return
            self.app.cfg[key] = v
        self.app.next()
