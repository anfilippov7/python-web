from typing import Union


class HttpError(Exception):

    def __init__(self, status_code: int, message: Union[str, dict, list]):
        self.status_code = status_code
        self.message = message

