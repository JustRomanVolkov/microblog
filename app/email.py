# -*- coding: utf-8 -*-

# Стандартные библиотеки Python
from threading import Thread

# Библиотеки третьей стороны
from flask import Flask, render_template
from flask_mail import Message

# Собственные модули
from app import app, mail


def send_async_email(app: Flask, msg: Message) -> None:
    """
    Функция для асинхронной отправки электронной почты.

    Args:
        app: Объект Flask-приложения.
        msg (Message): Объект сообщения для отправки.

    """
    with app.app_context():
        mail.send(msg)


def send_email(subject: str, sender: str, recipients: list, text_body: str, html_body: str) -> None:
    """
    Отправляет электронное письмо асинхронно.

    Args:
        subject (str): Тема письма.
        sender (str): Адрес отправителя.
        recipients (list): Список адресов получателей.
        text_body (str): Текстовое содержимое письма.
        html_body (str): HTML-содержимое письма.

    Returns:
        None
    """
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    Thread(target=send_async_email, args=(app, msg)).start()


def send_password_reset_email(user: 'User') -> None:
    """
    Отправляет письмо для сброса пароля пользователю.

    Args:
        user (User): Пользователь, которому отправляется письмо.

    Returns:
        None

    """
    token = user.get_reset_password_token()
    send_email('[Микроблог] Сброс Вашего Пароля.',
               sender=app.config['ADMINS'][0],
               recipients=[user.email],
               text_body=render_template('email/reset_password.txt',
                                         user=user, token=token),
               html_body=render_template('email/reset_password.html',
                                         user=user, token=token))
