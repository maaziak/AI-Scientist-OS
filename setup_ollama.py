from __future__ import annotations

import json
import subprocess
import time
from urllib.error import URLError
from urllib.request import urlopen


OLLAMA_URL = "http://localhost:11434/api/tags"
CLOUD_CHAT_MODELS = [
    "gpt-oss:120b-cloud",
    "deepseek-v3.1:671b-cloud",
    "gpt-oss:20b-cloud",
]


def ollama_installed() -> bool:
    try:
        subprocess.run(["ollama", "--version"], check=True, capture_output=True, text=True)
        return True
    except Exception:
        return False


def ollama_running() -> bool:
    try:
        with urlopen(OLLAMA_URL, timeout=5) as response:  # noqa: S310
            return response.status == 200
    except URLError:
        return False


def start_ollama_if_possible() -> None:
    subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)  # noqa: S603,S607
    time.sleep(5)


def installed_models() -> list[str]:
    with urlopen(OLLAMA_URL, timeout=10) as response:  # noqa: S310
        payload = json.loads(response.read().decode("utf-8"))
    return [item["name"] for item in payload.get("models", [])]


def ensure_model(candidates: list[str]) -> str | None:
    models = installed_models()
    for candidate in candidates:
        prefix = candidate.split(":")[0]
        if any(item == candidate or item.split(":")[0] == prefix for item in models):
            return candidate
    for candidate in candidates[:2]:
        print(f"Pulling missing Ollama model: {candidate}")
        result = subprocess.run(["ollama", "pull", candidate], check=False, text=True)  # noqa: S603,S607
        if result.returncode == 0:
            return candidate
    return None


def main() -> int:
    if not ollama_installed():
        print("Ollama is not installed. Install it from https://ollama.com/download and rerun setup.")
        return 1
    if not ollama_running():
        print("Ollama was installed but not running. Attempting to start it now...")
        start_ollama_if_possible()
    if not ollama_running():
        print("Ollama is still not reachable at http://localhost:11434. Start it manually with `ollama serve`.")
        return 1

    chat = ensure_model(CLOUD_CHAT_MODELS)
    if chat is None:
        print(
            "No supported Ollama cloud chat model is available. "
            "Run `ollama signin`, then `ollama pull gpt-oss:120b-cloud` "
            "or `ollama pull deepseek-v3.1:671b-cloud`."
        )
        return 1
    print(
        "Ollama ready. "
        f"Cloud chat model: {chat}. "
        "No cloud embedding model is configured, so the app will use keyword retrieval fallback."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
