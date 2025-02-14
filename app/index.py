from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import re
import nltk
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from spellchecker import SpellChecker
import os

# Initialize FastAPI
app = FastAPI()

# Download necessary NLTK resources
nltk.download('punkt')
nltk.download('wordnet')

# Ensure the CEFR file exists
CEFR_FILE = "app/cefr-vocab.csv"
if not os.path.exists(CEFR_FILE):
    raise FileNotFoundError(f"Missing CEFR vocabulary file: {CEFR_FILE}")

# Load CEFR word list
cefr_vocab = pd.read_csv(CEFR_FILE)

# Fix column names in case of extra spaces
cefr_vocab.columns = cefr_vocab.columns.str.strip()

# Convert CSV to dictionary
cefr_dict = dict(zip(cefr_vocab["headword"].str.lower(), cefr_vocab["CEFR"]))

# Initialize utilities
lemmatizer = WordNetLemmatizer()
spell = SpellChecker()

# Pydantic model for request body
class TextInput(BaseModel):
    text: str

# Function to analyze CEFR level of words
def cefr_analysis(text):
    words = word_tokenize(re.sub(r"[^\w\s]", "", text.lower()))
    lemmatized_words = [lemmatizer.lemmatize(word) for word in words]

    cefr_result = {word: cefr_dict.get(word, "uncategorized") for word in lemmatized_words}
    
    # Count words per CEFR level
    cefr_count = {}
    for word, level in cefr_result.items():
        cefr_count[level] = cefr_count.get(level, 0) + 1
    
    return cefr_result, cefr_count

# Function for simple spell correction
def correct_spelling(text):
    words = word_tokenize(text.lower())
    corrected_words = [
        spell.correction(word) if spell.correction(word) else word
        for word in words
    ]
    return " ".join(corrected_words)

# Function to calculate an overall CEFR level
def determine_cefr_level(cefr_count):
    levels = {"A1": 1, "A2": 2, "B1": 3, "B2": 4, "C1": 5, "C2": 6}
    
    score = sum(levels.get(level, 0) * count for level, count in cefr_count.items())
    total_words = sum(cefr_count.values())
    
    if total_words == 0:
        return "Unknown"
    
    avg_score = score / total_words
    
    if avg_score <= 1.5:
        return "A1"
    elif avg_score <= 2.5:
        return "A2"
    elif avg_score <= 3.5:
        return "B1"
    elif avg_score <= 4.5:
        return "B2"
    elif avg_score <= 5.5:
        return "C1"
    else:
        return "C2"

# API Endpoint
@app.post("/feedback/")
async def analyze_text(input_data: TextInput):
    text = input_data.text.strip()
    
    if not text:
        raise HTTPException(status_code=400, detail="Input text cannot be empty.")
    
    corrected_text = correct_spelling(text)
    cefr_result, cefr_count = cefr_analysis(corrected_text)
    overall_level = determine_cefr_level(cefr_count)

    return {
        "original_text": text,
        "corrected_text": corrected_text,
        "cefr_analysis": cefr_result,
        "cefr_count": cefr_count,
        "overall_cefr_level": overall_level
    }
