from flask import render_template, flash, redirect, url_for
from src import app, login_manager
from .database import User, db, Comic, Mapping
from .forms import RegisterForm, LoginForm, AddForm, SearchForm
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import current_user, login_user, logout_user
import requests
from datetime import datetime


@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


@app.route("/")
def home():
    return render_template("index.html", user=current_user)


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        result = db.session.execute(db.select(User).where(User.email == form.email.data)).scalar()
        if result:
            flash("Your email is registered")
        else:
            if form.password.data == form.confirm_password.data:
                secure_password = generate_password_hash(form.password.data, method="pbkdf2:sha256", salt_length=8)
                with app.app_context():
                    new_user = User(
                        name=form.name.data,
                        email=form.email.data,
                        password=secure_password
                    )
                    db.session.add(new_user)
                    db.session.commit()
                    return redirect(url_for('home'))
            else:
                flash("Your password is not match")
    return render_template("register.html", form=form, user=current_user)


@app.route("/login", methods=["GET","POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        result = db.session.execute(db.select(User).where(User.email == form.email.data)).scalar()
        if result:
            if check_password_hash(result.password, form.password.data):
                login_user(result)
                return redirect(url_for('home'))
            else:
                flash("Your password is not correct")
        else:
            flash("Your email is not correct")
    return render_template('login.html', form=form, user=current_user)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route("/add", methods=["GET", "POST"])
def add():
    form = AddForm()
    if form.validate_on_submit():
        headers = {
            'authority': 'manga.glhf.vn',
            'accept': '*/*',
            'accept-language': 'vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5',
            'referer': 'https://manga.glhf.vn/',
            'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
        }

        response = requests.get(
            f'https://manga.glhf.vn/api/releases?start={form.date_start.data}&end={form.date_end.data}&order=ascending&',
            headers=headers,
        )
        data_test = response.json()
        for data in data_test:
            with app.app_context():
                info = data["entries"]
                for item in info:
                    name = item["name"].split(" - ")[0]
                    result = db.session.execute(db.Select(Comic).where(Comic.name == name)).scalars().all()
                    if result:
                        pass
                    else:
                        new_comic = Comic(
                            name=name)
                        db.session.add(new_comic)
                        db.session.commit()
        return redirect(url_for("home"))
    return render_template('add.html', user=current_user, form=form)


@app.route("/tracking", methods=["GET", "POST"])
def tracking():
    form = SearchForm()
    if form.validate_on_submit():
        if current_user.is_authenticated:
            with app.app_context():
                search = form.name.data
                result = db.session.query(Comic).where(Comic.name.ilike(f'%{search}%')).all()
                return render_template('tracking.html', form=form, user=current_user, comics=result)
        else:
            flash("You have to login to add")
    return render_template("tracking.html", form=form, user=current_user)


@app.route("/follow/<index>", methods=["GET", "POST"])
def follow(index):
    with app.app_context():
        result = db.session.execute(db.Select(Mapping).where(Mapping.comic_id == index and Mapping.user_id == current_user.id)).scalars().all()
        if result:
            flash("you already follow this comic")
            return redirect(url_for('tracking'))
        else:
            new_follow = Mapping(
                user_id = current_user.id,
                comic_id = index
            )
            db.session.add(new_follow)
            db.session.commit()
            return redirect(url_for('tracking'))