from datetime import datetime
import requests
from flask import render_template, flash, redirect, url_for, request, jsonify
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
import smtplib
import os
from sqlalchemy import func, select
from google.cloud import storage
import secrets

from src import app, login_manager
from .database import User, db, Comic, Mapping, Schedule, Checking, Comment
from .forms import RegisterForm, LoginForm, AddForm, SearchForm, ForgotForm, UpdateForm, CommentForm, EditForm, ReplyForm


my_email = os.environ.get("email")
password = os.environ.get("password")
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'comictracker-7b0ea082fc63.json'


def take_data(start_day, end_day):
    headers = {
        'Content-Type': 'application/json'
    }

    params = {
        'page': '1',
        'perPage': '500',
        'skipTotal': '1',
        'filter': f"publishDate >= '{start_day}' && publishDate <= '{end_day}'",
        'sort': '+publishDate,+name,-edition',
        'expand': 'title, publisher',
    }

    response = requests.get('https://pb.tana.moe/api/collections/book_detailed/records', params=params, headers=headers)
    data_test = response.json()
    return data_test


def update_comic_schedule(data_test):
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
                Schedule.name == name, Schedule.release_date == datetime_obj.date(), Schedule.edition == edition,
                Schedule.volume == volume).first()
            if result:
                if data['baseCover'] != []:
                    result.img = f"https://image.tana.moe/unsafe/320x0/filters:quality(90)/{data['collectionId']}/{data['id']}/{data['baseCover'][0]}"
                    db.session.commit()
                else:
                    continue
            else:
                new_comic = Schedule(
                    name=name,
                    comic_id=query.id,
                    volume=volume,
                    edition=edition,
                    price=data["price"],
                    release_date=datetime_obj.date(),
                    publisher=data["expand"]["publisher"]["name"],
                    img=img
                )
                db.session.add(new_comic)
                db.session.commit()


def month_schedule(query):
    dict = {}
    for item in query:
        query_3 = Schedule.query.filter(Schedule.release_date == item.release_date).all()
        new_dict = {item.release_date: query_3}
        dict.update(new_dict)
    return dict


def bought_or_not(dict):
    bought_or_not = {}
    for value in dict.values():
        for comic in value:
            result = Checking.query.filter(Checking.schedule_id == comic.id, Checking.user_id == current_user.id).all()
            if result:
                new_element = {comic.id: "TRUE"}
                bought_or_not.update(new_element)
            else:
                new_element = {comic.id: "FALSE"}
                bought_or_not.update(new_element)
    return bought_or_not


def selected_month_shedule():
    selected_month = request.form['selected_month']
    selected_year = request.form['selected_year']
    selected_date = datetime.strptime(f"{selected_year}-{selected_month}", "%Y-%m")
    strip_date = datetime.strftime(selected_date, "%Y-%m")
    query = db.session.query(Schedule.release_date).filter(
        func.strftime('%Y-%m', Schedule.release_date) == strip_date).distinct().order_by(Schedule.release_date).all()
    return query


def set_avatar(avatar):
    random_hex = secrets.token_hex(8)
    filename = random_hex + avatar.filename
    uploaded_file = avatar
    content_type = uploaded_file.content_type
    gcs_client = storage.Client()
    storage_bucket = gcs_client.get_bucket('comictrack_avatar')
    try:
        storage_bucket.blob(f'{current_user.avatar.split("/")[-1]}').delete()
    except:
        blob = storage_bucket.blob(filename)
        blob.upload_from_string(uploaded_file.read(), content_type=content_type)
        blob.make_public()
        url = blob.public_url
        current_user.avatar = url
        db.session.commit()
    else:
        blob = storage_bucket.blob(filename)
        blob.upload_from_string(uploaded_file.read(), content_type=content_type)
        blob.make_public()
        url = blob.public_url
        current_user.avatar = url
        db.session.commit()


def calc_money(new_month):
    month_set = {}
    for item in new_month:
        month_set[item[0]] = []
    for item in new_month:
        month_set[item[0]].append(item[2])
    publish_set = {}
    for item in new_month:
        publish_set[item[1]] = []
    for item in new_month:
        publish_set[item[1]].append(item[2])
    month = [item for item in month_set.keys()]
    amount = [sum(item) for item in month_set.values()]
    publisher = [item for item in publish_set.keys()]
    publisher_amount = [sum(item) for item in publish_set.values()]
    year_amount = sum(amount)
    formatted_year_amount = f"{year_amount:,}"
    return month,amount, publisher, publisher_amount, formatted_year_amount

@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


