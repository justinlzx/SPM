from auth.models import Base
from auth.routes import router as auth_router
from database import engine
from fastapi import FastAPI
from users.routes import router as users_router

app = FastAPI()

Base.metadata.create_all(bind=engine)

# Include the auth and user routes
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(users_router, prefix="/users", tags=["Users"])
