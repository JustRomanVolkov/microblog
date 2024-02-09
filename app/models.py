# -*- coding: utf-8 -*-

# Стандартные библиотеки Python
from datetime import datetime
from time import time
from typing import Union

# Библиотеки третьей стороны
import jwt
from flask import current_app
from flask_login import UserMixin
from hashlib import md5
import sqlalchemy as sa
from sqlalchemy.orm import relationship, Query
from werkzeug.security import generate_password_hash, check_password_hash

# Собственные модули
from app import db, login
from app.search import add_to_index, remove_from_index, query_index


# Таблица followers моделирует отношения "подписчик - подписан на" между пользователями.
# Она используется для отслеживания того, какие пользователи подписаны на каких других пользователей.
# Столбец 'follower_id' представляет пользователя, который подписывается на других пользователей,
# Столбец 'followed_id' представляет пользователя, на которого подписаны.
followers = db.Table('followers',
                     db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
                     db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
                     )


class User(UserMixin, db.Model):
    """
    Модель пользователя для базы данных.
    """
    __tablename__ = 'user'
    id: int = db.Column(db.Integer, primary_key=True)
    username: str = db.Column(db.String(64), index=True, unique=True)
    email: str = db.Column(db.String(120), index=True, unique=True)
    password_hash: str = db.Column(db.String(128))
    about_me: str = db.Column(db.String(140))
    last_seen: datetime = db.Column(db.DateTime, default=datetime.utcnow)
    followed = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')

    # Для отношений «один ко многим».
    # Аргумент backref определяет имя поля добавленное к объектам класса «много», для указания на объект «один».
    posts: relationship = db.relationship('Post', backref='author', lazy='dynamic')
    __allow_unmapped__ = True

    def __repr__(self) -> str:
        """
        Метод, возвращающий строковое представление объекта пользователя.
        """
        return f'<Пользователь {self.username}>'

    def set_password(self, password: str) -> None:
        """
        Установка хэша пароля пользователя.
        """
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """
        Проверка введенного пароля с хэшем пароля пользователя.
        """
        return check_password_hash(self.password_hash, password)

    def avatar(self, size: int) -> str:
        """
        Генерирует URL аватара пользователя на основе Gravatar.

        Args:
            size (int): Размер аватара в пикселях.

        Returns:
            str: URL аватара пользователя.

        Note:
            Для генерации аватара используется хеш от адреса электронной почты пользователя (email),
            который приводится к нижнему регистру, кодируется в формате UTF-8 и хешируется с помощью MD5.
            Полученный хеш используется в URL для получения аватара с сервиса Gravatar.
        """
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return f'https://www.gravatar.com/avatar/{digest}?d=identicon&s={size}'

    def is_following(self, user: 'User') -> bool:
        """
        Проверить, подписан ли текущий пользователь на указанного пользователя.

        Args:
            user (User): Пользователь, наличие подписки на которого нужно проверить.

        Returns:
            bool: True, если текущий пользователь подписан на указанного пользователя, в противном случае False.
        """
        return self.followed.filter(followers.c.followed_id == user.id).count() > 0

    def follow(self, user: 'User') -> None:
        """
        Начать подписку на указанного пользователя.

        Args:
            user (User): Пользователь, на которого нужно подписаться.
        """
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user: 'User') -> None:
        """
        Прекратить подписку на указанного пользователя.

        Args:
            user (User): Пользователь, от которого нужно отписаться.
        """
        if self.is_following(user):
            self.followed.remove(user)

    def followed_posts(self) -> Query:
        """
        Получить посты, на которые подписан текущий пользователь, включая свои.

        Returns:
            Query: Запрос к базе данных, возвращающий посты, упорядоченные по времени (сначала новые).
        """
        followed = Post.query.join(
            followers, (followers.c.followed_id == Post.user_id)).filter(
                followers.c.follower_id == self.id)
        own = Post.query.filter_by(user_id=self.id)
        return followed.union(own).order_by(Post.timestamp.desc())

    def get_reset_password_token(self, expires_in: int = 600) -> str:
        """
        Генерирует токен сброса пароля для пользователя.

        Args:
            expires_in (int): Время жизни токена в секундах. По умолчанию 600 секунд (10 минут).

        Returns:
            str: Сгенерированный токен сброса пароля в формате строки.

        """
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_reset_password_token(token: str) -> Union[None, 'User']:
        """
        Проверяет токен сброса пароля и возвращает соответствующего пользователя.

        Args:
            token (str): Токен сброса пароля.

        Returns:
            Union[None, User]: Возвращает пользователя, связанного с токеном, или None, если токен недействителен.

        """
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)



class SearchableMixin(object):
    @classmethod
    def search(cls, expression, page, per_page):
        # Выполняем поиск по индексу
        ids, total = query_index(cls.__tablename__, expression, page, per_page)
        if total == 0:  # Если результаты не найдены
            return [], 0  # Возвращаем пустой список и ноль
        when = []  # Создаем список для определения порядка результатов
        for i in range(len(ids)):
            when.append((ids[i], i))  # Добавляем идентификаторы и их порядковый номер в список when
        # Формируем запрос к базе данных для получения объектов по их идентификаторам
        query = sa.select(cls).where(cls.id.in_(ids)).order_by(
            db.case(*when, value=cls.id))
        return db.session.scalars(query), total  # Возвращаем результаты поиска и общее количество найденных объектов

    @classmethod
    def before_commit(cls, session):
        # Запоминаем изменения в объектах перед фиксацией транзакции
        session._changes = {
            'add': list(session.new),
            'update': list(session.dirty),
            'delete': list(session.deleted)
        }

    @classmethod
    def after_commit(cls, session):
        # Применяем изменения к индексу после фиксации транзакции
        for obj in session._changes['add']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['update']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['delete']:
            if isinstance(obj, SearchableMixin):
                remove_from_index(obj.__tablename__, obj)
        session._changes = None  # Сбрасываем запомненные изменения

    @classmethod
    def reindex(cls):
        # Переиндексируем все объекты модели
        for obj in db.session.scalars(sa.select(cls)):
            add_to_index(cls.__tablename__, obj)


# Добавляем слушателей событий к экземпляру db.session
db.event.listen(db.session, 'before_commit', SearchableMixin.before_commit)
db.event.listen(db.session, 'after_commit', SearchableMixin.after_commit)


class Post(SearchableMixin, db.Model):
    """
    Модель поста для базы данных.
    """
    id: int = db.Column(db.Integer, primary_key=True)
    body: str = db.Column(db.String(140))

    # тут индексация для поиска, а сама логика в search.py
    __searchable__ = ['body']

    # Специально не включил () после utcnow,
    # поэтому передаю эту функцию, а не результат ее вызова.
    # SQLAlchemy установит для поля значение вызова этой функции.
    # Это позволяет работать с датами и временем UTC в серверном приложении.
    # То есть гарантирует, что используются единые временные метки независимо от того, где находятся пользователи
    timestamp: datetime = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id: int = db.Column(db.Integer, db.ForeignKey('user.id'))
    language = db.Column(db.String(5))

    def __repr__(self) -> str:
        """
        Метод, возвращающий строковое представление объекта поста.
        """
        return f'Пост {self.body}'


@login.user_loader
def load_user(id: int) -> User | None:
    """
    Функция для загрузки пользователя по его идентификатору.

    Args:
        id (int): Идентификатор пользователя.

    Returns:
        User: Экземпляр пользователя, если найден, или None.
    """
    return User.query.get(int(id))