@app.route("/")
def home():
    query = Schedule.query.filter(Schedule.img != "https://img.freepik.com/free-vector/flat-comic-style-background_23-2148882944.jpg?w=1380&t=st=1693394293~exp=1693394893~hmac=3dcc1ace1c32ce8b99a53c456a35a0160017b9893d8c078e34d29bc3d5d1d1bf").order_by(Schedule.release_date.desc()).limit(6)
    return render_template("index.html", user=current_user, comics=query)


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        result = db.session.execute(db.select(User).where(User.email == form.email.data)).scalar()
        if result:
            flash("Your email is registered", 'danger')
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
                    return redirect(url_for('login'))
            else:
                flash("Your password is not match", 'danger')
    return render_template("register.html", form=form, user=current_user)


@app.route("/login", methods=["GET","POST"])
def login():
    form = LoginForm()
    if request.method == "POST":
        result = db.session.execute(db.select(User).where(User.email == form.email.data)).scalar()
        if result:
            if check_password_hash(result.password, form.password.data):
                login_user(result, remember=form.remember.data)
                return redirect(url_for('home'))
            else:
                flash("Your password is not correct", 'danger')
        else:
            flash("Your email is not correct", 'danger')
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
                result = Comic.query.filter(Comic.name == name).first()
                if result:
                    if data["baseCover"] != []:
                        result.img_cover = f"https://image.tana.moe/unsafe/320x0/filters:quality(90)/{data['collectionId']}/{data['id']}/{data['baseCover'][0]}"
                    else:
                        continue
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
            para = "Follow your favorite comics and receive notifications on release date"
            with app.app_context():
                search = form.name.data
                result = db.session.query(Comic).where(Comic.name.ilike(f'%{search}%')).all()
                if result:
                    follow_or_not = {}
                    for comic in result:
                        query = Mapping.query.filter(Mapping.comic_id == comic.id, Mapping.user_id == current_user.id).all()
                        if query:
                            new_element = {comic.id: "TRUE"}
                            follow_or_not.update(new_element)
                        else:
                            new_element = {comic.id: "FALSE"}
                            follow_or_not.update(new_element)
                    return render_template('tracking.html', form=form, user=current_user, comics=result, dict = follow_or_not, search="true", para=para)
                else:
                    flash("The comic you are looking for does not exist.", 'info')
        else:
            flash("You have to login to add", 'danger')
    page = request.args.get('page', 1, type=int)
    result = Comic.query.order_by(Comic.name).paginate(page=page ,per_page=30)
    if current_user.is_authenticated:
        follow_or_not = {}
        para = "Follow your favorite comics and receive notifications on release date"
        for comic in result.items:
            query = Mapping.query.filter(Mapping.comic_id == comic.id, Mapping.user_id == current_user.id).all()
            if query:
                new_element = {comic.id: "TRUE"}
                follow_or_not.update(new_element)
            else:
                new_element = {comic.id: "FALSE"}
                follow_or_not.update(new_element)
        return render_template("tracking.html", form=form, user=current_user, comic=result, search="false",
                               dict=follow_or_not, para=para)
    para = "Log in to follow your favorite comic books"
    return render_template("tracking.html", form=form, user=current_user, comic=result, search="false", para=para)


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
        response = {"buttonText": "UnFollow"}
    else:
        with app.app_context():
            query = Mapping.query.filter(Mapping.comic_id == comic_id, Mapping.user_id == current_user.id).first()
            db.session.delete(query)
            db.session.commit()
        response = {"buttonText": "Follow"}
    return jsonify(response)


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    form = UpdateForm(
        name= current_user.name,
        email= current_user.email
    )
    if form.validate_on_submit():
        if form.avatar.data:
            set_avatar(form.avatar.data)
        current_user.name = form.name.data
        current_user.email = form.email.data
        db.session.commit()
        flash("Your account has been updated", 'success')
        return redirect(url_for('profile'))
    query = db.session.query(Comic).join(Mapping).filter(Mapping.user_id == current_user.id).all()
    return render_template("profile.html", list = query, user=current_user, form=form)


@app.route("/update", methods=["GET", "POST"])
def update():
    form = AddForm()
    if form.validate_on_submit():
        data_test = take_data(form.date_start.data, form.date_end.data)
        update_comic_schedule(data_test)
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
        dict = {}
        query = select(Schedule.name, Schedule.volume, Schedule.edition,Schedule.price, User.email).join(Mapping, Mapping.comic_id == Schedule.comic_id).join(User, User.id == Mapping.user_id).where(Schedule.comic_id == Mapping.comic_id, User.id == Mapping.user_id, Schedule.release_date == datetime.today().date())
        comics_release_today = list(db.session.execute(query).all())
        for comic in comics_release_today:
            dict[comic.email] = []
        for comic in comics_release_today:
            dict[comic.email].append([comic.name, comic.edition, comic.volume, comic.price])
        for email, comics in dict.items():
            msg = ""
            for comic in comics:
                msg += f"{comic[0]} {comic[1]} edition is released today ({datetime.today().date()}). Price {comic[3]}\n"
            if msg == "":
                flash("No comic that you followed release today", 'info')
            else:
                with smtplib.SMTP("smtp.gmail.com") as connection:
                    connection.starttls()
                    connection.login(user=my_email, password=password)
                    connection.sendmail(
                        from_addr=my_email,
                        to_addrs=email,
                        msg=f"Subject: BUY NOW\n\n{msg}"
                )
    return redirect(url_for('home'))


