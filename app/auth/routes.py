# -*- coding: utf-8 -*-

# Стандартные библиотеки Python
from typing import Union

# Библиотеки третьей стороны
from flask import render_template, flash, redirect, url_for, Response, request
from flask_babel import _
from flask_login import current_user, login_user, logout_user
import sqlalchemy as sa
from urllib.parse import urlsplit
from werkzeug import Response

# Собственные модули
from app import db
from app.auth import bp
from app.auth.email import send_password_reset_email
from app.auth.forms import LoginForm, RegistrationForm, ResetPasswordRequestForm, ResetPasswordForm
from app.models import User


@bp.route('/login', methods=['GET', 'POST'])
def login() -> Union[str, 'Response']:
    """
    Маршрут для страницы авторизации и обработки входа.

    GET-запрос показывает форму авторизации.
    POST-запрос обрабатывает данные, введенные в форму, и производит вход или направляет на регистрацию.

    Returns:
        Union[str, 'Response']: HTML-код страницы авторизации или объект Response.
    """
    # Проверка, если пользователь уже аутентифицирован, перенаправление на главную страницу.
    # Переменная current_user поступает из Flask-Login
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    # Создание формы авторизации.
    form = LoginForm()

    # При отправке формы.
    if form.validate_on_submit():
        # Поиск пользователя в базе данных по имени пользователя.
        user = db.session.scalar(
            sa.select(User).where(User.username == form.username.data))
        # Проверка правильности имени пользователя и пароля.
        if user is None or not user.check_password(form.password.data):
            flash(_('Не верное имя пользователя или пароль'))
            return redirect(url_for('auth.login'))

        # Вход пользователя в систему.
        login_user(user, remember=form.remember_me.data)

        # Получение значения 'next' из запроса, которое указывает на следующую страницу после успешной авторизации.
        next_page = request.args.get('next')

        # Проверка, если 'next_page' отсутствует или содержит абсолютный URL (внешнюю ссылку).
        if not next_page or urlsplit(next_page).netloc != '':
            # то перенаправляем пользователя на главную страницу.
            next_page = url_for('main.index')

        # Перенаправление пользователя на следующую страницу после успешной авторизации,
        # либо на главную страницу, если 'next_page' отсутствует или содержит абсолютный URL.
        return redirect(next_page)

    # Отображение страницы авторизации с формой.
    return render_template('auth/login.html', title=_('Авторизация'), form=form)


@bp.route('/logout')
def logout() -> Response:
    """
    Маршрут для выхода из системы (логаут).

    Returns:
        str: Перенаправление на главную страницу приложения после успешного выхода из системы.

    Notes:
        - Этот маршрут позволяет пользователю выйти из своей учетной записи (системы).
        - После успешного выхода из системы, пользователь перенаправляется на главную страницу.

    """
    logout_user()
    return redirect(url_for('main.index'))


@bp.route('/register', methods=['GET', 'POST'])
def register() -> Union[str, 'Response']:
    """
    Обработчик маршрута для регистрации новых пользователей.

    GET-запрос показывает форму регистрации.
    POST-запрос обрабатывает данные, введенные в форму, и регистрирует нового пользователя.

    Returns:
        str: Возвращает шаблон HTML для отображения формы регистрации или перенаправляет на главную страницу.

    Raises:
        Redirect: Если пользователь уже аутентифицирован, их перенаправляют на главную страницу.
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = RegistrationForm()

    if form.validate_on_submit():
        # Создание нового пользователя и добавление в базу данных
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        flash(_('Поздравляем, вы зарегистрированы! Теперь вы можете войти в систему.'))
        return redirect(url_for('auth.login'))

    # Отображение формы регистрации
    return render_template('auth/register.html', title=_('Регистрация'), form=form)


@bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request() -> Union[str, Response]:
    """
    Обработчик маршрута для запроса изменения пароля.

    Methods:
        - GET: Отображает форму запроса сброса пароля.
        - POST: Обрабатывает запрос на сброс пароля.

    Если пользователь аутентифицирован, он будет перенаправлен на страницу 'index'.
    В противном случае отображается форма для ввода email-адреса.
    Если форма заполнена и введенный email найден в базе данных, отправляется email с инструкциями по сбросу пароля.
    После этого пользователь перенаправляется на страницу 'login'.

    Returns:
        GET: HTML-страница с формой запроса сброса пароля.
        POST: Перенаправление пользователя после отправки запроса.
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    # Создаем экземпляр формы
    form = ResetPasswordRequestForm()

    # Если форма отправлена и прошла валидацию
    if form.validate_on_submit():
        # Ищем пользователя по email
        user = db.session.scalar(sa.select(User).where(User.email == form.email.data))
        if user:
            # Отправляем email с инструкциями по сбросу пароля
            send_password_reset_email(user)

        # Выводим сообщение пользователю
        flash(_('Проверьте почту и следуйте инструкция для изменения пароля.'))

        # Перенаправляем пользователя на страницу 'login'
        return redirect(url_for('auth.login'))

    # Отображаем HTML-страницу с формой
    return render_template('auth/reset_password_request.html',
                           title=_('Изменение пароля'), form=form)


@bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token: str) -> Union[str, 'Response']:
    """
    Обработчик маршрута для сброса пароля с использованием токена.

    Args:
        token (str): Токен сброса пароля.

    Returns:
        Union[str, Response]: HTML-страница для сброса пароля или перенаправление.

    """
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))  # Перенаправление, если пользователь уже аутентифицирован

    user = User.verify_reset_password_token(token)  # Проверка токена и получение пользователя
    if not user:
        return redirect(url_for('main.index'))  # Перенаправление, если токен недействителен

    form = ResetPasswordForm()
    if form.validate_on_submit():  # Если форма отправлена и прошла валидацию
        user.set_password(form.password.data)  # Установка нового пароля пользователю
        db.session.commit()  # Сохранение изменений в базе данных
        flash(_('Ваш пароль был изменен.'))  # Вывод сообщения пользователю
        return redirect(url_for('auth.login'))  # Перенаправление на страницу входа

    return render_template('auth/reset_password.html', form=form)  # Отображение HTML-страницы для сброса пароля
