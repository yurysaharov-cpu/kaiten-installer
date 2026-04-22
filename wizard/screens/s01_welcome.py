import customtkinter as ctk
from wizard.screens.base import BaseScreen


class WelcomeScreen(BaseScreen):
    step = 1
    heading = "Kaiten Watcher"

    def build(self):
        if self.app.already_installed:
            ctk.CTkLabel(
                self._body,
                text="Уже установлено",
                font=ctk.CTkFont("Helvetica Neue", 16, "bold"),
                text_color="#E65100",
            ).pack(pady=(20, 8))
            ctk.CTkLabel(
                self._body,
                text=(
                    "Kaiten Watcher уже установлен на этом компьютере.\n"
                    "Повторная установка через этот wizard не поддерживается.\n\n"
                    "Для переустановки удалите каталог ~/.kaiten-watcher/ вручную,\n"
                    "затем запустите installer снова."
                ),
                font=ctk.CTkFont("Helvetica Neue", 13),
                text_color="#555", wraplength=560, justify="left",
            ).pack(pady=4)
            self._btn_next.configure(state="disabled")
            return

        ctk.CTkLabel(
            self._body,
            text="Автоматизация работы с Kaiten и Пачкой",
            font=ctk.CTkFont("Helvetica Neue", 15, "bold"),
            text_color="#212121",
        ).pack(anchor="w", pady=(14, 10))

        ctk.CTkLabel(
            self._body,
            text=(
                "Этот установщик развернёт сервис kaiten-watcher, который:\n\n"
                "  •  Мониторит новые карточки в заданных колонках Kaiten\n"
                "  •  Проверяет оформление карточек по шаблону\n"
                "  •  Оценивает карточки по 8 критериям с помощью Claude AI\n"
                "  •  Записывает баллы в кастомные поля Kaiten\n"
                "  •  Отправляет уведомления о новых карточках и оценках в Пачку\n\n"
                "Потребуется: Docker Desktop (для локальной установки) или VPS с Docker."
            ),
            font=ctk.CTkFont("Helvetica Neue", 13),
            text_color="#424242", anchor="w",
            justify="left", wraplength=580,
        ).pack(anchor="w")
