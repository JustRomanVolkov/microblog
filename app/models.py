# -*- coding: utf-8 -*-

# Стандартные библиотеки Python
from datetime import datetime

# Библиотеки третьей стороны
from flask_login import UserMixin
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash

# Собственные модули
from app import db, login


class User(UserMixin, db.Model):
    """
    Модель пользователя для базы данных.
    """
    __tablename__ = 'user'
    id: int = db.Column(db.Integer, primary_key=True)
    username: str = db.Column(db.String(64), index=True, unique=True)
    email: str = db.Column(db.String(120), index=True, unique=True)
    password_hash: str = db.Column(db.String(128))

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


class Post(db.Model):
    """
    Модель поста для базы данных.
    """
    id: int = db.Column(db.Integer, primary_key=True)
    body: str = db.Column(db.String(140))

    # Специально не включил () после utcnow,
    # поэтому передаю эту функцию, а не результат ее вызова.
    # SQLAlchemy установит для поля значение вызова этой функции.
    # Это позволяет работать с датами и временем UTC в серверном приложении.
    # То есть гарантирует, что используются единые временные метки независимо от того, где находятся пользователи
    timestamp: datetime = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id: int = db.Column(db.Integer, db.ForeignKey('user.id'))

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
