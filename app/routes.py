# -*- coding: utf-8 -*-

from flask import render_template, flash, redirect, url_for
from app import app
from app.forms import LoginForm


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


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        flash(f'Логин запрошен для пользователя {form.username.data},'
              f'запомни меня = {form.remember_me.data}')
        return redirect(url_for('index'))
    return render_template('login.html', title='Авторизация', form=form)
