from flask import Flask, session
from flask_bootstrap import Bootstrap5
from flask_login import LoginManager
from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy



import src.local_func
app = Flask(__name__)
app.config['SECRET_KEY'] = "thisismysecretkey"
app.permanent_session_lifetime = timedelta(days=30)
Bootstrap5(app)

login_manager = LoginManager()
login_manager.init_app(app)

# create table

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///webdata.db'
db = SQLAlchemy(app)


with app.app_context():
    db.create_all()


import src.routes


