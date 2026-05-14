from pydantic import BaseModel, field_validator



class ItemAnswer(BaseModel):
    question_id: int
    answer: int # answers will always take on values from 1-5


class QuizSubmission(BaseModel):
    responses: list[ItemAnswer]
    reddit_username: str | None = None
    self_reported_jung: str | None = None
    type_confidence: int | None = None

    @field_validator("reddit_username")
    @classmethod
    def validate_reddit_username(cls, v):
        if v is None:
            return v
        for char in v:
            if char.isalnum() or char=='-' or char=="_":
                continue
            else:
                raise ValueError("Reddit username contains invalid characters")
        return v



class QuizResult(BaseModel):
    session_id: str
    openness: float
    conscientiousness: float
    extroversion: float
    agreeableness: float
    neuroticism: float