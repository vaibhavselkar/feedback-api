from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.spell_checker import check_spelling
from spellchecker import SpellChecker
import re

app = FastAPI()

class FeedbackRequest(BaseModel):
    feedback: str

@app.get("/")
def root():
    return {"message": "Welcome to the Feedback API"}

@app.post("/feedback/")
def process_feedback(data: FeedbackRequest):
    try:
        if not data or 'feedback' not in data or not isinstance(data['feedback'], str):
            return jsonify({"error": "Invalid input, please provide 'feedback' as a string in JSON format"}), 400
        
        feedback = data['feedback']
        # Remove special characters
        feedback_cleaned = re.sub('[^A-Za-z0-9 ]+', '', feedback)
        
        words = feedback_cleaned.split()
        misspelled = spell.unknown(words)
        
        corrections = {word: spell.correction(word) for word in misspelled}
        
        return jsonify({
            "Original Feedback": feedback,
            "Corrections": corrections
        })
    
    except Exception as e:
        # Log the error and return a 500 response
        app.logger.error(f"An error occurred: {e}")
        return jsonify({"error": "An internal error occurred"}), 500
