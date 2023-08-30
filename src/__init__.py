from flask import Flask
from flask_bootstrap import Bootstrap5
from flask_login import LoginManager

import src.local_func
app = Flask(__name__)
app.config['SECRET_KEY'] = "thisismysecretkey"
Bootstrap5(app)

login_manager = LoginManager()
login_manager.init_app(app)

# create table
from src.database import db
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///webdata.db'
db.init_app(app)


with app.app_context():
    db.create_all()


import src.routes


