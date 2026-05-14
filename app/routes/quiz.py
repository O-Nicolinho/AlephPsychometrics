# app/routes/quiz.py
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import SessionLocal
from app.models import QuizSession, ItemResponse, BigFiveScore
from app.schemas import QuizSubmission, QuizResult
from app.services.scoring import score_big_five, score_jung
from app.services.quality import validate_responses, reliability_score
from app.questions.csv_questions import csv_questions

import random

router = APIRouter()
templates = Jinja2Templates(directory="templates")


# gives us a fresh db session per request, closes it when done
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
def submit_quiz(submission: QuizSubmission, request: Request, db: Session = Depends(get_db)):

    is_repeat = request.cookies.get("has_taken_quiz") == "true"
    # step 1: flatten the list of ItemAnswer objects into a simple dict
    # {question_id: answer, question_id: answer, ...}
    responses = {}
    for item in submission.responses:
        responses[item.question_id] = item.answer

    # step 2: validate
    valid, reason = validate_responses(responses)
    if not valid:
        # 400 = bad request, tells the frontend something was wrong with their data
        raise HTTPException(status_code=400, detail=reason)

    # step 3: reliability: is this submission trustworthy?
    reliable = reliability_score(responses)

    # step 4: score the responses
    big_five = score_big_five(responses)
    jungian = score_jung(responses)

    # step 5: create the quiz session row
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
    # flush pushes the session to the db so it gets an id,
    # but doesnt commit yet,  we want everything in one transaction
    db.flush()

    # step 6: create an ItemResponse row for every single answer
    for qid, ans in responses.items():
        item = ItemResponse(
            session_id=session.id,
            question_id=str(qid),
            answer=ans,
        )
        db.add(item)

    # step 7: create the big five score row
    score = BigFiveScore(
        session_id=session.id,
        openness=big_five["o"],
        conscientiousness=big_five["c"],
        extraversion=big_five["e"],
        agreeableness=big_five["a"],
        neuroticism=big_five["n"],
    )
    db.add(score)

    # step 8: commit writes everything to postgres in one shot
    # if anything fails, nothing gets saved (thats what transactions do)
    db.commit()

    # step 9: send the scores back to the frontend
    return {
        "session_id": str(session.id),
        "big_five": big_five,
        "jungian": jungian,
        "reliable": reliable,
    }

@router.get("/results/{session_id}", response_class=HTMLResponse)
def results_page(session_id: str, request: Request, db: Session = Depends(get_db)):
    # look up the session and its scores from the db
    session = db.query(QuizSession).filter(QuizSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # get the big five scores
    big_five = {
        "o": session.big_five_score.openness,
        "c": session.big_five_score.conscientiousness,
        "e": session.big_five_score.extraversion,
        "a": session.big_five_score.agreeableness,
        "n": session.big_five_score.neuroticism,
    }

    # for jungian scores, we need to recompute from responses
    # since we dont have a JungianScore table yet
    responses = {}
    for r in session.responses:
        responses[int(r.question_id)] = r.answer
    jungian = score_jung(responses)

    return templates.TemplateResponse(request, "results.html", {
        "big_five": big_five,
        "jungian": jungian,
    })