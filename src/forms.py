from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email

class RegisterForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    confirm_password = PasswordField("Confirm Password", validators=[DataRequired()])
    submit = SubmitField("Sign Up")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Log in")


class AddForm(FlaskForm):
    date_start = StringField("Date Start", validators=[DataRequired()])
    date_end = StringField("Date End", validators=[DataRequired()])
    submit = SubmitField("Add")


class SearchForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    submit = SubmitField("Search")