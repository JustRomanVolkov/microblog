# -*- coding: utf-8 -*-

# Стандартные библиотеки Python
from typing import List, Dict, Union
from datetime import datetime

# Библиотеки третьей стороны
from flask import render_template, flash, redirect, url_for, Response, request
from flask_login import current_user, login_user, logout_user, login_required
from urllib.parse import urlsplit

# Собственные модули
from app import app, db
from app.forms import LoginForm, RegistrationForm, EditProfileForm, PostForm
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

    """
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data, author=current_user)
        form = PostForm()
        if form.validate_on_submit():
            post = Post(body=form.post.data, author=current_user)
            db.session.add(post)
            db.session.commit()
            flash('Ваш пост опубликован.')
            return redirect(url_for('index'))
    page = request.args.get('page', 1, type=int)
    posts = current_user.followed_posts().paginate(
        page=page, per_page=app.config["TICKERS_PER_PAGE"], error_out=False)
    next_url = url_for('index', page=posts.next_num) if posts.has_next else None
    prev_url = url_for('index', page=posts.prev_num) if posts.has_prev else None

    return render_template('index.html', title='Home', form=form,
                           posts=posts.items, next_url=next_url, prev_url=prev_url)


@app.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        page=page, per_page=app.config["TICKERS_PER_PAGE"], error_out=False)
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


@app.route('/user/<username>')
@login_required
def user(username):
    """
    Обработчик маршрута для отображения профиля пользователя.

    Args:
        username (str): Имя пользователя, чьей профиль нужно отобразить.

    Returns:
        str: Возвращает шаблон HTML с информацией о пользователе и их постах.

    Raises:
        404 Not Found: Если пользователь с указанным именем не найден.
    """
    user = User.query.filter_by(username=username).first_or_404()

    # Заглушка для постов пользователя (замените этот список на данные из вашей базы данных)
    posts = [
        {'author': user, 'body': 'Test post #1'},
        {'author': user, 'body': 'Test post #2'}
    ]
    return render_template('user.html', user=user, posts=posts)


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
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
        flash('Ваши изменения сохранены')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        # Заполнение полей формы текущими данными профиля пользователя
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me

    return render_template('edit_profile.html', title='Редактирование профиля', form=form)


@app.route('/follow/<username>')
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
        - Пользователь не может подписаться на самого себя.

    """
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(f"Пользователь {username} не найден.")
        return redirect(url_for('index'))
    if user == current_user:
        flash(f"Вы не можете подписаться на себя.")
        return redirect(url_for('user', username=username))
    current_user.follow(user)
    db.session.commit()
    flash(f"Вы подписались на {username}.")
    return redirect(url_for('user', username=username))


@app.route('/unfollow/<username>')
@login_required
def unfollow(username):
    """
    Обработчик маршрута для отписки от другого пользователя.

    Args:
        username (str): Имя пользователя, от которого нужно отписаться.

    Returns:
        Response: HTML-ответ, перенаправляющий пользователя на страницу профиля.

    Notes:
        - Этот маршрут доступен только для авторизованных пользователей (пользователей, которые вошли в систему).
        - Если указанный пользователь не существует, выводится сообщение об ошибке.
        - Пользователь не может подписаться на самого себя.
    """
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(f"Пользователь {username} не найден.")
        return redirect(url_for('index'))
    if user == current_user:
        flash(f"Вы не можете отписаться от себя.")
        return redirect(url_for('user', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash(f"Вы отписались от {username}.")
    return redirect(url_for('user', username=username))
