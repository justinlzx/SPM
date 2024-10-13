from fastapi import APIRouter, Form, HTTPException

from . import models

router = APIRouter()


@router.post("/sendemail")
async def send_email(to_email: str = Form(...), subject: str = Form(...), content: str = Form(...)):
    if not to_email.strip():
        raise HTTPException(status_code=400, detail="Recipient email cannot be empty.")
    if not subject.strip():
        raise HTTPException(status_code=400, detail="Subject cannot be empty.")
    if not content.strip():
        raise HTTPException(status_code=400, detail="Content cannot be empty.")

    sender_email = "zarapetproject@gmail.com"

    email = models.EmailModel(
        sender_email=sender_email, to_email=to_email, subject=subject, content=content
    )

    result = await email.send_email()

    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    return {
        "message": "Email sent successfully!",
        "sender_email": sender_email,
        "to_email": to_email,
        "subject": subject,
        "content": content,
    }
