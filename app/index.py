from fastapi import FastAPI
import pandas as pd
import re
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.stem import WordNetLemmatizer
from spellchecker import SpellChecker

# Initialize FastAPI
app = FastAPI()

# Download necessary NLTK resources
nltk.download('punkt')
nltk.download('wordnet')

# Load CEFR word list
cefr_vocab = pd.read_csv('./cefr-vocab.csv')
cefr_dict = dict(zip(cefr_vocab["headword"], cefr_vocab["CEFR"]))

# Initialize utilities
lemmatizer = WordNetLemmatizer()
spell = SpellChecker()

# Function to check CEFR level of words
def cefr_analysis(text):
    words = word_tokenize(re.sub(r'[^\w\s]', '', text.lower()))
    lemmatized_words = [lemmatizer.lemmatize(word) for word in words]

    cefr_result = {word: cefr_dict.get(word, "uncategorized") for word in lemmatized_words}
    return cefr_result

# Simple spell checker
def correct_spelling(text):
    words = word_tokenize(text.lower())
    return " ".join([spell.correction(word) if word in spell.unknown([word]) else word for word in words])

# API Endpoint
@app.post("/analyze/")
async def analyze_text(text: str):
    corrected_text = correct_spelling(text)
    cefr_result = cefr_analysis(corrected_text)

    return {
        "original_text": text,
        "corrected_text": corrected_text,
        "cefr_analysis": cefr_result
    }
