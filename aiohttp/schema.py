from pydantic import BaseModel, validator, EmailStr, StrictStr
from typing import Any, Dict, Type, Union
import re
import os
import json
from aiohttp import web

PASSWORD_LENGTH = int(os.getenv("PASSWORD_LENGTH", 7))
PASSWORD_REGEX = re.compile(
    "^(?=.*?[A-Z])(?=.*?[a-z])(?=.*?[0-9])(?=.*?[#?!@$%^&*-])*.{{{password_length},}}$".format(
        password_length=PASSWORD_LENGTH
    )
)


class Userval(BaseModel):
    name: Union[str, int]
    e_mail: EmailStr
    password: str

    @validator("password")
    def strong_password(cls, value: str):
        if not PASSWORD_REGEX.match(value):
            raise ValueError("password is to easy")
        return value


SCHEMA_TYPE = Type[Userval]


def validate_user(schema: SCHEMA_TYPE, data: Dict[str, Any], exclude_none: bool = True) -> dict:
    try:
        validated = schema(**data).dict(exclude_none=exclude_none)
    except (ValueError, TypeError):
        raise web.HTTPConflict(text=json.dumps({'status': 'error',
                                                'message': 'mistake registration '
                                                           '(password is to easy or incorrect e_mail)'}),
                               content_type='application/json')
    return validated


class Serviceval(BaseModel):
    heading: StrictStr
    description: StrictStr


def validate_service(Serviceval, json_data, exclude_none: bool = True):
    try:
        validated = Serviceval(**json_data).dict(exclude_none=exclude_none)
    except (ValueError, TypeError, json.decoder.JSONDecodeError):
        raise web.HTTPConflict(text=json.dumps({'status': 'error',
                                                'message': 'incorrect data'}),
                               content_type='application/json')
    return validated
