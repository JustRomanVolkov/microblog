# -*- coding: utf-8 -*-

from flask import render_template
from app import app


@app.route('/')
@app.route('/index')
def index():
    user = {'username': 'Роман'}
    return render_template('index.html', title='Главная страница', user=user)

