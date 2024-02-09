from flask import current_app


def add_to_index(index, model):  # Определение функции для добавления документа в индекс Elasticsearch
    if not current_app.elasticsearch:  # Проверка наличия подключения к Elasticsearch
        return  # В случае отсутствия подключения выход из функции
    payload = {}  # Создание пустого словаря для хранения данных документа
    for field in model.__searchable__:  # Перебор всех полей, указанных для индексации в модели
        payload[field] = getattr(model, field)  # Добавление значений полей в словарь payload
    current_app.elasticsearch.index(index=index, id=model.id, document=payload)  # Добавление документа в индекс Elasticsearch


def remove_from_index(index, model):  # Определение функции для удаления документа из индекса Elasticsearch
    if not current_app.elasticsearch:  # Проверка наличия подключения к Elasticsearch
        return  # В случае отсутствия подключения выход из функции
    current_app.elasticsearch.delete(index=index, id=model.id)  # Удаление документа из индекса Elasticsearch


def query_index(index, query, page, per_page):  # Определение функции для выполнения запроса к индексу Elasticsearch
    if not current_app.elasticsearch:  # Проверка наличия подключения к Elasticsearch
        return [], 0  # В случае отсутствия подключения возврат пустого списка и нуля
    # Выполнение поиска в индексе Elasticsearch
    search = current_app.elasticsearch.search(
        index=index,
        query={'multi_match': {'query': query, 'fields': ['*']}},
        from_=(page - 1) * per_page,
        size=per_page)
    ids = [int(hit['_id']) for hit in search['hits']['hits']]  # Получение идентификаторов найденных документов
    return ids, search['hits']['total']['value']  # Возврат списка идентификаторов и общего количества результатов поиска
