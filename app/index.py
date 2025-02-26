from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.spell_checker import check_spelling

app = FastAPI()

class FeedbackRequest(BaseModel):
    feedback: str

@app.get("/")
def root():
    return {"message": "Welcome to the Feedback API"}

@app.post("/feedback/")
def process_feedback(data: FeedbackRequest):
    corrected_feedback = check_spelling(data.feedback)
    return {"original": data.feedback, "corrected": corrected_feedback}