@app.route("/schedule", methods=["GET","POST"])
def schedule():
    if current_user.is_authenticated:
        if request.method == "POST":
            query = selected_month_shedule()
            schedule = month_schedule(query)
            list_check = bought_or_not(schedule)
            current_month = f"{request.form['selected_month']}-{request.form['selected_year']}"
            return render_template("schedule.html", user=current_user, dict_1= schedule, dict_2= list_check,
                                   current_month=current_month)
        query = db.session.query(Schedule.release_date).\
            filter(func.strftime('%Y-%m', Schedule.release_date) == datetime.today().
                   strftime('%Y-%m')).distinct().order_by(Schedule.release_date).all()
        schedule = month_schedule(query)
        list_check = bought_or_not(schedule)
        current_month = datetime.today().strftime('%m-%Y')
        return render_template("schedule.html", user=current_user, dict_1= schedule, dict_2= list_check,
                               current_month=current_month)
    else:
        if request.method == "POST":
            query = selected_month_shedule()
            schedule = month_schedule(query)
            current_month = f"{request.form['selected_month']}-{request.form['selected_year']}"
            return render_template("schedule.html", user=current_user, dict_1= schedule, dict_2= {}, current_month=current_month)
        else:
            current_month = datetime.today().strftime('%m-%Y')
            query = db.session.query(Schedule.release_date).filter(
                func.strftime('%Y-%m', Schedule.release_date) == datetime.today().strftime('%Y-%m')).distinct().order_by(Schedule.release_date).all()
            schedule = month_schedule(query)
            return render_template("schedule.html", user=current_user, dict_1=schedule, dict_2={}, current_month=current_month)


@app.route("/check", methods=["POST"])
def check():
    data = request.get_json()
    comic_id = data.get("comicId")
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
        response = {"buttonText": "UnCheck"}
    else:
        with app.app_context():
            query = Checking.query.filter(Checking.schedule_id == comic_id, Checking.user_id == current_user.id).first()
            db.session.delete(query)
            db.session.commit()
        response = {"buttonText": "Check"}

    return jsonify(response)


@app.route("/finance", methods=["GET", "POST"])
def finance():
    if current_user.is_authenticated:
        result = db.session.query(
            func.strftime('%Y-%m', Schedule.release_date).label('month'),
            Schedule.publisher,
            func.sum(Checking.price).label('total_amount')
        ).join(Checking).filter(
            Checking.user_id == current_user.id,
            Checking.bought == True
        ).group_by('month', Schedule.publisher).order_by('month').all()
        if request.method == "POST":
            new_month = []
            for item in result:
                if item[0].strip("-")[0:4] == request.form["selected_year"]:
                    new_month.append(item)
            month, amount, publisher, publisher_amount, formatted_year_amount = calc_money(new_month)
            selected_year = request.form["selected_year"]
        else:
            new_month = []
            for item in result:
                if item[0].strip("-")[0:4] == datetime.strftime(datetime.today(),'%Y'):
                    new_month.append(item)
            month,amount, publisher, publisher_amount, formatted_year_amount = calc_money(new_month)
            selected_year = datetime.strftime(datetime.today(), '%Y')
        total_amount = sum([item[2] for item in result])
        formatted_total_amount = f"{total_amount:,}"
        return render_template('finance.html',
                               user=current_user, month=month, amount=amount,
                               total_amount=formatted_total_amount, year_amount=formatted_year_amount,
                               selected_year=selected_year, publisher=publisher, publisher_amount=publisher_amount)
    else:
        return render_template('intro.html', user=current_user)


@app.route("/forgot", methods=["GET", "POST"])
def forgot_password():
    form = ForgotForm()
    if form.validate_on_submit():
        with app.app_context():
            query = User.query.filter(User.name == form.name.data, User.email == form.email.data).first()
            if query:
                if form.new_password.data == form.confirm_password.data:
                    query.password = generate_password_hash(form.new_password.data, method="pbkdf2:sha256", salt_length=8)
                    db.session.commit()
                    flash("Successfully update your password", "success")
                    return redirect(url_for('login'))
                else:
                    flash("Your password is not match", "info")
            else:
                flash("Your email or name is not correct", "info")
    return render_template("forgot.html", form=form, user= current_user)


