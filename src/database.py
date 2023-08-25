from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    email = db.Column(db.String(1000), nullable=False)
    password = db.Column(db.String(1000), nullable=False)


class Comic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    volume = db.Column(db.String(100), nullable=False)
    edition = db.Column(db.String(100),nullable=False)
    price = db.Column(db.Integer, nullable=False)
    release_date = db.Column(db.Date, nullable=False)
    publisher = db.Column(db.String(250), nullable=False)