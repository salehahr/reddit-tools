from __future__ import annotations

from typing import TYPE_CHECKING

import praw
import pytest
from sqlalchemy.exc import IntegrityError

from models import Bookmark
from reddit_tools import SavedPostsDb

if TYPE_CHECKING:
    from praw.models import Comment, Submission


class TestSavedPostsDatabase:
    @pytest.fixture(scope="session")
    def new_submission(self, reddit: praw.Reddit) -> praw.models.Submission:
        return reddit.submission(id="1k11kdy")

    @pytest.fixture(scope="session")
    def new_comment(self, reddit: praw.Reddit) -> praw.models.Comment:
        return reddit.comment(id="mnilzco")

    @pytest.fixture(scope="session")
    def existing_submission(self, reddit: praw.Reddit) -> praw.models.Submission:
        return reddit.submission(id="iam3qr")

    @pytest.fixture(scope="session")
    def existing_comment(self, reddit: praw.Reddit) -> praw.models.Comment:
        return reddit.comment(id="g1pgxy4")

    @pytest.fixture(autouse=True)
    def _class_fixture(self, local_database: SavedPostsDb):
        self._db = local_database.session
        self._prev_num_bookmarks = self.num_bookmarks

    @property
    def num_bookmarks(self) -> int:
        return self._db.query(Bookmark).count()

    def test_add_new_submission(self, new_submission: Submission):
        assert self._db.query(Bookmark).get(new_submission.id) is None

        bm = Bookmark.from_saved_post(new_submission)
        bm.add_to_database(self._db)

        assert self._db.query(Bookmark).get(new_submission.id) is not None

    def test_add_new_comment(self, new_comment: Comment):
        assert self._db.query(Bookmark).get(new_comment.id) is None

        bm = Bookmark.from_saved_post(new_comment)
        bm.add_to_database(self._db)

        assert self._db.query(Bookmark).get(new_comment.id) is not None

    def test_add_existing_submission(self, existing_submission: Submission):
        assert self._db.query(Bookmark).get(existing_submission.id) is not None

        bm = Bookmark.from_saved_post(existing_submission)
        with pytest.raises(IntegrityError):
            bm.add_to_database(self._db)
