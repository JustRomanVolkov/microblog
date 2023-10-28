# -*- coding: utf-8 -*-

# Стандартные библиотеки Python
from typing import Union
from datetime import datetime

# Библиотеки третьей стороны
from flask import current_app, flash, g, redirect, render_template, Response, request, url_for
from flask_babel import gettext as _, get_locale
from flask_login import current_user, login_required
from langdetect import detect, LangDetectException
from urllib.parse import urlsplit

# Собственные модули
from werkzeug import Response

from app import db
from app.main import bp
from app.main.forms import EditProfileForm, EmptyForm, PostForm
from app.models import User, Post


@bp.before_request
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
        g.locale = str(get_locale())

@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@login_required
def index() -> Union[str, 'Response']:
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
        try:
            language = detect(form.post.data)
        except LangDetectException:
            language = ''
        post = Post(body=form.post.data, author=current_user, language=language)
        db.session.add(post)
        db.session.commit()
        flash(_('Ваш пост опубликован.'))
        return redirect(url_for('main.index'))

    page = request.args.get('page', 1, type=int)
    posts = current_user.followed_posts().paginate(
        page=page, per_page=current_app.config["POSTS_PER_PAGE"], error_out=False)
    next_url = url_for('main.index', page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.index', page=posts.prev_num) if posts.has_prev else None

    return render_template('index.html', title=_('Главная'), form=form,
                           posts=posts.items, next_url=next_url, prev_url=prev_url)


@bp.route('/explore')
@login_required
def explore() -> str:
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
        page=page, per_page=current_app.config["POSTS_PER_PAGE"], error_out=False)
    next_url = url_for('main.explore', page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.explore', page=posts.prev_num) if posts.has_prev else None
    return render_template('index.html', title=_('Поиск'),
                           posts=posts.items, next_url=next_url, prev_url=prev_url)


@bp.route('/user/<username>')
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
        page=page, per_page=current_app.config["POSTS_PER_PAGE"], error_out=False)
    next_url = url_for('main.user', username=user.username, page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.user', username=user.username, page=posts.prev_num) if posts.has_prev else None
    form = EmptyForm()
    return render_template('user.html', user=user, posts=posts.items,
                           next_url=next_url, prev_url=prev_url, form=form)


@bp.route('/edit_profile', methods=['GET', 'POST'])
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
        return redirect(url_for('main.edit_profile'))

    elif request.method == 'GET':
        # Заполнение полей формы текущими данными профиля пользователя
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me

    return render_template('edit_profile.html', title=_('Редактирование профиля'), form=form)


@bp.route('/follow/<username>', methods=['POST'])
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
            flash(_('Пользователь %(username)s не найден.', username=username))
            return redirect(url_for('main.index'))

        if user == current_user:
            flash(_(f"Вы не можете подписаться на себя."))
            return redirect(url_for('main.user', username=username))

        current_user.follow(user)  # Вызываем метод подписки текущего пользователя на другого
        db.session.commit()  # Сохраняем изменения в базе данных
        flash(_(f"Вы подписались на {username}."))
        # Перенаправляем на страницу пользователя, на которого подписались
        return redirect(url_for('main.user', username=username))
    else:
        return redirect(url_for('main.index'))  # Если форма не прошла валидацию, перенаправляем на главную страницу


@bp.route('/unfollow/<username>', methods=['POST'])
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
            return redirect(url_for('main.index'))

        if user == current_user:
            flash(_(f"Вы не можете отписаться от себя."))
            return redirect(url_for('main.user', username=username))

        current_user.unfollow(user)
        db.session.commit()
        flash(_(f"Вы отписались от {username}."))
        return redirect(url_for('main.user', username=username))
    else:
        return redirect(url_for('main.index'))
