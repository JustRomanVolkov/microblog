# -*- coding: utf-8 -*-

# Стандартные библиотеки Python

# Библиотеки третьей стороны
from flask_babel import _, lazy_gettext as _l
from flask_wtf import FlaskForm
import sqlalchemy as sa
from wtforms import BooleanField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError

# Собственные модули
from app import db
from app.models import User


class LoginForm(FlaskForm):
    """
    Класс формы для входа пользователя.

    Attributes:
        username (StringField): Поле для ввода имени пользователя.
        password (PasswordField): Поле для ввода пароля.
        remember_me (BooleanField): Флажок "Запомнить меня".
        submit (SubmitField): Кнопка "Войти".
    """
    username: StringField = StringField(_l('Имя пользователя'), validators=[DataRequired()])
    password: PasswordField = PasswordField(_l('Пароль'), validators=[DataRequired()])
    remember_me: BooleanField = BooleanField(_l('Запомни меня'))
    submit: SubmitField = SubmitField(_l('Войти'))


class RegistrationForm(FlaskForm):
    """
    Класс формы регистрации пользователя.

    Attributes:
        username (StringField): Поле для ввода имени пользователя.
        email (StringField): Поле для ввода почты.
        password (PasswordField): Поле для ввода пароля.
        password2 (PasswordField): Поле для повторного ввода пароля.
        submit (SubmitField): Кнопка "Регистрация".
    """
    username: StringField = StringField(_l('Имя пользователя'), validators=[DataRequired()])
    email: StringField = StringField(_l('Почта'), validators=[DataRequired(), Email()])
    password: PasswordField = PasswordField(_l('Пароль'), validators=[DataRequired()])
    password2: PasswordField = PasswordField(_l('Повтор пароля'),
                                             validators=[DataRequired(), EqualTo('password')])
    submit: SubmitField = SubmitField(_l('Регистрация'))

    def validate_username(self, username):
        user = db.session.scalar(sa.select(User).where(
            User.username == username.data))
        if user is not None:
            raise ValidationError(_l('Используйте другое имя.'))

    def validate_email(self, email):
        user = db.session.scalar(sa.select(User).where(
            User.email == email.data))
        if user is not None:
            raise ValidationError(_l('Используйте другую почту.'))


class ResetPasswordRequestForm(FlaskForm):
    """
    Форма запроса сброса пароля.

    Attributes:
        email (StringField): Поле для ввода email-адреса пользователя. Обязательное поле.
        submit (SubmitField): Кнопка для отправки запроса сброса пароля.
    """
    email = StringField(_l('Email'), validators=[DataRequired(), Email()])
    submit = SubmitField(_l('Запрос сброса пароля'))


class ResetPasswordForm(FlaskForm):
    """
    Форма для сброса пароля пользователя.

    Attributes:
        password (PasswordField): Поле для ввода нового пароля.
        password2 (PasswordField): Поле для повторного ввода пароля с проверкой на совпадение.
        submit (SubmitField): Кнопка для отправки запроса сброса пароля.

    """
    password = PasswordField('Пароль', validators=[DataRequired()])
    password2 = PasswordField(_l(
        'Повторите пароль'), validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField(_l('Запрос сброса пароля'))
