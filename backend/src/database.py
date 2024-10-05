from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
import os

if os.getenv("ENV") == "TEST":
    SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
else:
    SQLALCHEMY_DATABASE_URL = "sqlite:///./app.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# from sqlalchemy import create_engine
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import sessionmaker

# SQLALCHEMY_DATABASE_URL = "sqlite:///./app.db"

# db = None


# class Database:
#     def __init__(self):
#         self.engine = create_engine(
#             SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
#         )
#         self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
#         self.db = self.SessionLocal()
#         self.Base = declarative_base()

#     def get_db(self):
#         try:
#             yield self.db
#         finally:
#             self.db.close()


#     def get_Base(self):
#         return self.Base
