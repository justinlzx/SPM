import hashlib
from typing import Optional
import uuid
import os
import jwt
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

TOKEN_SECRET = os.environ.get("TOKEN_SECRET")


def hash_password(password: str, salt: str) -> str:
    """Hash a password with a salt using SHA-256."""
    return hashlib.sha256((password + salt).encode()).hexdigest()


def verify_password(input_password: str, stored_hash: str, salt: str) -> bool:
    """Verify the password by comparing the hashed input password with the stored hash."""
    return hash_password(input_password, salt) == stored_hash


def generate_uuid() -> str:
    """Generate a unique UUID for each user."""
    return str(uuid.uuid4())

def generate_JWT(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Generate a JWT token for the user."""

    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, TOKEN_SECRET)
    return encoded_jwt

if __name__ == "__main__":
    # Test the hash_password and verify_password functions
    token_data = {"user_id": "uuid1"}
    token = generate_JWT(token_data)
    print(f"Generated JWT: {token}")
