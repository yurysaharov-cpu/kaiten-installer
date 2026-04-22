import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

import anthropic
import gspread
import httpx
from dotenv import load_dotenv
from google.oauth2 import service_account

load_dotenv(Path(__file__).parent / "config.env")

log = logging.getLogger(__name__)

KAITEN_TOKEN = os.environ["KAITEN_TOKEN"]
KAITEN_BASE = os.environ["KAITEN_BASE_URL"].rstrip("/")
SPACE_ID = os.environ["KAITEN_SPACE_ID"]

PACHCA_TOKEN = os.environ["PACHCA_TOKEN"]
PACHCA_BASE = os.environ["PACHCA_BASE_URL"].rstrip("/")
PACHCA_CHAT_ID = int(os.environ["PACHCA_CHAT_ID"])

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
GOOGLE_SERVICE_ACCOUNT_FILE = os.environ.get(
    "GOOGLE_SERVICE_ACCOUNT_FILE", "/app/service_account.json"
)

# Параметризованы через config.env — позволяют установить под любую таблицу и Kaiten-инстанс
SPREADSHEET_ID = os.environ.get(
    "SPREADSHEET_ID", "1dveK32toe4VExo32ZDaa3DpyFYhHmo37DhUknAOA42o"
)
SHEET_GID = int(os.environ.get("SHEET_GID", "771213470"))

KAITEN_FIELD_MAP = {
    "O": int(os.environ.get("KAITEN_FIELD_O", "577171")),
    "P": int(os.environ.get("KAITEN_FIELD_P", "577170")),
    "Q": int(os.environ.get("KAITEN_FIELD_Q", "577172")),
    "R": int(os.environ.get("KAITEN_FIELD_R", "577173")),
    "T": int(os.environ.get("KAITEN_FIELD_T", "577177")),
    "U": int(os.environ.get("KAITEN_FIELD_U", "577178")),
    "V": int(os.environ.get("KAITEN_FIELD_V", "577179")),
    "W": int(os.environ.get("KAITEN_FIELD_W", "577180")),
}

CRITERIA = {
    "O": {
        "name": "Влияние на операционную стабильность",
        "levels": {
            0: "Инциденты продолжатся, задача не устраняет причину",
            1: "Снижает вероятность инцидента",
            2: "Устраняет причину повторяющихся инцидентов",
            3: "Предотвращает инциденты и влияет на сокращение других",
        },
    },
    "P": {
        "name": "Снижение операционных расходов / автоматизация",
        "levels": {
            0: "Не влияет на снижение или неясно влияет ли",
            1: "До 300 тыс руб в месяц",
            2: "300 тыс — 1000 тыс руб в месяц",
            3: "От 1000 тыс руб в месяц",
        },
    },
    "Q": {
        "name": "Качество работы с клиентами. Корректность финансовых и юридических данных",
        "levels": {
            0: "Задача не влияет на такие данные",
            1: "Снижает риск ошибки, но ошибки всё ещё возможны",
            2: "Устраняет ошибку в данных или автоматизирует проверку",
            3: "Устраняет и текущую ошибку и влияет на другие ошибки",
        },
    },
    "R": {
        "name": "Скорость процессов (взаимодействие с клиентом, БО-процессы)",
        "levels": {
            0: "Не ускоряет или неясно влияет ли",
            1: "Менее 10%",
            2: "11–30%",
            3: "Более 30%",
        },
    },
    "T": {
        "name": "Уверенность в бизнес-обосновании",
        "levels": {
            0: "Гипотеза без данных",
            1: "Есть экспертная оценка",
            2: "Есть расчёты / пилот / похожие кейсы",
            3: "Эффект подтверждён данными",
        },
    },
    "U": {
        "name": "Трудозатраты (дни или эквивалент в руб., 1 день = 8 ч)",
        "levels": {
            0: "Больше 15 дней",
            1: "5–15 дней",
            2: "1–5 дней",
            3: "Меньше 1 дня",
        },
    },
    "V": {
        "name": "Техническая сложность и зависимость",
        "levels": {
            0: "Изменения в 3х и более системах, одна из них вне компании",
            1: "Изменения в 3х и более системах",
            2: "Изменения в 2х системах (одна не в команде)",
            3: "Все изменения делает команда",
        },
    },
    "W": {
        "name": "Обязательность",
        "levels": {
            0: "Необязательная инициатива",
            1: "Сильное ожидание бизнеса",
            2: "Внутреннее обязательство: решение руководства, утверждённый план, committed KPI",
            3: "Внешнее / регуляторное / договорное обязательство",
        },
    },
}

CHECKLIST_PROMPT = """\
Ты — ассистент по контролю качества оформления задач.

Ниже — шаблон, по которому должна быть оформлена карточка:

ШАБЛОН:
---
Текущая ситуация / Проблема

1. Что происходит сейчас (описание процесса: шаги, участники, системы)
2. Что не так (конкретная боль + цифры)
3. Как должно работать после решения (желаемое поведение)
4. Как поймём, что цель достигнута (измеримые метрики, цифры обязательны)

Детали

5. Срок / приоритет (когда нужно и почему сейчас)
6. Клиенты/Пользователи (кто именно видит проблему — конкретно, не «все»)
7. Масштаб (кол-во транзакций/подразделений/документов/клиентов — цифры обязательны)
8. Обязательность (почему эту задачу нельзя не сделать — аргументированно)

Материалы

- Ссылки на документы, скриншоты, файлы (необязательно)
---

Оцени описание карточки по 8 обязательным пунктам.

Правила оценки — провален пункт только если он пустой или содержит только шаблонный текст:
- П.1: есть описание процесса — провален только если пусто или шаблон
- П.2: есть конкретная проблема — цифры желательны, но не обязательны
- П.3: описано желаемое поведение — провален только если пусто или шаблон
- П.4: есть хотя бы одна метрика или критерий успеха (цифра, процент или качественный результат)
- П.5: указан срок ИЛИ причина «почему сейчас» — достаточно одного из двух
- П.6: названы роли, отделы или конкретные люди — «все» или «пользователи системы» не принимается
- П.7: есть хоть какое-то указание на масштаб (порядок цифр или оценка объёма)
- П.8: есть хоть какой-то аргумент почему нельзя откладывать — провален только если пусто или шаблон
Не придирайся к формулировкам — оценивай наличие смысла, а не идеальность текста.

Ответь строго в формате JSON (без markdown-обёртки):
{"passed": true/false, "issues": ["П.2 «Что не так» — нет цифр", ...]}

Если все 8 пунктов в порядке — "passed": true, "issues": [].

ОПИСАНИЕ КАРТОЧКИ:
"""


@dataclass
class CheckResult:
    passed: bool
    issues: list[str] = field(default_factory=list)
    card: dict = field(default_factory=dict)
    found_in_sheet: bool = True


def get_card(card_id: int) -> dict:
    headers = {"Authorization": f"Bearer {KAITEN_TOKEN}"}
    with httpx.Client(timeout=30) as client:
        r = client.get(f"{KAITEN_BASE}/cards/{card_id}", headers=headers)
        r.raise_for_status()
        return r.json()


def post_kaiten_comment(card_id: int, text: str) -> None:
    headers = {
        "Authorization": f"Bearer {KAITEN_TOKEN}",
        "Content-Type": "application/json",
    }
    with httpx.Client(timeout=30) as client:
        r = client.post(
            f"{KAITEN_BASE}/cards/{card_id}/comments",
            headers=headers,
            json={"text": text},
        )
        r.raise_for_status()


def card_url(card_id: int) -> str:
    return f"https://life-pay.kaiten.ru/space/{SPACE_ID}/boards/card/{card_id}"


def send_pachca_message(content: str) -> None:
    headers = {
        "Authorization": f"Bearer {PACHCA_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "message": {
            "entity_type": "group_chat",
            "entity_id": PACHCA_CHAT_ID,
            "content": content,
        }
    }
    with httpx.Client(timeout=30) as client:
        r = client.post(f"{PACHCA_BASE}/messages", headers=headers, json=payload)
        r.raise_for_status()


def write_kaiten_scores(card_id: int, scores: dict[str, int]) -> None:
    headers = {
        "Authorization": f"Bearer {KAITEN_TOKEN}",
        "Content-Type": "application/json",
    }
    properties = {
        f"id_{field_id}": scores[col]
        for col, field_id in KAITEN_FIELD_MAP.items()
    }
    with httpx.Client(timeout=30) as client:
        r = client.patch(
            f"{KAITEN_BASE}/cards/{card_id}",
            headers=headers,
            json={"properties": properties},
        )
        r.raise_for_status()
    log.info("Kaiten-баллы записаны в card_id=%d: %s", card_id, scores)


def run_eval_task_kaiten(card: dict) -> None:
    card_id = card["id"]
    title = card.get("title", "")
    description = card.get("description") or ""
    url = card_url(card_id)

    log.info("Запуск eval_task_kaiten для card_id=%d", card_id)
    scores = evaluate_criteria(title, description)
    write_kaiten_scores(card_id, scores)

    fresh = get_card(card_id)
    props = fresh.get("properties") or {}
    ibo = props.get("id_577176", "—")
    ikk = props.get("id_577181", "—")
    total = props.get("id_577182", "—")

    lines = [f"Карточка [{title}]({url}) оценена (поля Kaiten обновлены)"]
    lines.append(f"Админка\tИтоговая оценка - {total}")
    lines.append(f"Итоговая бизнес оценка. Админка - {ibo}")
    lines.append(f"Итоговый коэф. команды. Админка - {ikk}")
    send_pachca_message("\n".join(lines))


def _get_sheets_client() -> gspread.Client:
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = service_account.Credentials.from_service_account_file(
        GOOGLE_SERVICE_ACCOUNT_FILE, scopes=scopes
    )
    return gspread.authorize(creds)


