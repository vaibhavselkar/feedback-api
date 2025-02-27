from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from spellchecker import SpellChecker
import pandas as pd
import re
import nltk
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from collections import Counter
import os
from fastapi.middleware.cors import CORSMiddleware
from gramformer import Gramformer

# Initialize FastAPI
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ✅ Allow all origins (change this in production)
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# Initialize spell checker and lemmatizer
spell = SpellChecker()
lemmatizer = WordNetLemmatizer()
gf = Gramformer(models=1, use_gpu=False)

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
    input = cefr_ratings(input_text)
    cefr_mapping = input["CEFR_Levels"]
    corrections = input["Corrections"]
    cefr_counts = dict(Counter(cefr_mapping.values()))  # Count occurrences

    return {
        "Corrections": corrections,
        "CEFR Summary": cefr_counts
    }

def text_grammar_correction_highlight(input_text):
    """Corrects grammar mistakes and highlights changes in HTML."""
    sentences = input_text.split(". ")  # Simple sentence splitting
    color_corrected_text = ''

    for sentence in sentences:
        corrected_sentences = gf.correct(sentence, max_candidates=1)

        for corrected_sentence in corrected_sentences:
            all_edits = gf.get_edits(sentence, corrected_sentence)
            orig = sentence.split()
            amend_plus = []
            start = 0

            for edit in all_edits:
                amend_plus.extend(orig[start:edit[2]])

                if edit[1]:  # Incorrect word
                    amend_plus.append(f'<span style="background-color:#ffcccc;color:#ff3f33;text-decoration:line-through;">{edit[1]}</span>')

                if edit[4]:  # Corrected word
                    amend_plus.append(f'<span style="color:#07b81a;font-weight:bold;">{edit[4]}</span>')

                start = edit[3]  # Move start index

            amend_plus.extend(orig[start:])
            color_corrected_text += ' ' + ' '.join(amend_plus) + '.'

    return color_corrected_text.strip()

@app.post("/feedback/")
async def process_feedback(data: FeedbackRequest):
    try:
        feedback = data.feedback

        # Remove special characters for spell check
        #feedback_cleaned = re.sub(r'[^A-Za-z0-9 ]+', '', feedback)
        #words = feedback_cleaned.split()
        #misspelled = spell.unknown(words)
        #corrections = {word: spell.correction(word) for word in misspelled}

        # Get CEFR table
        cefr_table = tabulating_cefr(feedback)

        highlighted_text = text_grammar_correction_highlight(feedback)

        return {
            "Corrections": cefr_table["Corrections"],
            "Grammar Highlighted Text": highlighted_text,
            "CEFR Table": cefr_table
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"An internal error occurred: {str(e)}"
        )
