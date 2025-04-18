from __future__ import annotations

from datetime import datetime

import pytest

from models import DEFAULT_TAG, Bookmark, Tag
from reddit_tools import SavedPostsDb


class BaseTestModel:
    @pytest.fixture(autouse=True)
    def _class_fixture(self, tmp_database: SavedPostsDb):
        self._db = tmp_database.session


class TestTags(BaseTestModel):
    @pytest.fixture(autouse=True)
    def _class_fixture(self, tmp_database: SavedPostsDb):
        """
        Initializes the database with one tag.
        """
        self._db = tmp_database.session

        Tag.create_tags("existing", self._db)
        self._prev_num_tags = self.num_tags

    @property
    def all_tags(self) -> set[str]:
        return {tag.name for tag in self._db.query(Tag).all()}

    @property
    def num_tags(self) -> int:
        return self._db.query(Tag).count()

    @pytest.mark.parametrize("tag", ("single_tag", "SINGLE_TAG_UPPERCASE"))
    def test_create_new_tag(self, tag: str):
        Tag.create_tags(tag, self._db)
        assert {tag.lower()}.issubset(self.all_tags)
        assert self.num_tags == self._prev_num_tags + 1

    @pytest.mark.parametrize(
        "tags",
        [
            ("multi_tag1", "multi_tag2"),
            ("MULTI_TAG_UPPERCASE1", "MULTI_TAG_UPPERCASE2"),
        ],
    )
    def test_create_multiple_new_tags(self, tags: list[str]):
        Tag.create_tags(tags, self._db)
        assert {tag.lower() for tag in tags}.issubset(self.all_tags)
        assert self.num_tags == self._prev_num_tags + 2

    def test_create_unique_tags(self):
        tags = ("repeated_Tags", "repeated_Tags")
        Tag.create_tags(tags, self._db)
        assert self.num_tags == self._prev_num_tags + 1

    @pytest.mark.parametrize("new_tags", ["already", ["already", "I"]])
    def test_add_existing_tag(self, new_tags):
        existing_tags = {"i", "already", "exist"}
        Tag.create_tags(existing_tags, self._db)
        Tag.create_tags(new_tags, self._db)
        assert self.num_tags == self._prev_num_tags + 3

    @pytest.mark.parametrize("tag", ["existing", "new"])
    def test_get_tag(self, tag: str):
        Tag.create_tags("existing", self._db)
        tag_obj = Tag.get(tag, self._db)
        assert tag_obj.name == tag.lower()


class TestBookmark(BaseTestModel):
    def test_add_bookmark(self):
        bookmark_id = "wan25a2"
        assert Bookmark.get_existing(identifier=bookmark_id, session=self._db) is None

        new_bookmark = Bookmark(
            id=bookmark_id,
            title="My bookmark",
            subreddit="test",
            url="http://my.bookmark.com",
            date_created=datetime.now(),
        )
        new_bookmark.add_to_database(self._db)

        retrieved_bookmark = Bookmark.get_existing(
            identifier=bookmark_id, session=self._db
        )
        assert retrieved_bookmark == new_bookmark
        assert retrieved_bookmark.tags[0].name == DEFAULT_TAG
