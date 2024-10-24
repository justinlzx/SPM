import os
from pathlib import Path

from dotenv import load_dotenv

env_path = Path("../../.env")
load_dotenv(dotenv_path=env_path)


class Settings:
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", 587))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD")


settings = Settings()
