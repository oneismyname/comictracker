from datetime import datetime
import requests
from flask import render_template, flash, redirect, url_for, request, jsonify
from flask_login import current_user, login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
import smtplib
import os
from sqlalchemy import func, text

from src import app, login_manager
from .database import User, db, Comic, Mapping, Schedule, Checking
from .forms import RegisterForm, LoginForm, AddForm, SearchForm


my_email = os.environ.get("email")
password = os.environ.get("password")


def take_data(start_day, end_day):
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
        'filter': f"publishDate >= '{start_day}' && publishDate <= '{end_day}'",
        'sort': '+publishDate,+name,-edition',
        'expand': 'title, publisher',
    }

    response = requests.get('https://pb.tana.moe/api/collections/book_detailed/records', params=params,
                            headers=headers)
    data_test = response.json()
    return data_test


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
        data_test = take_data(form.date_start.data, form.date_end.data)
        for data in data_test['items']:
            with app.app_context():
                name = data["name"].split(" - ")[0]
                if data['baseCover'] == []:
                    img = "https://img.freepik.com/free-vector/flat-comic-style-background_23-2148882944.jpg?w=1380&t=st=1693394293~exp=1693394893~hmac=3dcc1ace1c32ce8b99a53c456a35a0160017b9893d8c078e34d29bc3d5d1d1bf"
                else:
                    img = f"https://image.tana.moe/unsafe/320x0/filters:quality(90)/{data['collectionId']}/{data['id']}/{data['baseCover'][0]}"
                result = db.session.execute(db.Select(Comic).where(Comic.name == name)).scalars().all()
                if result:
                    pass
                else:
                    new_comic = Comic(
                        name=name,
                        img_cover=img)
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


@app.route("/follow", methods=["POST"])
def follow():
    data = request.get_json()
    comic_id = data.get("comicId")
    if data.get("Follow"):
        with app.app_context():
            new_follow = Mapping(
                user_id = current_user.id,
                comic_id = comic_id
            )
            db.session.add(new_follow)
            db.session.commit()
        response = {"message": "Follow successfully!", "buttonText": "UnFollow"}
    else:
        with app.app_context():
            query = Mapping.query.filter(Mapping.comic_id == comic_id, Mapping.user_id == current_user.id).first()
            db.session.delete(query)
            db.session.commit()
        response = {"message": "UnFollow successfully!", "buttonText": "Follow"}
    return jsonify(response)


@app.route("/profile")
def profile():
    with app.app_context():
        query = db.session.query(Comic).join(Mapping).filter(Mapping.user_id == current_user.id).all()
        return render_template("profile.html", list = query, user=current_user)


@app.route("/update", methods=["GET", "POST"])
def update():
    form = AddForm()
    if form.validate_on_submit():
        data_test = take_data(form.date_start.data, form.date_end.data)
        for data in data_test['items']:
            with app.app_context():
                name = data["name"].split(" - ")[0]
                try:
                    volume = data["name"].split(" - ")[-1]
                except IndexError:
                    volume = "Tập 1"
                if data["digital"]:
                    edition = "Digital"
                elif data['edition'] == "":
                    edition = "Normal"
                else:
                    edition = data["edition"]
                if data['baseCover'] == []:
                    img = "https://img.freepik.com/free-vector/flat-comic-style-background_23-2148882944.jpg?w=1380&t=st=1693394293~exp=1693394893~hmac=3dcc1ace1c32ce8b99a53c456a35a0160017b9893d8c078e34d29bc3d5d1d1bf"
                else:
                    img = f"https://image.tana.moe/unsafe/320x0/filters:quality(90)/{data['collectionId']}/{data['id']}/{data['baseCover'][0]}"
                datetime_obj = datetime.strptime(data['publishDate'], "%Y-%m-%d %H:%M:%S.%fZ")
                query = Comic.query.filter(Comic.name.like(name)).first()
                result = Schedule.query.filter(
                    Schedule.name == name, Schedule.release_date == datetime_obj.date(), Schedule.edition == edition, Schedule.volume == volume).all()
                if result:
                    pass
                else:
                    new_comic = Schedule(
                        name=name,
                        comic_id= query.id,
                        volume= volume,
                        edition=edition,
                        price=data["price"],
                        release_date=datetime_obj.date(),
                        publisher=data["expand"]["publisher"]["name"],
                        img=img
                    )
                    db.session.add(new_comic)
                    db.session.commit()
        return redirect(url_for("home"))
    return render_template('update.html', user=current_user, form=form)


@app.route("/autocomplete", methods=["GET"])
def get_suggestions():
    user_input = request.args.get('text')
    suggestions = db.session.query(Comic.name).filter(
        Comic.name.ilike(f'%{user_input}%')
    ).all()
    suggestions = sorted(list(set([item[0] for item in suggestions])))
    db.session.close()
    return jsonify(suggestions)


