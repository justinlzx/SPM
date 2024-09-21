from pydantic import BaseModel, EmailStr


class EmailSchema(BaseModel):
    sender_email: EmailStr
    to_email: EmailStr
    subject: str
    content: str
