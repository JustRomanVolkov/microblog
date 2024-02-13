# -*- coding: utf-8 -*-

# Библиотеки третьей стороны
from flask import request
from flask_babel import _, lazy_gettext as _l
from flask_wtf import FlaskForm
import sqlalchemy as sa
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, ValidationError

# Собственные модули
from app import db
from app.models import User


class EditProfileForm(FlaskForm):
    """
    Класс формы редактирования профиля.

    Attributes:
        username (StringField): Поле изменения имени пользователя.
        about_me (TextAreaField): Поле изменения описания информации о пользователе.
        submit (SubmitField): Кнопка отправки данных формы.

    Methods:
        __init__(self, original_username, *args, **kwargs):
            Конструктор класса формы.

        validate_username(self, username: StringField):
            Метод для валидации имени пользователя.
    """
    username: StringField = StringField(_l('Имя пользователя'), validators=[DataRequired()])
    about_me: TextAreaField = TextAreaField(_l('Обо мне'), validators=[Length(min=0, max=140)])
    submit: SubmitField = SubmitField(_l('Принять изменения'))

    def __init__(self, original_username: str, *args, **kwargs):
        """
        Инициализирует форму редактирования профиля.

        Args:
            original_username (str): Оригинальное имя пользователя.
            *args: Позиционные аргументы FlaskForm.
            **kwargs: Именованные аргументы FlaskForm.
        """
        super().__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username: StringField):
        """
        Проверяет уникальность имени пользователя.

        Args:
            username (StringField): Поле с введенным именем пользователя.

        Raises:
            ValidationError: Вызывается, если пользователь с таким именем уже существует в базе данных.
        """
        if username.data != self.original_username:
            user = db.session.scalar(sa.select(User).where(
                User.username == self.username.data))
            if user is not None:
                raise ValidationError(_l("Пожалуйста, используйте другое имя для пользователя. Это имя уже занято."))


class EmptyForm(FlaskForm):
    """
    Пустая форма с кнопкой "Submit".

    Attributes:
        submit (SubmitField): Кнопка для отправки формы.

    """
    submit: SubmitField = SubmitField('Submit')


class PostForm(FlaskForm):
    """
    Форма создания новых постов.

    Attributes:
        post (TextAreaField): Поле для ввода текста поста. Обязательное поле.
        submit (SubmitField): Кнопка для отправки поста.
    """
    post = TextAreaField(_l("Напишите что-нибудь"), validators=[
        DataRequired(), Length(min=1, max=140)])
    submit = SubmitField(_l("Отправить"))


class SearchForm(FlaskForm):
    q = StringField(_l('Search'), validators=[DataRequired()])  # Определение поля для ввода текста поиска

    def __init__(self, *args, **kwargs):
        # Проверяем, были ли переданы данные формы в качестве аргументов
        if 'formdata' not in kwargs:
            # Если не были переданы, используем аргументы запроса (GET-параметры)
            kwargs['formdata'] = request.args
        # Проверяем, был ли передан дополнительный мета-атрибут
        if 'meta' not in kwargs:
            # Если не был передан, устанавливаем мета-атрибут csrf в False
            kwargs['meta'] = {'csrf': False}
        # Вызываем конструктор родительского класса с переданными аргументами
        super(SearchForm, self).__init__(*args, **kwargs)

class MessageForm(FlaskForm):
    message = TextAreaField(_l('Message'), validators=[
        DataRequired(), Length(min=0, max=140)])
    submit = SubmitField(_l('Submit'))