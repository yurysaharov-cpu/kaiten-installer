from wizard.screens.base import BaseScreen


class KaitenScreen(BaseScreen):
    step = 3
    heading = "Настройки Kaiten"

    def build(self):
        self.note("* — обязательные поля", color="#C62828")
        self._token = self.field("API-токен Kaiten", required=True,
                                  placeholder="ваш токен", show="●")
        self._base_url = self.field("Base URL", required=True,
                                     default="https://api.kaiten.ru/api/latest")
        self._space_id = self.field("Space ID", required=True, placeholder="123456")
        self._col_ids = self.field("Column IDs (через запятую)", required=True,
                                    placeholder="111222,333444")
        self.note("ID колонок для мониторинга. Найти: открыть колонку → скопировать column_id из URL.")

    def on_next(self):
        mapping = [
            ("KAITEN_TOKEN", self._token),
            ("KAITEN_BASE_URL", self._base_url),
            ("KAITEN_SPACE_ID", self._space_id),
            ("KAITEN_COLUMN_IDS", self._col_ids),
        ]
        for key, widget in mapping:
            v = widget.get().strip()
            if not v:
                self.error(f"Заполните поле: {key}")
                return
            self.app.cfg[key] = v
        self.app.next()
