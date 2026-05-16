# app/routes/quiz.py
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import SessionLocal
from app.models import QuizSession, ItemResponse, BigFiveScore, PersonalitySummary
from app.schemas import QuizSubmission, QuizResult
from app.services.scoring import score_big_five, score_jung
from app.services.quality import validate_responses, reliability_score
from app.services.summary import generate_summary, pick_animal, ANIMALS
from app.questions.csv_questions import csv_questions
from slowapi import Limiter
from slowapi.util import get_remote_address

import random

limiter = Limiter(key_func=get_remote_address)

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    count = db.query(QuizSession).count()
    return templates.TemplateResponse(request, "home.html", {"count": count})

@router.get("/quiz", response_class=HTMLResponse)
def quiz_page(request: Request):
    shuffled = csv_questions.copy()
    random.shuffle(shuffled)
    return templates.TemplateResponse(request, "quiz.html", {"questions": shuffled})

@router.post("/submit")
@limiter.limit("3/minute")
def submit_quiz(submission: QuizSubmission, request: Request, db: Session = Depends(get_db)):

    is_repeat = request.cookies.get("has_taken_quiz") == "true"

    responses = {}
    for item in submission.responses:
        responses[item.question_id] = item.answer

    valid, reason = validate_responses(responses)
    if not valid:
        raise HTTPException(status_code=400, detail=reason)

    reliable = reliability_score(responses)

    big_five = score_big_five(responses)
    jungian = score_jung(responses)

    summary_text = generate_summary(big_five, jungian)
    animal = pick_animal(big_five, jungian)
    if animal not in ANIMALS:
        animal = "koala"

    session = QuizSession(
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
        credibility_score=1.0 if reliable else 0.0,
        reddit_username=submission.reddit_username,
        self_reported_jung=submission.self_reported_jung,
        type_confidence=submission.type_confidence,
        is_repeat=is_repeat,
    )
    db.add(session)
    db.flush()

    for qid, ans in responses.items():
        item = ItemResponse(
            session_id=session.id,
            question_id=str(qid),
            answer=ans,
        )
        db.add(item)

    score = BigFiveScore(
        session_id=session.id,
        openness=big_five["o"],
        conscientiousness=big_five["c"],
        extraversion=big_five["e"],
        agreeableness=big_five["a"],
        neuroticism=big_five["n"],
    )
    db.add(score)

    personality_summary = PersonalitySummary(
        session_id=session.id,
        summary=summary_text,
        animal=animal,
    )
    db.add(personality_summary)

    db.commit()

    return {
        "session_id": str(session.id),
        "big_five": big_five,
        "jungian": jungian,
        "reliable": reliable,
    }

@router.get("/results/{session_id}", response_class=HTMLResponse)
def results_page(session_id: str, request: Request, db: Session = Depends(get_db)):
    session = db.query(QuizSession).filter(QuizSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    big_five = {
        "o": session.big_five_score.openness,
        "c": session.big_five_score.conscientiousness,
        "e": session.big_five_score.extraversion,
        "a": session.big_five_score.agreeableness,
        "n": session.big_five_score.neuroticism,
    }

    responses = {}
    for r in session.responses:
        responses[int(r.question_id)] = r.answer
    jungian = score_jung(responses)

    summary = session.personality_summary.summary if session.personality_summary else None
    animal = session.personality_summary.animal if session.personality_summary else None

    return templates.TemplateResponse(request, "results.html", {
        "big_five": big_five,
        "jungian": jungian,
        "summary": summary,
        "animal": animal,
    })