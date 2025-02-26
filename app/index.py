from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from spellchecker import SpellChecker  # ✅ Correct module is `pyspellchecker`
import re

app = FastAPI()
spell = SpellChecker()  # Initialize the spell checker

class FeedbackRequest(BaseModel):
    feedback: str

@app.get("/")
async def root():
    return {"message": "Welcome to the Feedback API"}

@app.post("/feedback/")
async def process_feedback(data: FeedbackRequest):
    try:
        feedback = data.feedback
        
        # Remove special characters
        feedback_cleaned = re.sub(r'[^A-Za-z0-9 ]+', '', feedback)
        
        words = feedback_cleaned.split()
        misspelled = spell.unknown(words)
        corrections = {word: spell.correction(word) for word in misspelled}
        
        return {
            "Original Feedback": feedback,
            "Corrections": corrections
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail="An internal error occurred"
        )
