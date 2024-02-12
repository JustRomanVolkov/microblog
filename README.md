# Microblog

Описание вашего микроблога, его основные функции и преимущества.

## Технологии

- **Backend**: Flask + SQLAlchemy
- **Frontend**: Bootstrap
- **Полнотекстовый поиск**: Elasticsearch
- **Перевод меню**: Flask-Babel
- **Перевод постов**: Google Translate API
- **Контейнеризация**: Docker

### Клонирование репозитория

```bash
git clone https://github.com/TheRomanVolkov/microblog.git
cd microblog
```

### Запуск с Docker

Для запуска приложения Microblog в Docker, следуйте ниже приведенным шагам. Это руководство предполагает, что у вас уже установлены Docker и Docker Compose (если используется).

#### Предварительные требования

- Установленный Docker
- Установленный Docker Compose (для многоконтейнерных приложений)


#### 1. Создание сети Docker

Для обеспечения связи между контейнерами необходимо создать сеть Docker:

```bash
docker network create microblog-network
```

#### 2. Запуск контейнера базы данных

Запустите контейнер MySQL, предварительно заменив `<database-password>` на ваш пароль:

```bash
docker run --name mysql -d -e MYSQL_RANDOM_ROOT_PASSWORD=yes \
    -e MYSQL_DATABASE=microblog -e MYSQL_USER=microblog \
    -e MYSQL_PASSWORD=<database-password> \
    --network microblog-network \
    mysql:latest
```

#### 3. Запуск контейнера Elasticsearch

```bash
docker run --name elasticsearch -d --rm -p 9200:9200 \
    -e discovery.type=single-node -e xpack.security.enabled=false \
    --network microblog-network \
    -t docker.elastic.co/elasticsearch/elasticsearch:8.11.1
```

#### 4. Запуск приложения Microblog

Замените `<database-password>` на пароль от базы данных:

```bash
docker run --name microblog -d -p 8000:5000 --rm -e SECRET_KEY=my-secret-key \
   --network microblog-network \
    -e DATABASE_URL=mysql+pymysql://microblog:<database-password>@mysql/microblog \
    -e ELASTICSEARCH_URL=http://elasticsearch:9200 \
    microblog:latest
```

#### 5. Проверка работоспособности приложения

После запуска всех контейнеров, приложение будет доступно по адресу `http://localhost:8000`.

## Функционал

- **Аутентификация и авторизация**: Система регистрации и входа в систему для пользователей.
- **Публикация постов**: Пользователи могут создавать и публиковать посты.
- **Подпискаа/отписка от пользователей**: Пользователи могут видеть посты только тех, на кого подписались.
- **Перевод меню**: Пользователи могут менять язык меню.
- **Полнотекстовый поиск**: Возможность поиска по содержимому постов с использованием Elasticsearch.
- **Автоматический перевод постов**: Интеграция с Google Translate API для автоматического перевода постов.

---

Создано с ❤️ и ☕
