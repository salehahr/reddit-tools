from __future__ import annotations

import shutil
from pathlib import Path
from typing import Generator

import praw
import pytest

from reddit_tools import SavedPostsDb
from reddit_tools.utils import get_secrets


def __create_backup(orig: Path, suffix: str = None) -> Path:
    if not orig.exists():
        return orig

    backup = Path(f"{orig.stem}_{suffix if suffix else 'backup'}.db")
    shutil.copy(orig, backup)
    return backup


def __restore_from_backup(orig: Path, backup: Path):
    shutil.move(backup, orig)


@pytest.fixture(scope="session")
def local_database() -> Generator[SavedPostsDb, None, None]:
    db_filepath = Path(__file__).parent / "saved.db"
    backup = __create_backup(db_filepath)

    with SavedPostsDb(database=db_filepath) as db:
        yield db

    __restore_from_backup(db_filepath, backup)


@pytest.fixture(scope="function")
def tmp_database() -> Generator[SavedPostsDb, None, None]:
    with SavedPostsDb() as db:
        yield db


@pytest.fixture(scope="session")
def reddit() -> praw.Reddit:
    secrets_filepath = Path(".secrets")
    secrets = get_secrets(secrets_filepath)
    reddit = praw.Reddit(
        client_id=secrets["client_id"],
        client_secret=secrets["client_secret"],
        user_agent=secrets["user_agent"],
    )
    assert reddit.read_only
    return reddit
