from flask import Flask, flash, g, redirect, render_template, url_for

from reddit_tools import SavedPostsDb

app = Flask(__name__)
app.config["SECRET_KEY"] = "DEFAULT"


@app.before_request
def before_request():
    g.db = SavedPostsDb(database="saved.db", secrets=".secrets")


@app.teardown_request
def teardown_request(exception=None):
    if hasattr(g, "db"):
        g.db.session.close()


@app.route("/sync", methods=["POST"])
def sync_db():
    g.db.sync()
    flash("Database synced successfully!", "success")
    return redirect(url_for("index"))


@app.route("/", methods=["GET", "POST"])
def index():
    db = g.db
    return render_template("index.html", bookmarks=db.bookmarks)


def main():
    app.run(debug=True)


if __name__ == "__main__":
    main()
