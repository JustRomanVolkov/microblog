
# -*- coding: utf-8 -*-

# Стандартные библиотеки Python

# Библиотеки третьей стороны
from flask import render_template, current_app
from flask_babel import _

# Собственные модули
from app.email import send_email


def send_password_reset_email(user: 'User') -> None:
    """
    Отправляет письмо для сброса пароля пользователю.

    Args:
        user (User): Пользователь, которому отправляется письмо.

    Returns:
        None

    """
    token = user.get_reset_password_token()
    send_email(_('[Микроблог] Сброс Вашего Пароля.'),
               sender=current_app.config['ADMINS'][0],
               recipients=[user.email],
               text_body=render_template('email/reset_password.txt',
                                         user=user, token=token),
               html_body=render_template('email/reset_password.html',
                                         user=user, token=token))
