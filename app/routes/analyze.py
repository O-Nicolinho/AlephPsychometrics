# app/routes/analyze.py
import os

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from pydantic import BaseModel, Field, ConfigDict

from app.routes.quiz import limiter, templates
router = APIRouter()

# Where the model service lives. Locally: the second uvicorn on port 8001.
MODEL_URL = os.getenv("MODEL_URL", "http://localhost:8001")

# we make it slightly longer than the model service's WAIT_TIMEOUT (200 s),
# so the model service always gets to answer (or time out) first.
MODEL_TIMEOUT = 210


class AnalyzeRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    text: str = Field(min_length=200, max_length=100000)


@router.post("/api/analyze")
@limiter.limit("5/minute;30/day")
async def analyze(request: Request, body: AnalyzeRequest):
    try:
        async with httpx.AsyncClient(timeout=MODEL_TIMEOUT) as client:
            resp = await client.post(f"{MODEL_URL}/predict", json={"text": body.text})
    except httpx.TimeoutException:
        raise HTTPException(504, "The analysis took too long. Please try again with a shorter text.")
    except httpx.RequestError:
        raise HTTPException(503, "The analysis service is unavailable right now. Please try again later.")

    if resp.status_code == 200:
        return resp.json()

    # Errors the user can act on: pass the model service's message through.
    if resp.status_code in (422, 429, 503, 504):
        try:
            detail = resp.json().get("detail", "Something went wrong.")
        except ValueError:
            detail = "Something went wrong."
        if not isinstance(detail, str):   # Pydantic errors arrive as a list
            detail = "Please check your text and try again."
        raise HTTPException(resp.status_code, detail)

    # Anything else is our bug, not the user's.
    raise HTTPException(502, "Something went wrong while analysing your text.")

@router.get("/analyze", response_class=HTMLResponse)
def analyze_page(request: Request):
    return templates.TemplateResponse(request, "analyze.html")