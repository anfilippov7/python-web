from cachetools import cached
from flask import Flask


@cached({})
def get_app():
    app = Flask("app")

    return app