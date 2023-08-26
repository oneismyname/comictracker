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
            'authority': 'pb.tana.moe',
            'accept': '*/*',
            'accept-language': 'en-US',
            'content-type': 'application/json',
            'origin': 'https://tana.moe',
            'referer': 'https://tana.moe/',
            'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
        }

        params = {
            'page': '1',
            'perPage': '500',
            'skipTotal': '1',
            'filter': f"publishDate >= '{form.date_start.data}' && publishDate <= '{form.date_end.data}'",
            'sort': '+publishDate,+name,-edition',
            'expand': 'title, publisher',
        }

        response = requests.get('https://pb.tana.moe/api/collections/book_detailed/records', params=params,
                                headers=headers)
        data_test = response.json()
        for data in data_test['items']:
            with app.app_context():
                name = data["name"].split(" - ")[0]
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
                follow_or_not = {}
                for comic in result:
                    query = Mapping.query.filter(Mapping.comic_id == comic.id, Mapping.user_id == current_user.id).all()
                    if query:
                        new_element = {comic.id: "TRUE"}
                        follow_or_not.update(new_element)
                    else:
                        new_element = {comic.id: "FALSE"}
                        follow_or_not.update(new_element)
                return render_template('tracking.html', form=form, user=current_user, comics=result, dict = follow_or_not)
        else:
            flash("You have to login to add")
    return render_template("tracking.html", form=form, user=current_user)


@app.route("/follow/<index>")
def follow(index):
    with app.app_context():
        new_follow = Mapping(
            user_id = current_user.id,
            comic_id = index
        )
        db.session.add(new_follow)
        db.session.commit()
        flash("Successfully follow this comic")
        return redirect(url_for('tracking'))


@app.route("/unfollow/<index>")
def unfollow(index):
    with app.app_context():
        query = Mapping.query.filter(Mapping.comic_id == index, Mapping.user_id == current_user.id).first()
        db.session.delete(query)
        db.session.commit()
        flash("Successfully unfollow this comic")
        return redirect(url_for('tracking'))


@app.route("/profile")
def profile():
    with app.app_context():
        query = db.session.query(Comic).join(Mapping).filter(Mapping.user_id == current_user.id).all()
        print(query)
        return render_template("profile.html", list = query, user=current_user)