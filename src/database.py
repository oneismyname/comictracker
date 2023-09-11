from src import db
from flask_login import UserMixin



class Mapping(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    comic_id = db.Column(db.Integer, db.ForeignKey('comic.id'), primary_key=True)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    email = db.Column(db.String(1000), nullable=False)
    avatar = db.Column(db.String(100), nullable=False, default='https://picsum.photos/200')
    password = db.Column(db.String(1000), nullable=False)
    following = db.relationship('Mapping', backref='user')
    check = db.relationship('Checking', backref='check')


class Comic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    img_cover = db.Column(db.String(1000))
    follower = db.relationship('Mapping', backref='comic')
    schedule_location = db.relationship('Schedule', backref='schedule_location')


class Schedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    comic_id = db.Column(db.Integer, db.ForeignKey('comic.id'))
    volume = db.Column(db.String(100), nullable=False)
    edition = db.Column(db.String(100),nullable=False)
    price = db.Column(db.Integer, nullable=False)
    release_date = db.Column(db.Date, nullable=False)
    publisher = db.Column(db.String(250), nullable=False)
    schedule = db.relationship('Checking', backref='schedule')
    img = db.Column(db.String(1000))


class Checking(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    schedule_id = db.Column(db.Integer, db.ForeignKey('schedule.id'), primary_key=True)
    bought = db.Column(db.Boolean, default=False)
    price = db.Column(db.Integer)