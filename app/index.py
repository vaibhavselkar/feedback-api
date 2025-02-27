from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from spellchecker import SpellChecker
from gingerit.gingerit import GingerIt
import spacy
import csv
import re
from collections import Counter
from fastapi.middleware.cors import CORSMiddleware

# Initialize FastAPI
app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# Load spaCy NLP Model
nlp = spacy.load("en_core_web_sm")

# Load Spell Checker
spell = SpellChecker()

# Load CEFR Vocabulary from CSV (Replaces Pandas)
cefr_dict = {}
try:
    with open("cefr-vocab.csv", newline='', encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # Skip header
        for row in reader:
            cefr_dict[row[0].lower()] = row[1]  # Store word & CEFR level
except FileNotFoundError:
    raise FileNotFoundError("Missing CEFR vocabulary file: cefr-vocab.csv")

# Request Model
class FeedbackRequest(BaseModel):
    feedback: str

@app.get("/")
async def root():
    return {"message": "Welcome to the Feedback API"}

# ✅ Function to Tokenize & Lemmatize text
def tokenize_and_lemmatize(text):
    doc = nlp(text)
    return [token.lemma_.lower() for token in doc if token.is_alpha]  # Remove punctuations

# ✅ Function to Analyze CEFR Levels
def analyze_cefr_levels(text):
    words = tokenize_and_lemmatize(text)
    cefr_mapping = {}
    
    for word in words:
        cefr_mapping[word] = cefr_dict.get(word, "uncategorized")  # Get CEFR level

    cefr_counts = dict(Counter(cefr_mapping.values()))  # Count occurrences

    return {"Word Breakdown": cefr_mapping, "CEFR Summary": cefr_counts}

# ✅ Function to Check Spelling
def check_spelling(text):
    words = tokenize_and_lemmatize(text)
    misspelled = spell.unknown(words)
    return {word: spell.correction(word) for word in misspelled}

# ✅ Function to Correct Grammar and Highlight Mistakes
def text_grammar_correction_highlight(input_text):
    sentences = input_text.split(". ")  # Basic sentence splitting using periods
    color_corrected_text = ''
    ginger = GingerIt()

    for sentence in sentences:
        correction = ginger.parse(sentence)  # Get corrected text
        corrected_sentence = correction["result"]

        all_edits = correction["corrections"] if "corrections" in correction else []
        orig = sentence.split()  # Tokenize using simple split
        amend_plus = []
        start = 0

        for edit in all_edits:
            incorrect_word = edit["text"]
            corrected_word = edit["correct"]

            # Highlight incorrect words in RED
            amend_plus.append(f'<span style="background-color:#ffffff;color:#ff3f33">{incorrect_word}</span>')

            # Highlight corrected words in GREEN
            amend_plus.append(f'<span style="color:#07b81a">{corrected_word}</span>')

            start += 1  # Move start index

        amend_plus.extend(orig[start:])  # Add remaining words
        color_corrected_text += ' ' + ' '.join(amend_plus) + '.'  # Append period back

    return color_corrected_text.strip()

@app.post("/feedback/")
async def process_feedback(data: FeedbackRequest):
    try:
        feedback = data.feedback

        # Perform Spell Check
        corrections = check_spelling(feedback)

        # Analyze CEFR Levels
        cefr_table = analyze_cefr_levels(feedback)

        # Correct Grammar with Highlights
        highlighted_text = text_grammar_correction_highlight(feedback)

        return {
            "Original Feedback": feedback,
            "Corrections": corrections,
            "CEFR Table": cefr_table,
            "Grammar Highlighted": highlighted_text
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {str(e)}")

