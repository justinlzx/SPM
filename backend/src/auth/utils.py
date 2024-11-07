import hashlib
import os
from datetime import datetime, timedelta
from typing import Optional
from zoneinfo import ZoneInfo

import jwt
from dotenv import load_dotenv

load_dotenv()

singapore_timezone = ZoneInfo("Asia/Singapore")
TOKEN_SECRET = os.environ.get("TOKEN_SECRET")


def hash_password(password: str, salt: str) -> str:
    """Hash a password with a salt using SHA-256."""
    return hashlib.sha256((password + salt).encode()).hexdigest()


def verify_password(input_password: str, stored_hash: str, salt: str) -> bool:
    """Verify the password by comparing the hashed input password with the stored hash."""
    return hash_password(input_password, salt) == stored_hash


def generate_JWT(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Generate a JWT token for the user."""

    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(singapore_timezone) + expires_delta
    else:
        expire = datetime.now(singapore_timezone) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, TOKEN_SECRET)
    return encoded_jwt
