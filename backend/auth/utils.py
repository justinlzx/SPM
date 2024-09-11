import hashlib
import uuid

def hash_password(password: str, salt: str) -> str:
    """Hash a password with a salt using SHA-256."""
    return hashlib.sha256((password + salt).encode()).hexdigest()

def verify_password(input_password: str, stored_hash: str, salt: str) -> bool:
    """Verify the password by comparing the hashed input password with the stored hash."""
    return hash_password(input_password, salt) == stored_hash

def generate_uuid() -> str:
    """Generate a unique UUID for each user."""
    return str(uuid.uuid4())
