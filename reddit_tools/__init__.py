from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from .saved_posts_db import SavedPostsDb

if TYPE_CHECKING:
    from praw import Reddit


def setup_logging():
    today = datetime.now().strftime("%Y-%m-%d")
    logging_dir = Path("logs")
    logging_dir.mkdir(parents=True, exist_ok=True)
    current_log = logging_dir / f"{today}.log"

    logging.basicConfig(
        level=logging.INFO,
        format="{asctime}:{levelname}:{message}",
        datefmt="%Y-%m-%d %H:%M",
        style="{",
        handlers=[
            logging.FileHandler(current_log),
            logging.StreamHandler(),
        ],
    )


def print_uncategorised_subreddits(reddit: Reddit):
    all_subreddits = set(reddit.user.subreddits(limit=None))

    multireddits = reddit.user.multireddits()
    subreddits_categorised = {s for m in multireddits for s in m.subreddits}

    subreddits_uncategorised = list(all_subreddits - subreddits_categorised)
    subreddits_uncategorised.sort(key=lambda s: s.display_name.lower())

    print(f"Not categorised ({len(subreddits_uncategorised)})")
    for subreddit in subreddits_uncategorised:
        print(f"\t{subreddit}")


setup_logging()
