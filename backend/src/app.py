from contextlib import asynccontextmanager

from fastapi import FastAPI

from .employees import models as employee_models

from .auth import models as auth_models

from .auth.routes import router as auth_router

from .users.routes import router as users_router

from .database import engine

from .init_db import load_data

from fastapi.middleware.cors import CORSMiddleware


"""
Create a context manager to handle the lifespan of the FastAPI application
Code before the yield keyword is run before the application starts
Code after the yield keyword is run after the application stops
"""
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Recreate all tables
    employee_models.Base.metadata.create_all(bind=engine)
    auth_models.Base.metadata.create_all(bind=engine)
    
    # Load employee data from CSV
    load_data.load_employee_data_from_csv("./src/init_db/employee.csv")
    
    yield
    
    # Drop all tables
    employee_models.Base.metadata.drop_all(bind=engine)
    auth_models.Base.metadata.drop_all(bind=engine)

app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost:3000",
]

# middlwares
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allow specific origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
)


# Include the auth and user routes
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(users_router, prefix="/users", tags=["Users"])
