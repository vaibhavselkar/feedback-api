from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from spellchecker import SpellChecker
import pandas as pd
import re
import nltk
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
import os

# Initialize FastAPI
app = FastAPI()

# Initialize spell checker and lemmatizer
spell = SpellChecker()
lemmatizer = WordNetLemmatizer()

# Load CEFR Vocabulary
# Correct path construction
current_dir = os.path.dirname(os.path.abspath(__file__))
CEFR_FILE = os.path.join(current_dir, 'api', 'cefr-vocab.csv')

if not os.path.exists(CEFR_FILE):
    raise FileNotFoundError(f"Missing CEFR vocabulary file: {CEFR_FILE}")

# Load CEFR word list
cefr_vocab = pd.read_csv(CEFR_FILE)

# Load CEFR word list
cefr_vocab = pd.read_csv(CEFR_FILE)
cefr_dict = {k : v for k,v in cefr_vocab[['headword', 'CEFR']].values}
word_set = set(cefr_vocab.headword)

# Define request model
class FeedbackRequest(BaseModel):
    feedback: str

@app.get("/")
async def root():
    return {"message": "Welcome to the Feedback API"}

def cefr_ratings(input_text):
    """Process text to extract CEFR levels for each word."""
    # ✅ Remove punctuation & numbers
    clean_text = re.sub(r'[^\w\s]', '', input_text.lower())  # Remove punctuation
    clean_text = re.sub(r'[0-9]', '', clean_text)  # Remove numbers

    # ✅ Tokenize text (split by spaces instead of NLTK)
    words = clean_text.split()

    # ✅ Check for spelling corrections
    misspelled = spell.unknown(words)
    corrections = {word: spell.correction(word) for word in misspelled}

    cefr_mapping = {}
    for word in words:
        if word in word_set:
            cefr_mapping[word] = cefr_dict[word]
        else:
            cefr_mapping[word] = "uncategorized"

    return {"CEFR_Levels": cefr_mapping, "Corrections": corrections}

def tabulating_cefr(input_text):
    """Tabulate CEFR level counts."""
    cefr_mapping = cefr_ratings(input_text)["CEFR_Levels"]
    cefr_counts = dict(Counter(cefr_mapping.values()))  # Count occurrences

    return {
        "Word Breakdown": cefr_mapping,
        "CEFR Summary": cefr_counts
    }

@app.post("/feedback/")
async def process_feedback(data: FeedbackRequest):
    try:
        feedback = data.feedback

        # Remove special characters for spell check
        feedback_cleaned = re.sub(r'[^A-Za-z0-9 ]+', '', feedback)
        words = feedback_cleaned.split()
        misspelled = spell.unknown(words)
        corrections = {word: spell.correction(word) for word in misspelled}

        # Get CEFR table
        cefr_table = tabulating_cefr(feedback)

        return {
            "Original Feedback": feedback,
            "Corrections": corrections,
            "CEFR Table": cefr_table
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"An internal error occurred: {str(e)}"
        )
