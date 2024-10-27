from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .arrangements import models as arrangement_models
from .arrangements.routes import router as arrangement_router
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


@asynccontextmanager
async def lifespan(app: FastAPI):
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

    yield

    # Drop all tables
    arrangement_models.Base.metadata.drop_all(bind=engine)
    auth_models.Base.metadata.drop_all(bind=engine)
    employee_models.Base.metadata.drop_all(bind=engine)


app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:3002",
    "http://frontend:3000",  # for docker networking
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
