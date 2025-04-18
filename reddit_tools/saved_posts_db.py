from __future__ import annotations

from itertools import tee
from pathlib import Path
from typing import Generator

import praw
from praw.models import Comment, Submission
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from models import Base, Bookmark

from .utils import get_secrets


class SavedPostsDb:
    def __init__(self, secrets: str | Path = None, database: str | Path = None):
        if isinstance(database, str):
            database = Path(database)
        self.__filepath = database
        self.__engine = None
        self.__init_engine()

        self.__session = Session(self.__engine)

        if secrets:
            secret_data = get_secrets(secrets)
            self.__reddit = praw.Reddit(
                client_id=secret_data["client_id"],
                client_secret=secret_data["client_secret"],
                username=secret_data["username"],
                password=secret_data["password"],
                user_agent=secret_data["user_agent"],
            )
        else:
            self.__reddit = None

    def __init_engine(self):
        if self.__filepath:
            db_url = f"sqlite:///{self.__filepath.as_posix()}"
        else:
            db_url = f"sqlite:///:memory:"

        self.__engine = create_engine(db_url, echo=True)
        Base.metadata.create_all(self.__engine)

    def __enter__(self) -> SavedPostsDb:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()

    def saved_posts(self) -> Generator[Comment | Submission, None, None]:
        return self.__reddit.user.me().saved(limit=None)

    def sync(self):
        all_, new_ = tee(self.saved_posts())

        all_bookmark_ids = {x.id for x in self.session.query(Bookmark).all()}
        all_saved_post_ids = {x.id for x in all_}

        # new saved posts not yet in database
        new_saved_posts_ids = all_saved_post_ids - all_bookmark_ids
        new_saved_posts = filter(lambda post: post.id in new_saved_posts_ids, new_)
        for s in new_saved_posts:
            bookmark = Bookmark.from_saved_post(s)
            bookmark.add_to_database(self.session)

        # posts no longer saved - to be deleted from the database
        removed_posts_ids = list(all_bookmark_ids - all_saved_post_ids)
        removed_bookmarks = self.session.query(Bookmark).filter(
            Bookmark.id.in_(removed_posts_ids)
        )
        removed_bookmarks.delete()
        self.session.commit()

    @property
    def session(self) -> Session:
        return self.__session
