import logging
import os
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from .exceptions import InvalidEmailException


class EmailModel:
    def __init__(self, sender_email, to_email, subject, content):
        if not self.is_valid_email(sender_email):
            raise InvalidEmailException(f"Invalid sender email: {sender_email}")
        if not self.is_valid_email(to_email):
            raise InvalidEmailException(f"Invalid recipient email: {to_email}")
        self.sender_email = sender_email
        self.to_email = to_email
        self.subject = subject
        self.content = content

    def is_valid_email(self, email):
        # Simple regex for validating an email
        regex = r"^\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        return re.match(regex, email) is not None

    async def send_email(self):
        # Get Gmail SMTP settings from environment variables
        smtp_server = os.getenv("SMTP_SERVER", "SMTP_SERVER")
        smtp_port = os.getenv("SMTP_PORT", "SMTP_PORT")
        smtp_username = os.getenv("SMTP_USERNAME")
        smtp_password = os.getenv("SMTP_PASSWORD")

        msg = MIMEMultipart()
        msg["From"] = self.sender_email
        msg["To"] = self.to_email
        msg["Subject"] = self.subject

        # Attach the content (in this case, plain text)
        msg.attach(MIMEText(self.content, "plain"))

        # Create SMTP session for sending email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            logging.debug("SMTP session created")
            server.starttls()  # Enable security
            logging.debug("starttls called")
            server.login(smtp_username, smtp_password)
            logging.debug("Logged in to SMTP server")
            server.sendmail(self.sender_email, self.to_email, msg.as_string())
            logging.debug("Email sent")

        return {"message": "Email sent successfully!"}
