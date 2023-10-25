# -*- coding: utf-8 -*-

# Стандартные библиотеки Python
from typing import List, Dict, Union
from datetime import datetime

# Библиотеки третьей стороны
from flask import render_template, flash, redirect, url_for, Response, request
from flask_babel import Babel, gettext as _
from flask_login import current_user, login_user, logout_user, login_required
from urllib.parse import urlsplit

# Собственные модули
from werkzeug import Response

from app import app, db
from app.email import send_password_reset_email
from app.forms import LoginForm, RegistrationForm, EditProfileForm,\
    EmptyForm, PostForm, ResetPasswordRequestForm, ResetPasswordForm
from app.models import User, Post


@app.before_request
def before_request() -> None:
    """
    Функция, выполняемая перед каждым запросом к приложению.

    Обновляет поле 'last_seen' для текущего пользователя, если он аутентифицирован.

    Returns:
        None
    """
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index() -> str:
    """
    Маршрут для главной страницы приложения.

    Returns:
        str: HTML-страница с главной страницей приложения.

    Notes:
        - Этот маршрут доступен как для GET, так и для POST запросов.
        - Пользователь должен быть авторизован (вошел в систему) для доступа к этому маршруту.
        - Если запрос выполняется методом POST (отправка формы), создается новый пост, и пользователь
          перенаправляется на главную страницу.
        - Список постов на главной странице пагинируется, и пользователь может переключаться между страницами.

    """
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash(_('Ваш пост опубликован.'))
        return redirect(url_for('index'))

    page = request.args.get('page', 1, type=int)
    posts = current_user.followed_posts().paginate(
        page=page, per_page=app.config["POSTS_PER_PAGE"], error_out=False)
    next_url = url_for('index', page=posts.next_num) if posts.has_next else None
    prev_url = url_for('index', page=posts.prev_num) if posts.has_prev else None

    return render_template('index.html', title='Главная', form=form,
                           posts=posts.items, next_url=next_url, prev_url=prev_url)


@app.route('/explore')
@login_required
def explore():
    """
    Маршрут для страницы "Поиск".

    Returns:
        str: HTML-страница с постами, отсортированными по времени (сначала новые).

    Notes:
        - Этот маршрут доступен только для авторизованных пользователей (пользователей, которые вошли в систему).
        - Список постов на странице "Поиск" также пагинируется, и пользователь может переключаться между страницами.

    """
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        page=page, per_page=app.config["POSTS_PER_PAGE"], error_out=False)
    next_url = url_for('explore', page=posts.next_num) if posts.has_next else None
    prev_url = url_for('explore', page=posts.prev_num) if posts.has_prev else None
    return render_template('index.html', title='Поиск',
                           posts=posts.items, next_url=next_url, prev_url=prev_url)


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
            flash(_('Не верное имя пользователя или пароль'))
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

        flash(_('Поздравляем, вы зарегистрированы! Теперь вы можете войти в систему.'))
        return redirect(url_for('login'))

    # Отображение формы регистрации
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/user/<username>')
@login_required
def user(username: str) -> str:
    """
    Обработчик маршрута для отображения профиля пользователя и его постов.

    Args:
        username (str): Имя пользователя, чей профиль нужно отобразить.

    Returns:
        str: Возвращает шаблон HTML с информацией о пользователе и их постах.

    Notes:
        - Этот маршрут доступен только для авторизованных пользователей (пользователей, которые вошли в систему).
        - Пользователь, чьей страницей является профиль, и его посты отображаются на странице.
        - Список постов на странице профиля пагинируется, и пользователь может переключаться между страницами.

    Raises:
        404 Not Found: Если пользователь с указанным именем не найден.
    """
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(
        page=page, per_page=app.config["POSTS_PER_PAGE"], error_out=False)
    next_url = url_for('user', username=user.username, page=posts.next_num) if posts.has_next else None
    prev_url = url_for('user', username=user.username, page=posts.prev_num) if posts.has_prev else None
    form = EmptyForm()
    return render_template('user.html', user=user, posts=posts.items,
                           next_url=next_url, prev_url=prev_url, form=form)


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile() -> Union[str, Response]:
    """
    Обработчик маршрута для редактирования профиля пользователя.

    GET-запрос отображает форму редактирования профиля.
    POST-запрос обрабатывает данные формы и сохраняет их в профиль пользователя

    Returns:
         str: Возвращает шаблон HTML для отображения формы редактирования
              и перенаправляет на ту же страницу, чтобы отобразить результат сохранения.

    Raises:
          Redirect: Если пользователь не аутентифицирован, то перенаправляет его на страницу входа.
    """
    # Создаем экземпляр формы редактирования профиля пользователя
    form = EditProfileForm(current_user.username)

    if form.validate_on_submit():
        # Сохранение изменений профиля пользователя
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash(_('Ваши изменения сохранены'))
        return redirect(url_for('edit_profile'))

    elif request.method == 'GET':
        # Заполнение полей формы текущими данными профиля пользователя
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me

    return render_template('edit_profile.html', title='Редактирование профиля', form=form)


