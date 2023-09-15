from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Email, Length

class RegisterForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(min=6, max=20)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    confirm_password = PasswordField("Confirm Password", validators=[DataRequired()])
    submit = SubmitField("Sign Up")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember Me")
    submit = SubmitField("Log in")


class AddForm(FlaskForm):
    date_start = StringField("Date Start", validators=[DataRequired()])
    date_end = StringField("Date End", validators=[DataRequired()])
    submit = SubmitField("Add")


class SearchForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    submit = SubmitField("Search")


class ForgotForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    new_password = PasswordField("New Password", validators=[DataRequired()])
    confirm_password = PasswordField("Confirm Password", validators=[DataRequired()])
    submit = SubmitField("Confirm")


class UpdateForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(min=6, max=20)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    avatar = FileField("Update Avatar", validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField("Update")


class CommentForm(FlaskForm):
    content = TextAreaField("Comment", validators=[DataRequired()])
    submit = SubmitField("Comment")


class EditForm(FlaskForm):
    edit = TextAreaField("Edit", validators=[DataRequired()])
    submit = SubmitField("Edit")


class ReplyForm(FlaskForm):
    reply = TextAreaField("Edit", validators=[DataRequired()])
    submit = SubmitField("Reply")
