from flask import current_app


def add_to_index(index, model):  # ����������� ������� ��� ���������� ��������� � ������ Elasticsearch
    if not current_app.elasticsearch:  # �������� ������� ����������� � Elasticsearch
        return  # � ������ ���������� ����������� ����� �� �������
    payload = {}  # �������� ������� ������� ��� �������� ������ ���������
    for field in model.__searchable__:  # ������� ���� �����, ��������� ��� ���������� � ������
        payload[field] = getattr(model, field)  # ���������� �������� ����� � ������� payload
    current_app.elasticsearch.index(index=index, id=model.id, document=payload)  # ���������� ��������� � ������ Elasticsearch


def remove_from_index(index, model):  # ����������� ������� ��� �������� ��������� �� ������� Elasticsearch
    if not current_app.elasticsearch:  # �������� ������� ����������� � Elasticsearch
        return  # � ������ ���������� ����������� ����� �� �������
    current_app.elasticsearch.delete(index=index, id=model.id)  # �������� ��������� �� ������� Elasticsearch


def query_index(index, query, page, per_page):  # ����������� ������� ��� ���������� ������� � ������� Elasticsearch
    if not current_app.elasticsearch:  # �������� ������� ����������� � Elasticsearch
        return [], 0  # � ������ ���������� ����������� ������� ������� ������ � ����
    # ���������� ������ � ������� Elasticsearch
    search = current_app.elasticsearch.search(
        index=index,
        query={'multi_match': {'query': query, 'fields': ['*']}},
        from_=(page - 1) * per_page,
        size=per_page)
    ids = [int(hit['_id']) for hit in search['hits']['hits']]  # ��������� ��������������� ��������� ����������
    return ids, search['hits']['total']['value']  # ������� ������ ��������������� � ������ ���������� ����������� ������
