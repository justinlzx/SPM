from fastapi import APIRouter, HTTPException, Form
from .models import EmailModel

router = APIRouter()


@router.post("/send_email")
async def send_email(
    to_email: str = Form(...), subject: str = Form(...), content: str = Form(...)
):
    if not to_email.strip():
        raise HTTPException(status_code=400, detail="Recipient email cannot be empty.")
    if not subject.strip():
        raise HTTPException(status_code=400, detail="Subject cannot be empty.")
    if not content.strip():
        raise HTTPException(status_code=400, detail="Content cannot be empty.")

    sender_email = "zarapetproject@gmail.com"

    email = EmailModel(
        sender_email=sender_email, to_email=to_email, subject=subject, content=content
    )

    result = email.send_email()

    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    return {
        "message": "Email sent successfully!",
        "sender_email": sender_email,
        "to_email": to_email,
        "subject": subject,
        "content": content,
    }
