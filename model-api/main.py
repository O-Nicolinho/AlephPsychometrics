from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, ConfigDict
app = FastAPI()

from model import inference

#this outlines the structure of our input text(for predict)
class InputText(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    text: str = Field(min_length=200, max_length=100000)

#this outlines the structure of our output text(for predict)
class OutputBig5(BaseModel):
    openness: float = Field(ge=0, le=100)
    conscientiousness: float = Field(ge=0, le=100)
    extraversion: float = Field(ge=0, le=100)
    agreeableness: float = Field(ge=0, le=100)
    neuroticism: float = Field(ge=0, le=100)
    truncated: bool


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/predict", response_model=OutputBig5)
def predict(inp: InputText):
    try:
        out = inference(inp.text)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    return out