from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from app.database import engine, Base
from app.routes.quiz import router as quiz_router, limiter

import app.models

Base.metadata.create_all(bind=engine)

app = FastAPI()
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request, exc):
    return JSONResponse(status_code=429, content={"detail": "Too many requests. Try again later."})

app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(quiz_router)