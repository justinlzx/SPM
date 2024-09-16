from typing import Optional
from pydantic import BaseModel, EmailStr


class User(BaseModel):
    email: EmailStr
    username: str
    password: str
    role: str


class UserLogin(User):
    email: Optional[EmailStr] = None
    role: Optional[str] = None