@app.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username: str) -> Response:
    """
    Обработчик маршрута для подписки на другого пользователя.

    Args:
        username (str): Имя пользователя, на которого нужно подписаться.

    Returns:
        Response: HTTP-ответ, перенаправляющий пользователя на страницу профиля.

    Notes:
        - Этот маршрут доступен только для авторизованных пользователей (пользователей, которые вошли в систему).
        - Если указанный пользователь не существует, выводится сообщение об ошибке.
        - Если форма не прошла валидацию, пользователь перенаправляется на главную страницу.
        - Пользователь не может подписаться на самого себя.

    """
    form = EmptyForm()  # Создаем экземпляр пустой формы
    if form.validate_on_submit():  # Если форма отправлена
        user = User.query.filter_by(username=username).first()  # Ищем пользователя по имени
        if user is None:
            flash(_(f"Пользователь {username} не найден."))
            return redirect(url_for('index'))

        if user == current_user:
            flash(_(f"Вы не можете подписаться на себя."))
            return redirect(url_for('user', username=username))

        current_user.follow(user)  # Вызываем метод подписки текущего пользователя на другого
        db.session.commit()  # Сохраняем изменения в базе данных
        flash(_(f"Вы подписались на {username}."))
        # Перенаправляем на страницу пользователя, на которого подписались
        return redirect(url_for('user', username=username))
    else:
        return redirect(url_for('index'))  # Если форма не прошла валидацию, перенаправляем на главную страницу


@app.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username: str) -> Response:
    """
    Обработчик маршрута для отписки от другого пользователя.

    Args:
        username (str): Имя пользователя, от которого нужно отписаться.

    Returns:
        Response: HTML-ответ, перенаправляющий пользователя на страницу профиля.

    Notes:
        - Этот маршрут доступен только для авторизованных пользователей (пользователей, которые вошли в систему).
        - Если указанный пользователь не существует, выводится сообщение об ошибке.
        - Пользователь не может отписаться от самого себя.
    """
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash(_(f"Пользователь {username} не найден."))
            return redirect(url_for('index'))

        if user == current_user:
            flash(_(f"Вы не можете отписаться от себя."))
            return redirect(url_for('user', username=username))

        current_user.unfollow(user)
        db.session.commit()
        flash(_(f"Вы отписались от {username}."))
        return redirect(url_for('user', username=username))
    else:
        return redirect(url_for('index'))


@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request() -> Union[str, Response]:
    """
    Обработчик маршрута для запроса изменения пароля.

    Methods:
        - GET: Отображает форму запроса сброса пароля.
        - POST: Обрабатывает запрос на сброс пароля.

    Если пользователь аутентифицирован, он будет перенаправлен на страницу 'index'.
    В противном случае, отображается форма для ввода email-адреса.
    Если форма заполнена и введенный email найден в базе данных, отправляется email с инструкциями по сбросу пароля.
    После этого пользователь перенаправляется на страницу 'login'.

    Args:
        None

    Returns:
        GET: HTML-страница с формой запроса сброса пароля.
        POST: Перенаправление пользователя после отправки запроса.
    """
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    # Создаем экземпляр формы
    form = ResetPasswordRequestForm()

    # Если форма отправлена и прошла валидацию
    if form.validate_on_submit():
        # Ищем пользователя по email
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            # Отправляем email с инструкциями по сбросу пароля
            send_password_reset_email(user)

        # Выводим сообщение пользователю
        flash(_('Проверьте почту и следуйте инструкция для изменения пароля.'))

        # Перенаправляем пользователя на страницу 'login'
        return redirect(url_for('login'))

    # Отображаем HTML-страницу с формой
    return render_template('reset_password_request.html',
                           title='Изменение пароля', form=form)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token: str) -> Union[str, 'Response']:
    """
    Обработчик маршрута для сброса пароля с использованием токена.

    Args:
        token (str): Токен сброса пароля.

    Returns:
        Union[str, Response]: HTML-страница для сброса пароля или перенаправление.

    """
    if current_user.is_authenticated:
        return redirect(url_for('index'))  # Перенаправление, если пользователь уже аутентифицирован

    user = User.verify_reset_password_token(token)  # Проверка токена и получение пользователя
    if not user:
        return redirect(url_for('index'))  # Перенаправление, если токен недействителен

    form = ResetPasswordForm()
    if form.validate_on_submit():  # Если форма отправлена и прошла валидацию
        user.set_password(form.password.data)  # Установка нового пароля пользователю
        db.session.commit()  # Сохранение изменений в базе данных
        flash(_('Ваш пароль был изменен.'))  # Вывод сообщения пользователю
        return redirect(url_for('login'))  # Перенаправление на страницу входа

    return render_template('reset_password.html', form=form)  # Отображение HTML-страницы для сброса пароля
