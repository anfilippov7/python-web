from pydantic import BaseModel, validator, ValidationError, EmailStr
from errors import HttpError
from typing import Any, Dict, Type, Union
import re
import os

PASSWORD_LENGTH = int(os.getenv("PASSWORD_LENGTH", 7))
PASSWORD_REGEX = re.compile(
    "^(?=.*?[A-Z])(?=.*?[a-z])(?=.*?[0-9])(?=.*?[#?!@$%^&*-])*.{{{password_length},}}$".format(
        password_length=PASSWORD_LENGTH
    )
)


class Register(BaseModel):

    username: Union[str, int]
    e_mail: EmailStr
    password: str

    @validator("password")
    def strong_password(cls, value: str):
        if not PASSWORD_REGEX.match(value):
            raise ValueError("password is to easy")
        return value


class Login(BaseModel):

    username: Union[str, int]
    e_mail: EmailStr
    password: str


SCHEMA_TYPE = Union[Type[Register], Type[Login]]


def validate(schema: SCHEMA_TYPE, data: Dict[str, Any], exclude_none: bool = True) -> dict:
    try:
        validated = schema(**data).dict(exclude_none=exclude_none)
    except ValidationError as er:
        raise HttpError(400, er.errors())
    return validated


class CreateService(BaseModel):
    heading: str
    description: str


def validate_create_service(json_data):
    try:
        service_schema = CreateService(**json_data)
        return service_schema.dict()
    except ValidationError as er:
        raise HttpError(status_code=400, message=er.errors())



