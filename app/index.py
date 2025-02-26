from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from spellchecker import SpellChecker
import pandas as pd
import re
import nltk
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

# Initialize FastAPI
app = FastAPI()

# Download necessary NLTK resources
nltk.download('punkt')
nltk.download('wordnet')

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
    nopunc_input_text = re.sub(r'[^\w\s]', '', input_text.lower())
    nopunc_input_text = re.sub(r'[0-9]', '', nopunc_input_text)
    words = word_tokenize(nopunc_input_text)
    lemma_words = [lemmatizer.lemmatize(word.lower()) for word in words]

    pos_values = ['v', 'a', 'n', 'r', 's']
    cefr_mapping = {}

    for word in lemma_words:
        if word in word_set:
            cefr_mapping[word] = cefr_dict[word]
        else:
            for pos_value in pos_values:
                changed_word = lemmatizer.lemmatize(word, pos=pos_value)
                if changed_word in word_set:
                    cefr_mapping[word] = cefr_dict[changed_word]
                    break
            else:
                cefr_mapping[word] = 'uncategorized'

    return cefr_mapping

def tabulate_cefr(clean_text):
    """Create a CEFR table from the text analysis."""
    cefr_mapping = cefr_ratings(clean_text)
    cefr_counts = pd.Series(cefr_mapping.values()).value_counts().to_dict()
    return cefr_counts

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
        cefr_table = tabulate_cefr(feedback)

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
