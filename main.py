from flask import Flask, render_template, flash, redirect, url_for
from forms import RegisterForm, LoginForm
from flask_bootstrap import Bootstrap5
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, logout_user, LoginManager, current_user


app = Flask(__name__)
app.config['SECRET_KEY'] = "thisismysecretkey"
Bootstrap5(app)
# create table
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///webdata.db'
db = SQLAlchemy(app)
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    email = db.Column(db.String(1000), nullable=False)
    password = db.Column(db.String(1000), nullable=False)


with app.app_context():
    db.create_all()




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
                        name= form.name.data,
                        email = form.email.data,
                        password = secure_password
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


if __name__ == "__main__":
    app.run(debug=True)