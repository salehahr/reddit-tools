from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Iterable, List

from praw.models import Comment, Submission
from sqlalchemy import Column, ForeignKey, Table, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class Base(DeclarativeBase):
    pass


association_table = Table(
    "association_table",
    Base.metadata,
    Column("bookmarks", ForeignKey("bookmarks.id"), primary_key=True),
    Column("tags", ForeignKey("tags.name"), primary_key=True),
)

DEFAULT_TAG = "_untagged"
REDDIT_URL = "https://www.reddit.com"


class Bookmark(Base):
    __tablename__ = "bookmarks"

    id: Mapped[str] = mapped_column(primary_key=True)
    url: Mapped[str] = mapped_column()
    title: Mapped[str] = mapped_column()
    subreddit: Mapped[str] = mapped_column()
    date_created: Mapped[datetime] = mapped_column()
    tags: Mapped[List[Tag]] = relationship(
        "Tag", secondary=association_table, back_populates="bookmarks"
    )

    def __init__(self, **kwargs):
        date_created = kwargs["date_created"]

        match date_created:
            case float():
                kwargs["date_created"] = datetime.fromtimestamp(date_created)
            case datetime():
                pass
            case _:
                raise TypeError(
                    f"Invalid date_created type: {date_created=}, {type(date_created)=}"
                )
        super().__init__(**kwargs)

    def __repr__(self):
        return f"<Bookmark(title='{self.title}', url='{self.url}')>"

    @staticmethod
    def from_saved_post(saved_post: Submission | Comment) -> Bookmark:
        title, url = "", ""

        match saved_post:
            case Submission():
                title = saved_post.title
                url = REDDIT_URL + saved_post.permalink
            case Comment():
                title = f"{saved_post.author}: {saved_post.body[:40]}"
                url = REDDIT_URL + f"{saved_post.submission.permalink}/{saved_post.id}"

        return Bookmark(
            id=saved_post.id,
            title=title,
            subreddit=saved_post.subreddit.display_name,
            date_created=saved_post.created_utc,
            url=url,
        )

    @classmethod
    def get_existing(cls, identifier: str, session: Session) -> Bookmark | None:
        return session.query(cls).filter_by(id=identifier).first()

    def add_to_database(self, session: Session) -> None:
        if not self.tags:
            self.apply_tag(DEFAULT_TAG, session)
        session.add(self)
        session.commit()

    def apply_tag(self, tag: str | Tag, session: Session) -> None:
        match tag:
            case str():
                tag_obj = Tag.get(identifier=tag, session=session)
            case Tag():
                tag_obj = tag
            case _:
                raise TypeError

        if tag_obj not in self.tags:
            self.tags.append(tag_obj)

    @property
    def tags_string(self) -> str:
        if DEFAULT_TAG in (t.name for t in self.tags):
            return ""
        return ", ".join(tag.name for tag in self.tags)

    @property
    def date_created_string(self) -> str:
        return self.date_created.strftime("%Y-%m-%d")


class Tag(Base):
    __tablename__ = "tags"

    name: Mapped[str] = mapped_column(primary_key=True, unique=True, nullable=False)
    bookmarks: Mapped[List[Bookmark]] = relationship(
        "Bookmark", secondary=association_table, back_populates="tags"
    )

    def __repr__(self):
        return f"<Tag(name='{self.name}')>"

    @staticmethod
    def contains(tag_name: str, session: Session) -> bool:
        return session.query(Tag).filter_by(name=tag_name).first() is not None

    @classmethod
    def create_tags(cls, tags: str | Iterable[str], session: Session):
        if isinstance(tags, str):
            new_tag_names = {tags.lower()}
        else:
            new_tag_names = {t.lower() for t in tags}

        existing_tag_names = set(
            session.scalars(select(Tag.name).where(Tag.name.in_(new_tag_names))).all()
        )
        if len(existing_tag_names) < len(tags):
            new_tags = [Tag(name=name) for name in (new_tag_names - existing_tag_names)]
            session.bulk_save_objects(new_tags)
            session.commit()

    @classmethod
    def get(cls, identifier: str, session: Session) -> Tag:
        if (entry := session.query(cls).filter_by(name=identifier).first()) is None:
            entry = cls(name=identifier)
            session.add(entry)
        return entry
