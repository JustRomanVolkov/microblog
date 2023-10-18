# -*- coding: utf-8 -*-

# Стандартные библиотеки Python

# Библиотеки третьей стороны
from flask_mail import Message

# Собственные модули
from app import mail


def send_email(subject, sender, recipients, text_body, html_body):
    """
    Отправляет электронное письмо с заданными параметрами.

    :param subject: Тема письма (строка)
    :param sender: Отправитель письма (строка)
    :param recipients: Список получателей (список строк)
    :param text_body: Текстовое тело письма (строка)
    :param html_body: HTML-тело письма (строка)

    :return: Ничего не возвращает.
    """
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    mail.send(msg)
