# -*- coding: utf-8 -*-

from flask import render_template
from app import app


@app.route('/')
@app.route('/index')
def index():
    user = {'username': 'Роман Волков'}
    posts = [
        {
            'author': {'username': 'Олег'},
            'body': 'Всем привет!'
        },
        {
            'author': {'username': 'Маша'},
            'body': 'Всем чмоки в этом чатике'
        },
        {
            'author': {'username': 'Петя'},
            'body': 'Дароу!'
        }
    ]
    return render_template('index.html', title='Главная страница', user=user, posts=posts)