def find_sheet_row(url: str) -> int | None:
    client = _get_sheets_client()
    ws = client.open_by_key(SPREADSHEET_ID).get_worksheet_by_id(SHEET_GID)
    all_rows = ws.get_all_values()
    card_id_str = url.split("/card/")[-1]
    for i, row in enumerate(all_rows):
        cell = row[8].strip() if len(row) > 8 else ""
        if cell and card_id_str in cell:
            return i + 1
    return None


def scores_already_filled(row_num: int) -> bool:
    client = _get_sheets_client()
    ws = client.open_by_key(SPREADSHEET_ID).get_worksheet_by_id(SHEET_GID)
    values = ws.get(f"O{row_num}:W{row_num}")
    if not values or not values[0]:
        return False
    return any(str(v).strip() not in ("", "0") for v in values[0])


def write_scores(row_num: int, scores: dict[str, int]) -> None:
    client = _get_sheets_client()
    ws = client.open_by_key(SPREADSHEET_ID).get_worksheet_by_id(SHEET_GID)
    values = [[
        scores["O"], scores["P"], scores["Q"], scores["R"],
        "",
        scores["T"], scores["U"], scores["V"], scores["W"],
    ]]
    ws.update(f"O{row_num}:W{row_num}", values, value_input_option="USER_ENTERED")
    log.info("Баллы записаны в строку %d: %s", row_num, scores)


def _claude(prompt: str, max_tokens: int = 1024) -> str:
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return raw.strip()


def evaluate_checklist(description: str) -> tuple[bool, list[str]]:
    raw = _claude(CHECKLIST_PROMPT + (description or "").strip())
    data = json.loads(raw)
    return bool(data.get("passed", False)), [str(i) for i in data.get("issues", [])]


def evaluate_criteria(title: str, description: str) -> dict[str, int]:
    criteria_text = "\n".join(
        f'  {col}. {info["name"]}:\n'
        + "\n".join(f"    {k}: {v}" for k, v in info["levels"].items())
        for col, info in CRITERIA.items()
    )

    prompt = f"""\
Оцени задачу по 8 критериям. Каждый критерий — балл от 0 до 3.
Оценивай ТОЛЬКО на основе информации в карточке. Если данных недостаточно — ставь 0.
При неоднозначности выбирай более низкий уровень.

КРИТЕРИИ:
{criteria_text}

ЗАДАЧА:
Название: {title}
Описание:
{description or "— нет описания —"}

Ответь строго в формате JSON (без markdown-обёртки):
{{"O": 0, "P": 0, "Q": 0, "R": 0, "T": 0, "U": 0, "V": 0, "W": 0}}
"""
    raw = _claude(prompt, max_tokens=512)
    data = json.loads(raw)
    return {col: max(0, min(3, int(data.get(col, 0)))) for col in ("O", "P", "Q", "R", "T", "U", "V", "W")}


def run_eval_task(card: dict):
    card_id = card["id"]
    title = card.get("title", "")
    description = card.get("description") or ""
    url = card_url(card_id)

    log.info("Запуск eval_task для card_id=%d", card_id)

    row_num = find_sheet_row(url)
    if row_num is None:
        log.warning("card_id=%d не найдена в Google Sheet", card_id)
        send_pachca_message(
            f"Карточка [{title}]({url}) прошла проверку оформления.\n"
            f"Не найдена в таблице приоритетов. Добавь строку со ссылкой в колонку H — "
            f"оценка запустится автоматически при следующей проверке."
        )
        return False

    if scores_already_filled(row_num):
        log.info("card_id=%d строка %d уже оценена — пропускаю", card_id, row_num)
        return

    scores = evaluate_criteria(title, description)
    write_scores(row_num, scores)

    ibo = scores["O"] * 0.30 + scores["P"] * 0.30 + scores["Q"] * 0.20 + scores["R"] * 0.20
    ikk = (scores["T"] + scores["U"] + scores["V"] + scores["W"]) / 4
    total = round(ibo + ikk, 2)

    lines = [f"Карточка [{title}]({url}) оценена и записана в таблицу (строка {row_num})."]
    lines.append(f"ИБО={round(ibo,2)} | ИКК={round(ikk,2)} | ИО={total}")
    for col, score in scores.items():
        lines.append(f"  {col} ({CRITERIA[col]['name']}): {score}")
    send_pachca_message("\n".join(lines))


def check_card(card_id: int) -> CheckResult:
    log.info("Проверяю карточку card_id=%d", card_id)

    card = get_card(card_id)
    title = card.get("title", "")
    description = card.get("description") or ""

    passed, issues = evaluate_checklist(description)

    found_in_sheet = True
    if passed:
        log.info("card_id=%d прошла чеклист", card_id)
        run_eval_task_kaiten(card)
    else:
        log.info("card_id=%d не прошла чеклист: %s", card_id, issues)
        lines = ["Карточка оформлена недостаточно. Нужно доработать:\n"]
        lines += [f"  {issue}" for issue in issues]
        lines.append("\nПосле доработки карточка будет проверена автоматически.")
        post_kaiten_comment(card_id, "\n".join(lines))

    return CheckResult(passed=passed, issues=issues, card=card, found_in_sheet=found_in_sheet)
