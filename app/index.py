from fastapi import FastAPI
import pandas as pd
import re
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.stem import WordNetLemmatizer
from spellchecker import SpellChecker
import spacy
import torch
from gramformer import Gramformer
from collections import defaultdict

# Initialize FastAPI app
app = FastAPI()

# Download necessary resources
nltk.download('punkt')
nltk.download('wordnet')

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# Load CEFR vocabulary
cefr_vocab = pd.read_csv("data/cefr-vocab-cefrj-octanove.csv")
cefr_dict = {k: v for k, v in cefr_vocab[['headword', 'CEFR']].values}
word_set = set(cefr_vocab.headword)

# Initialize spell checker and lemmatizer
lemmatizer = WordNetLemmatizer()
spell = SpellChecker()

# Initialize Gramformer for grammar correction
torch.manual_seed(1212)
gf = Gramformer(models=1, use_gpu=False)  # Model 1 = corrector

# Function to get CEFR ratings of words in input text
def cefr_ratings(input_text):
    words = word_tokenize(re.sub(r'[^\w\s]', '', input_text.lower()))
    lemma_words = [lemmatizer.lemmatize(word) for word in words]

    cefr_counts = defaultdict(int)
    cefr_mapping = {}
    
    for word in lemma_words:
        if word in word_set:
            cefr_mapping[word] = cefr_dict[word]
            cefr_counts[cefr_dict[word]] += 1
        else:
            cefr_mapping[word] = "uncategorized"
            cefr_counts["uncategorized"] += 1

    return cefr_mapping, dict(cefr_counts)

# Grammar correction function
def text_grammar_correction(input_text):
    sentences = sent_tokenize(input_text)
    corrected_text = ""

    for sentence in sentences:
        corrected_sentences = gf.correct(sentence, max_candidates=1)
        for corrected_sentence in corrected_sentences:
            corrected_text += corrected_sentence + " "

    return corrected_text.strip()

# Spell check function
def sentence_spelling_correction(input_text):
    words = word_tokenize(input_text.lower())
    corrected_words = [spell.correction(word) if word in spell.unknown([word]) else word for word in words]
    return " ".join(corrected_words) + "."

# API endpoint for text analysis
@app.post("/analyze/")
async def analyze_text(text: str):
    # Step 1: Spell Check
    corrected_spelling_text = sentence_spelling_correction(text)

    # Step 2: Grammar Correction
    corrected_text = text_grammar_correction(corrected_spelling_text)

    # Step 3: CEFR Analysis
    cefr_mapping, cefr_counts = cefr_ratings(corrected_text)

    return {
        "original_text": text,
        "corrected_text": corrected_text,
        "cefr_word_levels": cefr_mapping,
        "cefr_distribution": cefr_counts
    }
