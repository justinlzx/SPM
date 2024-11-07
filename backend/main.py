import os
from enum import Enum

import uvicorn
from dotenv import load_dotenv

load_dotenv()

ENV = os.getenv("ENV", "development")


class Environment(Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"


if __name__ == "__main__":
    uvicorn.run(
        "src.app:app",
        host="0.0.0.0",
        port=8000,
        reload=ENV == Environment.DEVELOPMENT.value,
    )
