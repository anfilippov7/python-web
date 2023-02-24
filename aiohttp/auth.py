import bcrypt
from app import get_app
import os

app = get_app()
TOKEN_TTL = int(os.getenv("TOKEN_TTL", 86400))


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def check_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed_password.encode())


