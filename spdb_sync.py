from reddit_tools import SavedPostsDb


def main():
    with SavedPostsDb(database="saved.db", secrets=".secrets") as db:
        db.sync()


if __name__ == "__main__":
    main()
