import uuid

from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base

class QuizSession(Base):
    __tablename__ = "quiz_sessions"

    #we're giving a unique id for each and every quiz attempt
    # UUIDS are harder to guess than an increasing counter so
    # that's why we're using em

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    started_at = Column(DateTime,default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    credibility_score = Column(Float, nullable=True)

    responses = relationship("ItemResponse", back_populates="session")

    big_five_Score = relationship("BigFiveScore", back_populates="session", uselist=False)

    #if the user so chooses, they can share their reddit usr
    #may help us train another model in the future
    reddit_username = Column(String, nullable=True)


class ItemResponse(Base):
    __tablename__ = "item_responses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    #links a response to a given quiz session
    session_id = Column(UUID(as_uuid=True), ForeignKey("quiz_sessions.id"), nulabble=False)

    #shows what question was answered, and what the ans was
    question_id = Column(String,nullable=False)
    answer= Column(Integer, nullable=False)

    session = relationship("QuizSession", back_populates="responses")

    class BigFiveScore(Base):
        # so that sqlalchemy knows how to name postgres table
        __tablename__="big_five_scores"

        id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

        session_id = Column(UUID(as_uuid=True), ForeignKey("quiz_sessions.id"), nullable=False)

        openness = Column(Float, nullable=False)
        conscientiousness = Column(Float, nullable=False)
        extroversion = Column(Float, nullable=False)
        agreeableness = Column(Float, nullable=False)
        neuroticism = Column(Float, nullable=False)

        session = relationship("QuizSession", back_populates="big_five_score")





