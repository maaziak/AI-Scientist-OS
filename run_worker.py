from __future__ import annotations

import argparse
import platform
from typing import Any

from redis import Redis
from redis.exceptions import ConnectionError as RedisConnectionError
from rq import SimpleWorker, Worker

from app.core.config import get_settings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the AI Scientist OS RQ worker.")
    parser.add_argument(
        "--burst",
        action="store_true",
        help="Process queued jobs and then exit.",
    )
    return parser.parse_args()


def worker_class() -> type[Any]:
    if platform.system().lower() == "windows":
        return SimpleWorker
    return Worker


def main() -> int:
    args = parse_args()
    settings = get_settings()
    redis_client = Redis.from_url(settings.redis_url)
    try:
        worker = worker_class()([settings.rq_queue_name], connection=redis_client)
    except RedisConnectionError:
        print(
            "Redis is not reachable at "
            f"{settings.redis_url}. Start Redis first, for example with "
            "`docker compose up redis` or `docker compose up postgres redis`."
        )
        return 1
    worker.work(burst=args.burst)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
