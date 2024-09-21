import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os


class EmailModel:
    def __init__(self, sender_email, to_email, subject, content):
        self.sender_email = sender_email
        self.to_email = to_email
        self.subject = subject
        self.content = content

    def send_email(self):
        # Get Gmail SMTP settings from environment variables
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = os.getenv('SMTP_PORT', 587)
        smtp_username = os.getenv('SMTP_USERNAME')
        smtp_password = os.getenv('SMTP_PASSWORD')

        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = self.to_email
            msg['Subject'] = self.subject

            # Attach the content (in this case, plain text)
            msg.attach(MIMEText(self.content, 'plain'))

            # Create SMTP session for sending email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()  # Enable security
                server.login(smtp_username, smtp_password)
                server.sendmail(self.sender_email, self.to_email, msg.as_string())

            return {"message": "Email sent successfully!"}
        except Exception as e:
            return {"error": str(e)}
