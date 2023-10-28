# -*- coding: utf-8 -*-

# Библиотеки третьей стороны
from flask_babel import lazy_gettext as _loc
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, ValidationError

# Собственные модули
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
    username: StringField = StringField(_loc('Имя пользователя'), validators=[DataRequired()])
    about_me: TextAreaField = TextAreaField(_loc('Обо мне'), validators=[Length(min=0, max=140)])
    submit: SubmitField = SubmitField(_loc('Принять изменения'))

    def __init__(self, original_username: str, *args, **kwargs):
        """
        Инициализирует форму редактирования профиля.

        Args:
            original_username (str): Оригинальное имя пользователя.
            *args: Позиционные аргументы FlaskForm.
            **kwargs: Именованные аргументы FlaskForm.
        """
        super(EditProfileForm, self).__init__(*args, **kwargs)
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
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError(_loc("Пожалуйста, используйте другое имя для пользователя. Это имя уже занято."))


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
    post = TextAreaField(_loc("Напишите что-нибудь"), validators=[
        DataRequired(), Length(min=1, max=140)])
    submit = SubmitField(_loc("Отправить"))