@app.route("/inform")
def inform():
    with app.app_context():
        comics = db.session.query(Comic).join(Mapping).filter(Mapping.user_id == current_user.id).all()
        dict = {}
        for comic in comics:
            schedule = db.session.query(Schedule).filter(Schedule.name == comic.name, Schedule.release_date == datetime.today().date()).all()
            for item in schedule:
                new_obj = {item.name: [item.price, item.volume]}
                dict.update(new_obj)
        msg = ""
        for key, values in dict.items():
            para = f"{key} - volume {values[1].split(' ')[-1]} is released today {datetime.today().date()}. Price: {values[0]}\n"
            msg += para
        if msg == "":
            flash("No comic release today")
            return redirect(url_for('home'))
        else:
            with smtplib.SMTP("smtp.gmail.com") as connection:
                connection.starttls()
                connection.login(user=my_email, password=password)
                connection.sendmail(
                    from_addr=my_email,
                    to_addrs=current_user.email,
                    msg=f"Subject: BUY NOW\n\n{msg}"
                )
            return redirect(url_for('home'))


@app.route("/schedule", methods=["GET","POST"])
def schedule():
    if request.method == "POST":
        selected_month = request.form['selected_month']
        selected_year = request.form['selected_year']
        selected_date = datetime.strptime(f"{selected_year}-{selected_month}", "%Y-%m")
        strip_date = datetime.strftime(selected_date, "%Y-%m")
        query_1 = Schedule.query.filter(func.strftime('%Y-%m', Schedule.release_date) == strip_date).all()
        query_2 = db.session.query(Schedule.release_date).filter(
            func.strftime('%Y-%m', Schedule.release_date) == strip_date).distinct().all()
        dict = {}
        for item in query_2:
            query_3 = Schedule.query.filter(Schedule.release_date == item.release_date).all()
            new_dict = {item.release_date: query_3}
            dict.update(new_dict)
        bought_or_not = {}
        for comic in query_1:
            result = Checking.query.filter(Checking.schedule_id == comic.id, Checking.user_id == current_user.id).all()
            if result:
                new_element = {comic.id: "TRUE"}
                bought_or_not.update(new_element)
            else:
                new_element = {comic.id: "FALSE"}
                bought_or_not.update(new_element)
        return render_template("schedule.html", user=current_user, dict_1= dict, dict_2= bought_or_not)
    query_1 = Schedule.query.filter(func.strftime('%Y-%m', Schedule.release_date) == datetime.today().strftime('%Y-%m')).all()
    query_2 = db.session.query(Schedule.release_date).filter(func.strftime('%Y-%m', Schedule.release_date) == datetime.today().strftime('%Y-%m')).distinct().all()
    dict = {}
    for item in query_2:
        query_3 = Schedule.query.filter(Schedule.release_date == item.release_date).all()
        new_dict = {item.release_date : query_3}
        dict.update(new_dict)
    bought_or_not = {}
    for comic in query_1:
        result = Checking.query.filter(Checking.schedule_id == comic.id, Checking.user_id == current_user.id).all()
        if result:
            new_element = {comic.id: "TRUE"}
            bought_or_not.update(new_element)
        else:
            new_element = {comic.id: "FALSE"}
            bought_or_not.update(new_element)
    return render_template("schedule.html", user=current_user, dict_1= dict, dict_2= bought_or_not)


@app.route("/check", methods=["POST"])
def check():
    data = request.get_json()
    comic_id = data.get("comicId")
    print(data.get("Check"))
    if data.get("Check"):
        with app.app_context():
            query = Schedule.query.filter(Schedule.id == comic_id).first()
            new = Checking(
                user_id=current_user.id,
                schedule_id=comic_id,
                bought=True,
                price=query.price)
            db.session.add(new)
            db.session.commit()
        response = {"message": "Check successfully!", "buttonText": "UnCheck"}
    else:
        with app.app_context():
            query = Checking.query.filter(Checking.schedule_id == comic_id, Checking.user_id == current_user.id).first()
            db.session.delete(query)
            db.session.commit()
        response = {"message": "UnCheck successfully!", "buttonText": "Check"}

    return jsonify(response)


@app.route("/finance")
def finance():
    result = db.session.query(
        func.strftime('%Y-%m', Schedule.release_date).label('month'),
        func.sum(Checking.price).label('total_amount')
    ).join(Checking).filter(
        Checking.user_id == current_user.id,
        Checking.bought == True
    ).group_by('month').order_by('month').all()
    month = [item[0] for item in result]
    amount = [item[1] for item in result]
    return render_template('finance.html', user=current_user, month=month, amount=amount)
