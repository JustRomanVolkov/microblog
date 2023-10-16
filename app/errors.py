# -*- coding: utf-8 -*-

# Библиотеки третьей стороны
from flask import render_template

# Собственные модули
from app import app, db


@app.errorhandler(404)
def not_found_error(error: Exception) -> tuple:
    """
    Обработчик ошибки 404 (Not found).

    Args:
        error (Exception): Исключение, связанное с ошибкой 404.
    Returns:
        tuple: Возвращает кортеж с шаблоном HTML для ошибки 404 и кодом состояния 404.
    """
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error: Exception) -> tuple:
    """
    Обработчик ошибки 500 (Internal Server Error).

    Args:
        error (Exception): Исключение, связанное с ошибкой 500.

    Returns:
        tuple: Возвращает кортеж с шаблоном HTML для ошибки 500 и кодом состояния 500.
    """
    db.session.rollback() # Откатываем транзакцию базы данных
    return render_template('500.html'), 500
