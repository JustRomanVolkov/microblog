from flask import Flask

app = Flask(__name__)

from app import app


if __name__ == '__main__':
    app.run()
