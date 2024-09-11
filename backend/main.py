from fastapi import FastAPI
from auth.routes import router as auth_router
from users.routes import router as users_router

app = FastAPI()

# Include the auth and user routes
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(users_router, prefix="/users", tags=["Users"])
