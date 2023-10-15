# -*- coding: utf-8 -*-

# Стандартные библиотеки Python
from typing import List, Dict, Union

# Библиотеки третьей стороны
from flask import render_template, flash, redirect, url_for, Response, request
from flask_login import current_user, login_user, logout_user, login_required
from urllib.parse import urlsplit

# Собственные модули
from app import app, db
from app.forms import LoginForm, RegistrationForm
from app.models import User


@app.route('/')
@app.route('/index')
@login_required
def index() -> str:
    """
    Отображение главной страницы.

    Returns:
        str: HTML-код главной страницы.
    """
    posts: List[Dict[str, Union[Dict[str, str], str]]] = [
        {
            'author': {'username': 'Олег'},
            'body': 'Всем привет!'
        },
        {
            'author': {'username': 'Маша'},
            'body': 'Всем чмоки в этом чатике'
        },
        {
            'author': {'username': 'Петя'},
            'body': 'Дароу!'
        }
    ]
    # Отображение главной страницы с постами.
    return render_template('index.html', title='Главная страница', posts=posts)


@app.route('/login', methods=['GET', 'POST'])
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
        return redirect(url_for('index'))

    # Создание формы авторизации.
    form = LoginForm()

    # При отправке формы.
    if form.validate_on_submit():
        # Поиск пользователя в базе данных по имени пользователя.
        user = User.query.filter_by(username=form.username.data).first()

        # Проверка правильности имени пользователя и пароля.
        if user is None or not user.check_password(form.password.data):
            flash('Не верное имя пользователя или пароль')
            return redirect(url_for('login'))

        # Вход пользователя в систему.
        login_user(user, remember=form.remember_me.data)

        # Получение значения 'next' из запроса, которое указывает на следующую страницу после успешной авторизации.
        next_page = request.args.get('next')

        # Проверка, если 'next_page' отсутствует или содержит абсолютный URL (внешнюю ссылку).
        if not next_page or urlsplit(next_page).netloc != '':
            # то перенаправляем пользователя на главную страницу.
            next_page = url_for('index')

        # Перенаправление пользователя на следующую страницу после успешной авторизации,
        # либо на главную страницу, если 'next_page' отсутствует или содержит абсолютный URL.
        return redirect(next_page)

    # Отображение страницы авторизации с формой.
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
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
        return redirect(url_for('index'))

    form = RegistrationForm()

    if form.validate_on_submit():
        # Создание нового пользователя и добавление в базу данных
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        flash('Поздравляем, вы зарегистрированы! Теперь вы можете войти в систему.')
        return redirect(url_for('login'))

    # Отображение формы регистрации
    return render_template('register.html', title='Регистрация', form=form)
