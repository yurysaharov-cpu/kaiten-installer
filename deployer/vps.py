import tempfile
from pathlib import Path

from deployer.local import asset_path, write_config, _ASSETS

_MARKER = ".installed"


def deploy_vps(cfg: dict, log) -> None:
    import paramiko

    host = cfg["vps_host"]
    port = cfg["vps_port"]
    user = cfg["vps_user"]
    password = cfg["vps_pass"]
    deploy_path = cfg.get("vps_path", "/opt/kaiten-watcher")

    log(f"→ Подключаюсь к {user}@{host}:{port} ...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, port=port, username=user, password=password, timeout=20)
    log("   Соединение установлено")

    sftp = ssh.open_sftp()

    log(f"→ Создаю каталог {deploy_path}")
    _exec(ssh, f"mkdir -p {deploy_path}", log)

    sa = cfg.get("GOOGLE_SERVICE_ACCOUNT_FILE")
    if sa and Path(sa).exists():
        log("   Загружаю service_account.json")
        sftp.put(sa, f"{deploy_path}/service_account.json")
        cfg["GOOGLE_SERVICE_ACCOUNT_FILE"] = f"{deploy_path}/service_account.json"

    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    write_config(tmp_path, cfg)
    log("→ Загружаю config.env")
    sftp.put(str(tmp_path), f"{deploy_path}/config.env")
    tmp_path.unlink(missing_ok=True)

    for f in _ASSETS:
        log(f"   Загружаю {f}")
        sftp.put(str(asset_path(f)), f"{deploy_path}/{f}")

    _exec(ssh,
          f"test -f {deploy_path}/state.json || echo '{{}}' > {deploy_path}/state.json",
          log)

    log("→ Запускаю docker compose up -d --build ...")
    _exec(ssh, f"cd {deploy_path} && docker compose up -d --build 2>&1", log, stream=True)

    _exec(ssh, f"touch {deploy_path}/{_MARKER}", log)

    sftp.close()
    ssh.close()
    log("→ SSH-соединение закрыто")


def _exec(ssh, cmd: str, log, stream: bool = False) -> None:
    _, stdout, stderr = ssh.exec_command(cmd)
    if stream:
        for line in stdout:
            log("   " + line.rstrip())
    else:
        out = stdout.read().decode(errors="replace").strip()
        err = stderr.read().decode(errors="replace").strip()
        if out:
            log("   " + out)
        if err:
            log("   " + err)
    rc = stdout.channel.recv_exit_status()
    if rc != 0 and not stream:
        raise RuntimeError(f"Команда завершилась с кодом {rc}: {cmd}")
