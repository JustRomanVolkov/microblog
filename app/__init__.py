# -*- coding: utf-8 -*-

# Стандартные библиотеки Python
import os

# Библиотеки третьей стороны
import logging
from flask import Flask, request
from flask_babel import Babel, lazy_gettext as _l
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from logging.handlers import SMTPHandler, RotatingFileHandler

# Собственные модули
from config import Config

# Создаем экземпляр Flask-приложения.
app = Flask(__name__)

# Загружаем настройки из объекта конфигурации.
app.config.from_object(Config)

# Инициализация SQLAlchemy для работы с базой данных.
db: SQLAlchemy = SQLAlchemy(app)

# Инициализация Flask-Migrate для миграции базы данных.
migrate: Migrate = Migrate(app, db)


def get_locale():
    """
    Функция для явного установления текущего языка приложения.

    В данном случае, функция всегда возвращает язык 'ru', что означает, что
    приложение будет работать на русском языке.

    :return: Возвращает строку, представляющую выбранный язык (в данном случае 'ru').
    """
    # return request.accept_languages.best_match(app.config['BABEL_LANGUAGES'])
    return 'ru'


# Инициализация Flask-Babel для интернационализации и локализации.
babel: Babel = Babel(app)
babel.init_app(app, locale_selector=get_locale)


# Инициализация Flask-Login для управления аутентификацией.
login: LoginManager = LoginManager(app)

# Определения URL-адреса страницы для перенаправления на вход в систему
# Значение «login» выше является именем функции
login.login_view = 'login'
login.login_message = _l("Пожалуйста, войдите, чтобы открыть эту страницу.")

# Создаем экземпляр Mail.
mail = Mail(app)

# Инициализация Flask-bootstrap для создания красивого и отзывчивого пользовательского интерфейса.
bootstrap = Bootstrap(app)

# Создаем экземпляр Flask-Moment и связываем его с Flask-приложением.
moment = Moment(app)


if not app.debug:
    if app.config['MAIL_SERVER']:
        auth = None
        if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
            auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
        secure = None
        if app.config['MAIL_USE_TLS']:
            secure = ()
        mail_handler = SMTPHandler(
            mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
            fromaddr='no-reply@' + app.config['MAIL_SERVER'],
            toaddrs=app.config['ADMINS'],
            subject='Microblog Failure',
            credentials=auth,
            secure=secure)

    # Если папка 'logs' не существует, создаем ее.
    if not os.path.exists('logs'):
        os.mkdir('logs')

    # Создаем файловый обработчик, который ротирует (создает новый) файл лога при достижении определенного размера.
    # Файлы логов хранятся в папке 'logs' и имеют максимальный размер 10 килобайт,
    # при достижении которого создается новый файл.
    # Максимальное количество файлов логов, хранящихся в архиве (backupCount), равно 10.
    file_handler = RotatingFileHandler('logs/microblog.log', maxBytes=10240, backupCount=10)

    # Устанавливаем формат сообщений в файле журнала.
    # В этом случае, будет дата и время, уровень логирования, текст сообщения и источник (путь и номер строки).
    file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))

    # Устанавливаем уровень логирования для файла журнала на INFO, чтобы записывать сообщения INFO и более высокого уровня.
    file_handler.setLevel(logging.INFO)

    # Добавляем файловый обработчик к логгеру приложения.
    app.logger.addHandler(file_handler)

    # Устанавливаем уровень логирования для логгера приложения на INFO.
    app.logger.setLevel(logging.INFO)

    # Записываем информационное сообщение в лог о запуске приложения.
    app.logger.info('Microblog startup')


from app import routes, models, errors
