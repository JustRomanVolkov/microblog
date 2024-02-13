# -*- coding: utf-8 -*-

# Стандартные библиотеки Python
from datetime import datetime, timezone
from time import time
from typing import Union, Optional

# Библиотеки третьей стороны
import jwt
from flask import current_app
from flask_login import UserMixin
from hashlib import md5
import sqlalchemy as sa
import sqlalchemy.orm as so
from werkzeug.security import generate_password_hash, check_password_hash

# Собственные модули
from app import db, login
from app.search import add_to_index, remove_from_index, query_index


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

# Таблица followers моделирует отношения "подписчик - подписан на" между пользователями.
# Она используется для отслеживания того, какие пользователи подписаны на каких других пользователей.
# Столбец 'follower_id' представляет пользователя, который подписывается на других пользователей,
# Столбец 'followed_id' представляет пользователя, на которого подписаны.
followers = sa.Table(
    'followers',
    db.metadata,
    sa.Column('follower_id', sa.Integer, sa.ForeignKey('user.id'),
              primary_key=True),
    sa.Column('followed_id', sa.Integer, sa.ForeignKey('user.id'),
              primary_key=True)
)


class User(UserMixin, db.Model):
    """
    Модель пользователя для базы данных.
    """
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True,
                                                unique=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index=True,
                                             unique=True)
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))
    about_me: so.Mapped[Optional[str]] = so.mapped_column(sa.String(140))
    last_seen: so.Mapped[Optional[datetime]] = so.mapped_column(
        default=lambda: datetime.now(timezone.utc))

    posts: so.WriteOnlyMapped['Post'] = so.relationship(
        back_populates='author')
    following: so.WriteOnlyMapped['User'] = so.relationship(
        secondary=followers, primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        back_populates='followers')
    followers: so.WriteOnlyMapped['User'] = so.relationship(
        secondary=followers, primaryjoin=(followers.c.followed_id == id),
        secondaryjoin=(followers.c.follower_id == id),
        back_populates='following')

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
        query = self.following.select().where(User.id == user.id)
        return db.session.scalar(query) is not None

    def follow(self, user: 'User') -> None:
        """
        Начать подписку на указанного пользователя.

        Args:
            user (User): Пользователь, на которого нужно подписаться.
        """
        if not self.is_following(user):
            self.following.add(user)

    def unfollow(self, user: 'User') -> None:
        """
        Прекратить подписку на указанного пользователя.

        Args:
            user (User): Пользователь, от которого нужно отписаться.
        """
        if self.is_following(user):
            self.following.remove(user)

    def followers_count(self):
        query = sa.select(sa.func.count()).select_from(
            self.followers.select().subquery())
        return db.session.scalar(query)

    def following_count(self):
        query = sa.select(sa.func.count()).select_from(
            self.following.select().subquery())
        return db.session.scalar(query)

    def following_posts(self):
        Author = so.aliased(User)
        Follower = so.aliased(User)
        return (
            sa.select(Post)
            .join(Post.author.of_type(Author))
            .join(Author.followers.of_type(Follower), isouter=True)
            .where(sa.or_(
                Follower.id == self.id,
                Author.id == self.id,
            ))
            .group_by(Post)
            .order_by(Post.timestamp.desc())
        )

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
        return db.session.get(User, id)


@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))


class Post(SearchableMixin, db.Model):
    """
    Модель поста для базы данных.
    """
    __searchable__ = ['body']
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    body: so.Mapped[str] = so.mapped_column(sa.String(140))
    timestamp: so.Mapped[datetime] = so.mapped_column(
        index=True, default=lambda: datetime.now(timezone.utc))
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id),
                                               index=True)
    language: so.Mapped[Optional[str]] = so.mapped_column(sa.String(5))

    author: so.Mapped[User] = so.relationship(back_populates='posts')

    def __repr__(self) -> str:
        """
        Метод, возвращающий строковое представление объекта поста.
        """
        return f'Пост {self.body}'
