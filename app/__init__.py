# -*- coding: utf-8 -*-

# Стандартные библиотеки Python
import os

# Библиотеки третьей стороны
from elasticsearch import Elasticsearch
from flask import Flask
from flask_babel import Babel, lazy_gettext as _loc
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging.handlers import SMTPHandler, RotatingFileHandler

# Собственные модули
from config import Config


db: SQLAlchemy = SQLAlchemy()
migrate: Migrate = Migrate()

babel: Babel = Babel()

login: LoginManager = LoginManager()
login.login_view = 'auth.login'
login.login_message = _loc("Пожалуйста, войдите, чтобы открыть эту страницу.")

mail = Mail()
bootstrap = Bootstrap()
moment = Moment()

static_folder = 'static'


def create_app(config_class=Config):
    # Создаем экземпляр Flask-приложения.
    app = Flask(__name__)

    # Загружаем настройки из объекта конфигурации.
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    mail.init_app(app)
    bootstrap.init_app(app)
    moment.init_app(app)
    babel.init_app(app, locale_selector=get_locale)

    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    if not app.debug and not app.testing:
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
        # В этом случае будет дата и время, уровень логирования, текст сообщения и источник (путь и номер строки).
        file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))

        # Устанавливаем уровень логирования для файла журнала на INFO, чтобы записывать сообщения INFO и более высокого уровня.
        file_handler.setLevel(logging.INFO)

        # Добавляем файловый обработчик к логгеру приложения.
        app.logger.addHandler(file_handler)

        # Устанавливаем уровень логирования для логгера приложения на INFO.
        app.logger.setLevel(logging.INFO)

        # Записываем информационное сообщение в лог о запуске приложения.
        app.logger.info('Microblog startup')

        app.elasticsearch = Elasticsearch([app.config['ELASTICSEARCH_URL']]) \
            if app.config['ELASTICSEARCH_URL'] else None

    return app


def get_locale():
    """
    Функция для установления текущего языка приложения.

    :return: Возвращает строку, представляющую выбранный язык.
    """
    # return request.accept_languages.best_match(app.config['BABEL_LANGUAGES'])
    return 'ru'


from app import models
