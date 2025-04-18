from __future__ import annotations

from datetime import datetime
from typing import Generator, Type

import pytest
from sqlalchemy.orm import Session

from models import DEFAULT_TAG, Bookmark, Tag
from reddit_tools import SavedPostsDb


class TestDatabase:
    EXISTING_BOOKMARK_ID = "003"
    NEW_BOOKMARK_ID = "100"

    EXISTING_TAGS = [f"tag_{x}" for x in "abcde"] + [DEFAULT_TAG]

    @pytest.fixture(autouse=True)
    def _class_fixture(self, local_database: SavedPostsDb):
        self._db = local_database.session

    @pytest.fixture(scope="function")
    def existing_tags(self) -> list[Type[Tag]]:
        Tag.create_tags(self.EXISTING_TAGS, session=self._db)
        return self._db.query(Tag).all()

    @pytest.fixture(scope="function")
    def existing_bookmark(self, existing_tags: list[Type[Tag]]) -> Bookmark:
        bookmark = Bookmark(
            id=self.EXISTING_BOOKMARK_ID,
            title="My existing bookmark",
            subreddit="test",
            url="https://my.bookmark.com/existing",
            date_created=datetime.now(),
        )
        if (
            Bookmark.get_existing(
                identifier=self.EXISTING_BOOKMARK_ID, session=self._db
            )
            is None
        ):
            bookmark.add_to_database(session=self._db)
        return Bookmark.get_existing(
            identifier=self.EXISTING_BOOKMARK_ID, session=self._db
        )

    @pytest.fixture(scope="function")
    def new_bookmark(self) -> Generator[Bookmark, None, None]:
        new_bookmark = Bookmark(
            id=self.NEW_BOOKMARK_ID,
            title="My new bookmark",
            subreddit="test",
            url="https://my.bookmark.com/new",
            date_created=datetime.now(),
        )
        yield new_bookmark
        self._db.delete(new_bookmark)
        self._db.commit()

    def test_add_new_bookmark(
        self,
        existing_bookmark: Bookmark,
        new_bookmark: Bookmark,
    ):
        assert new_bookmark not in self._db.query(Bookmark).all()
        assert (
            Bookmark.get_existing(identifier=self.NEW_BOOKMARK_ID, session=self._db)
            is None
        )

        new_bookmark.add_to_database(self._db)
        retrieved_bookmark = Bookmark.get_existing(
            identifier=self.NEW_BOOKMARK_ID, session=self._db
        )
        assert retrieved_bookmark is not None
        assert len(retrieved_bookmark.tags) == 1
        assert retrieved_bookmark.tags[0].name == DEFAULT_TAG
