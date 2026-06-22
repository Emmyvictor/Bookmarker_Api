from datetime import datetime
import random
import string
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    # FIX: Capitalized db.Column and used standard Python True
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.Text(), nullable=False)

    # FIX: Removed () from datetime.now so it generates at insertion time
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, onupdate=datetime.now)

    # FIX: Changed "Bookmarks" to "Bookmark" to match the class name
    bookmarks = db.relationship("Bookmark", backref="user")

    def __repr__(self) -> str:
        return f"User>>> {self.username}"


class Bookmark(db.Model):
    # FIX: Capitalized db.Column across all fields
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text, nullable=True)
    url = db.Column(db.Text, nullable=False)
    short_url = db.Column(db.String(3), nullable=True)
    visits = db.Column(db.Integer, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    # FIX: Removed () from datetime.now
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, onupdate=datetime.now)

    def generate_short_characters(self):
        characters = string.digits + string.ascii_letters
        picked_chars = "".join(random.choices(characters, k=3))

        link = self.query.filter_by(short_url=picked_chars).first()

        if link:
            # FIX: Added 'return' here so recursion passes the value back up
            return self.generate_short_characters()
        else:
            return picked_chars

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.short_url = self.generate_short_characters()

    def __repr__(self) -> str:
        return f"Bookmark>>> {self.url}"
