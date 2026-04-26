from __future__ import annotations

import argparse
import os
import signal
import shutil
import socket
import subprocess
import sys
import threading
import time
from collections.abc import Sequence
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND_PYTHON = ROOT / "backend" / ".venv" / "Scripts" / "python.exe"


def resolve_npm_command() -> list[str]:
    candidates = ["npm.cmd", "npm"]
    for candidate in candidates:
        resolved = shutil.which(candidate)
        if resolved:
            return [resolved, "--prefix", str(ROOT / "frontend")]
    raise RuntimeError("npm was not found on PATH. Install Node.js and npm, then retry.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Start AI Scientist OS development services from one terminal.",
    )
    parser.add_argument(
        "--skip-docker",
        action="store_true",
        help="Skip starting docker compose services.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print commands without starting long-running processes.",
    )
    return parser.parse_args()


def run_command(command: Sequence[str], *, cwd: Path) -> None:
    completed = subprocess.run(command, cwd=cwd, check=False)
    if completed.returncode != 0:
        raise RuntimeError(f"Command failed ({completed.returncode}): {' '.join(command)}")


def wait_for_port(host: str, port: int, *, timeout_seconds: int, service_name: str) -> None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=1):
                return
        except OSError:
            time.sleep(1)
    raise RuntimeError(f"{service_name} was not reachable at {host}:{port} within {timeout_seconds} seconds.")


def stream_output(prefix: str, process: subprocess.Popen[str]) -> None:
    assert process.stdout is not None
    for line in process.stdout:
        print(f"[{prefix}] {line}", end="")


def start_process(
    name: str,
    command: Sequence[str],
    *,
    cwd: Path,
    env: dict[str, str],
) -> subprocess.Popen[str]:
    process = subprocess.Popen(
        command,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    thread = threading.Thread(target=stream_output, args=(name, process), daemon=True)
    thread.start()
    return process


def terminate_processes(processes: list[subprocess.Popen[str]]) -> None:
    for process in processes:
        if process.poll() is None:
            process.terminate()
    deadline = time.time() + 10
    for process in processes:
        while process.poll() is None and time.time() < deadline:
            time.sleep(0.2)
        if process.poll() is None:
            process.kill()


def main() -> int:
    args = parse_args()

    if not BACKEND_PYTHON.exists():
        print(
            "Backend virtual environment was not found. Run `make setup` first.",
            file=sys.stderr,
        )
        return 1
    try:
        npm_cmd = resolve_npm_command()
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    docker_cmd = ["docker", "compose", "up", "-d", "postgres", "redis"]
    backend_cmd = [
        str(BACKEND_PYTHON),
        "-m",
        "uvicorn",
        "app.main:app",
        "--reload",
        "--app-dir",
        "backend",
    ]
    worker_cmd = [str(BACKEND_PYTHON), str(ROOT / "scripts" / "run_worker.py")]
    frontend_cmd = [*npm_cmd, "run", "dev"]

    print("AI Scientist OS dev launcher")
    if not args.skip_docker:
        print(f"- Docker services: {' '.join(docker_cmd)}")
    print(f"- Backend: {' '.join(backend_cmd)}")
    print(f"- Worker: {' '.join(worker_cmd)}")
    print(f"- Frontend: {' '.join(frontend_cmd)}")

    if args.dry_run:
        return 0

    if not args.skip_docker:
        run_command(docker_cmd, cwd=ROOT)
        wait_for_port("127.0.0.1", 5433, timeout_seconds=30, service_name="PostgreSQL")
        wait_for_port("127.0.0.1", 6379, timeout_seconds=30, service_name="Redis")

    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"

    processes: list[subprocess.Popen[str]] = []
    stop_event = threading.Event()

    def stop_all(_: int | None = None, __: object | None = None) -> None:
        if stop_event.is_set():
            return
        stop_event.set()
        print("\nStopping AI Scientist OS dev services...")
        terminate_processes(processes)

    if hasattr(signal, "SIGINT"):
        signal.signal(signal.SIGINT, stop_all)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, stop_all)

    try:
        processes.append(start_process("backend", backend_cmd, cwd=ROOT, env=env))
        time.sleep(2)
        processes.append(start_process("worker", worker_cmd, cwd=ROOT, env=env))
        processes.append(start_process("frontend", frontend_cmd, cwd=ROOT, env=env))

        while not stop_event.is_set():
            for process in processes:
                code = process.poll()
                if code is not None:
                    stop_all()
                    return code
            time.sleep(1)
        return 0
    finally:
        terminate_processes(processes)


if __name__ == "__main__":
    raise SystemExit(main())
