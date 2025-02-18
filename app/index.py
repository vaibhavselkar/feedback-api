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


# API Endpoint
@app.post("/feedback/")
async def analyze_text(input_data: TextInput):
    text = input_data.text.strip()
    
    if not text:
        raise HTTPException(status_code=400, detail="Input text cannot be empty.")
    
    corrected_text = correct_spelling(text)

    return {
        "original_text": text,
        "corrected_text": corrected_text,
    }
