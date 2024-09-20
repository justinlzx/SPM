from typing import Optional

from pydantic import BaseModel, EmailStr


class User(BaseModel):
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None
