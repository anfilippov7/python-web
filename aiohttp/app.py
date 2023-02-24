from cachetools import cached
from aiohttp import web


@cached({})
def get_app():
    app = web.Application()

    return app