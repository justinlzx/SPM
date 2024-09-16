from pydantic import BaseModel, EmailStr


class UserLogin(BaseModel):
    username: str
    password: str


class UserRegister(BaseModel):
    email: EmailStr
    username: str
    password: str
    role: str
