import asyncio
import os
from contextlib import asynccontextmanager
from venv import logger

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from main import ENV

from .arrangements.commons import models as arrangement_models
from .arrangements.routes import router as arrangement_router
from .arrangements.services import auto_reject_old_requests
from .auth import models as auth_models
from .auth.routes import router as auth_router
from .database import engine
from .email.routes import router as email_router
from .employees import models as employee_models
from .employees.routes import router as employee_router
from .health.health import router as health_router
from .init_db import load_data

"""
Create a context manager to handle the lifespan of the FastAPI application
Code before the yield keyword is run before the application starts
Code after the yield keyword is run after the application stops
"""

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info(f"App started in <{ENV}> mode")
    # Drop all tables
    arrangement_models.Base.metadata.drop_all(bind=engine)
    auth_models.Base.metadata.drop_all(bind=engine)
    employee_models.Base.metadata.drop_all(bind=engine)

    # Recreate all tables
    arrangement_models.Base.metadata.create_all(bind=engine)
    auth_models.Base.metadata.create_all(bind=engine)
    employee_models.Base.metadata.create_all(bind=engine)

    # Load employee data from CSV
    load_data.load_employee_data_from_csv("./src/init_db/employee.csv")

    # Load auth data from CSV
    load_data.load_auth_data_from_csv("./src/init_db/auth.csv")

    # Load arrangements data from CSV
    load_data.load_latest_arrangement_data_from_csv("./src/init_db/latest_arrangement.csv")

    # Startup: Initialize services before the application starts
    print("Starting scheduler...")
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        lambda: asyncio.run(auto_reject_old_requests()),
        CronTrigger(hour=0, minute=0),  # Run every day at midnight
        id="auto_reject_job",
        replace_existing=True,
        misfire_grace_time=300,  # 5 minutes grace time
        max_instances=1,  # Ensure only one instance runs at a time
    )
    scheduler.start()

    yield

    # Shutdown: Clean up resources when the application is shutting down
    print("Stopping scheduler...")
    scheduler.shutdown(wait=False)

    # Drop all tables
    arrangement_models.Base.metadata.drop_all(bind=engine)
    auth_models.Base.metadata.drop_all(bind=engine)
    employee_models.Base.metadata.drop_all(bind=engine)


app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:3002",
    os.getenv("FRONTEND_URL", "localhost"),  # for docker networking
]

# Add CORS middleware to allow requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# Include the auth and user routes
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
# app.include_router(users_router, prefix="/users", tags=["Users"])
app.include_router(health_router, prefix="/health", tags=["Health"])
app.include_router(employee_router, prefix="/employees", tags=["Employees"])
app.include_router(email_router, prefix="/email", tags=["Email"])
app.include_router(arrangement_router, prefix="/arrangements", tags=["Arrangements"])