@app.route("/info/<index>", methods=["GET", "POST"])
def info(index):
    if current_user.is_authenticated:
        first_comic = db.session.query(Schedule).filter(Schedule.comic_id == index).order_by(Schedule.release_date).first()
        select = request.args.get("select", "all", type=str)
        if select == "all" :
            query = db.session.query(Schedule).filter(Schedule.comic_id == index).order_by(Schedule.release_date).all()
        elif select == "purchased":
            query = db.session.query(Schedule).join(Checking).filter(Schedule.comic_id == index, Checking.bought == True, Checking.user_id == current_user.id).order_by(Schedule.release_date).all()
        else:
            query1 = db.session.query(Schedule).filter(Schedule.comic_id == index).order_by(Schedule.release_date).all()
            query2 = db.session.query(Schedule).join(Checking).filter(Schedule.comic_id == index,
                                                                     Checking.bought == True,
                                                                     Checking.user_id == current_user.id).order_by(
                Schedule.release_date).all()
            result = list(set(query1) - set(query2))
            query = sorted(result, key=lambda schedule: schedule.release_date)
        list_check = {}
        for comic in query:
            with app.app_context():
                check = Checking.query.filter(Checking.schedule_id == comic.id, Checking.user_id == current_user.id).all()
                for item in check:
                    if item.bought == True:
                        add = {comic.id: "TRUE"}
                        list_check.update(add)
                    else:
                        add = {comic.id: "FALSE"}
                        list_check.update(add)
        follow = Mapping.query.filter(Mapping.comic_id == index, Mapping.user_id == current_user.id).first()
        if follow:
            follow_check = "TRUE"
        else:
            follow_check = "FALSE"
        form = CommentForm()
        if form.validate_on_submit():
            new_comment = Comment(
                user_id = current_user.id,
                comic_id = index,
                time_post= datetime.today(),
                content= form.content.data)
            new_comment.save()
            flash("Successfully post comment", 'success')
            return redirect(url_for('info', index=index))
        edit_form = EditForm()
        reply_form = ReplyForm()
        page = request.args.get('page', 1, type=int)
        comments = Comment.query.filter(Comment.comic_id == index, Comment.parent_id == None).order_by(Comment.time_post.desc()).paginate(page=page,
                                                                                                       per_page=5)
        return render_template('info.html', comic=query, user=current_user, dict = list_check,
                               follow_check=follow_check,
                               index=index,
                               first=first_comic,
                               form=form,
                               comments=comments,
                               edit_form=edit_form,
                               reply_form=reply_form)
    else:
        form = CommentForm()
        edit_form = EditForm()
        reply_form =ReplyForm()
        if form.validate_on_submit():
            flash("Login to leave a comment", 'danger')
        page = request.args.get('page', 1, type=int)
        comments = Comment.query.filter(Comment.comic_id == index).order_by(Comment.time_post).paginate(page=page,
                                                                                                       per_page=5)
        query = db.session.query(Schedule).filter(Schedule.comic_id == index).order_by(Schedule.release_date).all()
        return render_template('info.html', comic=query, user=current_user, dict={}, index=index, first=query[0],
                               form=form, comments=comments, edit_form=edit_form, reply_form=reply_form)


def delete_nested_comments(comments):
    for reply in comments.replies:
        delete_nested_comments(reply)
    db.session.delete(comments)
    db.session.commit()


@app.route("/delete/comment/<index>/<comic_id>")
def delete_comment(index, comic_id):
    comment = Comment.query.filter(Comment.id == index).first()
    delete_nested_comments(comment)
    return redirect(url_for('info', index=comic_id))


@app.route("/edit/<index>/<comic_id>", methods=["POST"])
def edit(index, comic_id):
    comment = Comment.query.filter(Comment.id == index).first()
    comment.content = request.form.get('edit')
    db.session.commit()
    return redirect(url_for('info', index=comic_id))


@app.route("/reply/<index>/<comic_id>", methods=["POST"])
def reply(index, comic_id):
    if current_user.is_authenticated:
        reply_comment = Comment(
            user_id=current_user.id,
            comic_id=comic_id,
            time_post=datetime.today(),
            content= request.form.get('reply'),
            parent_id=index,
        )
        reply_comment.save()
        return redirect(url_for('info', index=comic_id))
    else:
        flash("Login to leave a reply comment", 'danger')
        return redirect(url_for('info', index=comic_id))

