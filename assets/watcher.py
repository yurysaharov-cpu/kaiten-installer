import json
import logging
import os
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / "config.env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

KAITEN_TOKEN = os.environ["KAITEN_TOKEN"]
KAITEN_BASE = os.environ["KAITEN_BASE_URL"].rstrip("/")
COLUMN_IDS = [x.strip() for x in os.environ["KAITEN_COLUMN_IDS"].split(",")]
SPACE_ID = os.environ["KAITEN_SPACE_ID"]

PACHCA_TOKEN = os.environ["PACHCA_TOKEN"]
PACHCA_BASE = os.environ["PACHCA_BASE_URL"].rstrip("/")
PACHCA_CHAT_ID = int(os.environ["PACHCA_CHAT_ID"])

POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL", "600"))
INCIDENT_PROPERTY_ID = os.environ.get("INCIDENT_PROPERTY_ID", "576936")
INCIDENT_OPTION_ID = int(os.environ.get("INCIDENT_OPTION_ID", "16305587"))

STATE_FILE = Path(__file__).parent / "state.json"


def load_state() -> tuple[set[int], list[dict], list[dict]]:
    if STATE_FILE.exists():
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        seen = set(data.get("seen_ids", []))
        pending = data.get("pending_review", [])
        pending_eval = data.get("pending_eval", [])
        return seen, pending, pending_eval
    return set(), [], []


def save_state(seen_ids: set[int], pending_review: list[dict], pending_eval: list[dict]) -> None:
    STATE_FILE.write_text(
        json.dumps(
            {
                "seen_ids": list(seen_ids),
                "pending_review": pending_review,
                "pending_eval": pending_eval,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def get_column_cards(column_id: str) -> list[dict]:
    headers = {"Authorization": f"Bearer {KAITEN_TOKEN}"}
    with httpx.Client(timeout=30) as client:
        r = client.get(f"{KAITEN_BASE}/cards", params={"column_id": column_id}, headers=headers)
        r.raise_for_status()
        return r.json()


def get_card(card_id: int) -> dict:
    headers = {"Authorization": f"Bearer {KAITEN_TOKEN}"}
    with httpx.Client(timeout=30) as client:
        r = client.get(f"{KAITEN_BASE}/cards/{card_id}", headers=headers)
        r.raise_for_status()
        return r.json()


def get_incident_type(card: dict) -> bool:
    props = card.get("properties") or {}
    option_ids = props.get(f"id_{INCIDENT_PROPERTY_ID}", [])
    if isinstance(option_ids, list):
        return INCIDENT_OPTION_ID in option_ids
    return False


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


def card_url(card_id: int) -> str:
    return f"https://life-pay.kaiten.ru/space/{SPACE_ID}/boards/card/{card_id}"


def run_checker(card_id: int):
    from checker import check_card
    try:
        return check_card(card_id)
    except Exception as e:
        log.error("Ошибка checker для card_id=%d: %s", card_id, e)
        return None


def poll() -> dict[int, dict]:
    all_cards = {}
    for col_id in COLUMN_IDS:
        for card in get_column_cards(col_id):
            all_cards[card["id"]] = card
    return all_cards


def run():
    log.info("kaiten-watcher started | columns=%s interval=%ds", COLUMN_IDS, POLL_INTERVAL)

    seen_ids, pending_review, pending_eval = load_state()

    if not seen_ids:
        log.info("First run — initializing state, no notifications sent")
        cards = poll()
        save_state(set(cards.keys()), [], [])
        log.info("Initialized with %d cards", len(cards))
        return

    while True:
        try:
            cards = poll()
            current_ids = set(cards.keys())
            new_ids = current_ids - seen_ids

            for card_id in new_ids:
                card = cards[card_id]
                title = card.get("title", "")
                url = card_url(card_id)
                is_incident = get_incident_type(card)

                if is_incident:
                    text = f'Создана новая карточка [{title}]({url}) с типом INCIDENT'
                else:
                    text = f'Создана новая карточка [{title}]({url})'

                try:
                    send_pachca_message(text)
                    log.info("Sent notification: card=%d incident=%s", card_id, is_incident)
                except Exception as e:
                    log.error("Failed to send Pachca message for card %d: %s", card_id, e)

                result = run_checker(card_id)
                if result is None:
                    pass
                elif not result.passed:
                    full_card = get_card(card_id)
                    pending_review.append({
                        "card_id": card_id,
                        "updated": full_card.get("updated", ""),
                    })
                    log.info("card_id=%d добавлена в pending_review", card_id)
                elif not result.found_in_sheet:
                    pending_eval.append({"card_id": card_id})
                    log.info("card_id=%d добавлена в pending_eval", card_id)

            seen_ids = seen_ids | new_ids

            still_pending = []
            for entry in pending_review:
                card_id = entry["card_id"]
                try:
                    fresh = get_card(card_id)
                    fresh_updated = fresh.get("updated", "")
                    entry_updated = entry.get("updated") or entry.get("updated_at", "")

                    if fresh_updated != entry_updated:
                        log.info("card_id=%d обновлена — повторная проверка", card_id)
                        result = run_checker(card_id)
                        if result is None:
                            still_pending.append(entry)
                        elif result.passed:
                            log.info("card_id=%d прошла повторную проверку", card_id)
                            if not result.found_in_sheet:
                                pending_eval.append({"card_id": card_id})
                        else:
                            still_pending.append({
                                "card_id": card_id,
                                "updated": fresh_updated,
                            })
                    else:
                        still_pending.append(entry)
                except Exception as e:
                    log.error("Ошибка при проверке pending card_id=%d: %s", card_id, e)
                    still_pending.append(entry)

            pending_review = still_pending

            from checker import find_sheet_row, run_eval_task, get_card as checker_get_card
            if pending_eval:
                log.info("pending_eval: проверяю %d карточек", len(pending_eval))
            still_pending_eval = []
            for entry in pending_eval:
                card_id = entry["card_id"]
                try:
                    url = card_url(card_id)
                    row_num = find_sheet_row(url)
                    if row_num is not None:
                        log.info("card_id=%d появилась в таблице (строка %d)", card_id, row_num)
                        card = checker_get_card(card_id)
                        result = run_eval_task(card)
                        if result is False:
                            still_pending_eval.append(entry)
                    else:
                        still_pending_eval.append(entry)
                except Exception as e:
                    log.error("Ошибка при pending_eval card_id=%d: %s", card_id, e)
                    still_pending_eval.append(entry)

            pending_eval = still_pending_eval
            save_state(seen_ids, pending_review, pending_eval)

        except Exception as e:
            log.error("Poll error: %s", e)

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    run()
