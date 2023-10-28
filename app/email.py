# -*- coding: utf-8 -*-

# Стандартные библиотеки Python
from threading import Thread

# Библиотеки третьей стороны
from flask import Flask, current_app
from flask_mail import Message

# Собственные модули
from app import mail


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
    Thread(target=send_async_email, args=(current_app._get_current_object(), msg)).start()
