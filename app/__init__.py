from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from config import Config

# Создаем экземпляр Flask-приложения.
app = Flask(__name__)

# Загружаем настройки из объекта конфигурации.
app.config.from_object(Config)

# Инициализация SQLAlchemy для работы с базой данных.
db: SQLAlchemy = SQLAlchemy(app)

# Инициализация Flask-Login для управления аутентификацией.
login: LoginManager = LoginManager(app)

# Инициализация Flask-Migrate для миграции базы данных.
migrate: Migrate = Migrate(app, db)


from app import routes, models
