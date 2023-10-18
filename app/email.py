# -*- coding: utf-8 -*-

# Стандартные библиотеки Python

# Библиотеки третьей стороны
from flask import render_template
from flask_mail import Message


# Собственные модули
from app import app, mail


def send_email(subject: str, sender: str, recipients: list, text_body: str, html_body: str) -> None:
    """
    Отправляет электронное письмо.

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
    # Предполагается, что у вас есть объект mail для отправки писем
    mail.send(msg)


def send_password_reset_email(user: 'User') -> None:
    """
    Отправляет письмо для сброса пароля пользователю.

    Args:
        user (User): Пользователь, которому отправляется письмо.

    Returns:
        None

    """
    token = user.get_reset_password_token()
    send_email('[Microblog] Reset Your Password',
               sender=app.config['ADMINS'][0],
               recipients=[user.email],
               text_body=render_template('email/reset_password.txt',
                                         user=user, token=token),
               html_body=render_template('email/reset_password.html',
                                         user=user, token=token))
