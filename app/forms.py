# -*- coding: utf-8 -*-

# Библиотеки третьей стороны
from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError

# Собственные модули
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
        """
        Проверяет уникальность имени пользователя.

        Args:
            username (StringField): Поле имени пользователя.

        Raises:
            ValidationError: Если имя пользователя уже занято.
        """
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError(_l('Используйте другое имя.'))

    def validate_email(self, email):
        """
        Проверяет уникальность почты.

        Args:
            email (StringField): Поле почты.

        Raises:
            ValidationError: Если почта уже используется другим пользователем.
        """
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError(_l('Используйте другую почту.'))


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
