from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ConfigDict
from model import inference
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
import threading
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=1)
MAX_IN_LINE = 3
WAIT_TIMEOUT = 200

# the amount of people in our inference queue
in_line = 0
in_line_lock = threading.Lock()

def _leave_line(_future):
    global in_line
    with in_line_lock:
        in_line -= 1


limiter = Limiter(key_func=lambda request: "global")

app = FastAPI()
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limited(request: Request, exc:RateLimitExceeded):
    return JSONResponse(status_code=429, content={"detail": "The system is receiving too many requests at the moment. Try again later."})


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
@limiter.limit("60/hour")
def predict(request: Request, inp: InputText):
    global in_line
    # we attempt to grab the counter lock, to add our inf request to the queue
    with in_line_lock:
        # if there are too many people in the queue, we raise
        if in_line >= MAX_IN_LINE:
            raise HTTPException(status_code=503, detail="Lots of people are using this right now. Try again in a minute.")
        in_line += 1

    # we submit our inference request to the queue
    future = executor.submit(inference, inp.text)
    future.add_done_callback(_leave_line)

    try:
        return future.result(timeout=WAIT_TIMEOUT)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    except TimeoutError as e:
        #if we timeout, we cancel the queued up job
        future.cancel()
        raise HTTPException(status_code=504, detail="Took too long. Try a shorter text.") from e
