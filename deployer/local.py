import shutil
import subprocess
import sys
from pathlib import Path

INSTALL_DIR = Path.home() / ".kaiten-watcher"

_ASSETS = ["watcher.py", "checker.py", "requirements.txt", "Dockerfile", "docker-compose.yml"]

_CONFIG_KEYS = [
    "KAITEN_TOKEN", "KAITEN_BASE_URL", "KAITEN_SPACE_ID", "KAITEN_COLUMN_IDS",
    "PACHCA_TOKEN", "PACHCA_BASE_URL", "PACHCA_CHAT_ID",
    "ANTHROPIC_API_KEY",
    "POLL_INTERVAL", "INCIDENT_PROPERTY_ID", "INCIDENT_OPTION_ID",
    "SPREADSHEET_ID", "SHEET_GID", "GOOGLE_SERVICE_ACCOUNT_FILE",
    "KAITEN_FIELD_O", "KAITEN_FIELD_P", "KAITEN_FIELD_Q", "KAITEN_FIELD_R",
    "KAITEN_FIELD_T", "KAITEN_FIELD_U", "KAITEN_FIELD_V", "KAITEN_FIELD_W",
]


def asset_path(name: str) -> Path:
    if hasattr(sys, "_MEIPASS"):
        base = Path(sys._MEIPASS) / "assets"
    else:
        base = Path(__file__).parent.parent / "assets"
    return base / name


def write_config(path: Path, cfg: dict) -> None:
    lines = []
    for k in _CONFIG_KEYS:
        v = cfg.get(k)
        if v:
            lines.append(f"{k}={v}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def deploy_local(cfg: dict, log) -> None:
    log("→ Проверяю Docker...")
    result = subprocess.run(
        ["docker", "info"], capture_output=True, timeout=15
    )
    if result.returncode != 0:
        raise RuntimeError(
            "Docker не запущен или не установлен. Запустите Docker Desktop и повторите."
        )
    log("   Docker доступен")

    log(f"→ Создаю каталог {INSTALL_DIR}")
    INSTALL_DIR.mkdir(parents=True, exist_ok=True)

    for f in _ASSETS:
        src = asset_path(f)
        dst = INSTALL_DIR / f
        log(f"   Копирую {f}")
        shutil.copy2(src, dst)

    sa = cfg.get("GOOGLE_SERVICE_ACCOUNT_FILE")
    if sa and Path(sa).exists():
        log("   Копирую service_account.json")
        shutil.copy2(sa, INSTALL_DIR / "service_account.json")
        cfg["GOOGLE_SERVICE_ACCOUNT_FILE"] = "/app/service_account.json"

    log("→ Записываю config.env")
    write_config(INSTALL_DIR / "config.env", cfg)

    state = INSTALL_DIR / "state.json"
    if not state.exists():
        state.write_text("{}")

    log("→ Запускаю docker-compose up -d --build ...")
    proc = subprocess.Popen(
        ["docker", "compose", "-f", str(INSTALL_DIR / "docker-compose.yml"),
         "up", "-d", "--build"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        cwd=str(INSTALL_DIR),
    )
    for line in proc.stdout:
        log("   " + line.decode(errors="replace").rstrip())
    proc.wait()
    if proc.returncode != 0:
        raise RuntimeError(f"docker compose завершился с кодом {proc.returncode}")

    (INSTALL_DIR / ".installed").write_text("ok")
    log(f"→ Маркер установки записан в {INSTALL_DIR / '.installed'}")
