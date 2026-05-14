

from fastapi import FastAPI
from app.database import engine, Base
from app.routes.quiz import router as quiz_router

import app.models

# this makes it so that SQLAlchemy creates our tables in postgres
# it reads the models we created and makes corresponding tables
# does not create dupes
Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(quiz_router)