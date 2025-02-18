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

nltk.download('punkt')

app = Flask(__name__)
CORS(app)
spell = SpellChecker()

# Ensure the CEFR file exists
CEFR_FILE = "api/cefr-vocab.csv"
if not os.path.exists(CEFR_FILE):
    raise FileNotFoundError(f"Missing CEFR vocabulary file: {CEFR_FILE}")

# Load CEFR word list
cefr_vocab = pd.read_csv(CEFR_FILE)
cefr_dict = {k : v for k,v in cefr_vocab[['headword', 'CEFR']].values}
word_set = set(cefr_vocab.headword)

grammar_fullforms ={'ADV': 'Adverb', 'PREP': 'Prepositions', 'PRON': 'Pronoun', 'WO': 'Wrong Order', 'VERB': 'Verbs', 'VERB:SVA': 'Singular-Plural', 'VERB:TENSE': 'Verb Tenses', 'VERB:FORM': 'Verb Forms', 'VERB:INFL': 'Verbs', 'SPELL': 'Spelling', 'OTHER': 'Other', 'NOUN': 'Other', 'NOUN:NUM': 'Singular-Plural', 'DET': 'Articles', 'MORPH': 'Other', 'ADJ': 'Adjectives', 'PART': 'Other', 'ORTH': 'Other', 'CONJ': 'Conjugations', 'PUNCT': 'Punctuation'}

def tabulating_cefr(clean_text):
    cefr_mapping = cefr_ratings(clean_text)
    cefr_df = pd.DataFrame(pd.Series(cefr_mapping.values()).value_counts())
    print(cefr_df)
    return [word for word in cefr_mapping.keys() if cefr_mapping[word] == 'uncategorized']


def cefr_ratings(input_words):
    words = word_tokenize(input_words)
    lemma_words = [lemmatizer.lemmatize(word.lower()) for word in words]

    pos_values = ['v', 'a', 'n', 'r', 's']

    cefr_list = []
    cefr_mapping = {}
    for word in lemma_words:
        if word in word_set:
            cefr_list.append(cefr_dict[word])
            cefr_mapping[word] = cefr_dict[word]
        else:      
            for pos_value in pos_values:
                changed_word = lemmatizer.lemmatize(word, pos = pos_value)
                if changed_word != word:
                    break
            if changed_word in word_set:
                cefr_list.append(cefr_dict[changed_word])
                cefr_mapping[changed_word] = cefr_dict[changed_word]
            else:
                #print(changed_word)
                cefr_list.append('uncategorized')
                cefr_mapping[changed_word] = 'uncategorized'
    return cefr_mapping

@app.route('/')
def home():
    return 'Hello, World!'

@app.route('/about')
def about():
    return 'About'

@app.route('/run-python', methods=['POST'])
def run_python():

    data = request.json
    code = data.get('code', '')

    try:
        # Execute the Python code
        result = subprocess.run(
            ['python3', '-c', code],
            capture_output=True,
            text=True,
            timeout=15  # Limit execution time
        )
        output = result.stdout
        if result.returncode != 0:
            output = result.stderr
    except subprocess.TimeoutExpired:
        output = "Execution timed out."

    return jsonify({'output': output})

@app.route('/feedback', methods=['POST'])
def feedback():
    try:
        data = request.get_json()
        if not data or 'feedback' not in data or not isinstance(data['feedback'], str):
            return jsonify({"error": "Invalid input, please provide 'feedback' as a string in JSON format"}), 400
        
        feedback = data['feedback']
        # Remove special characters
        feedback_cleaned = re.sub('[^A-Za-z0-9 ]+', '', feedback)
        
        words = feedback_cleaned.split()
        misspelled = spell.unknown(words)
        corrections = {word: spell.correction(word) for word in misspelled}

        table = tabulating_cefr(cefr_ratings(words))
        
        return jsonify({
            "Original Feedback": feedback,
            "Corrections": corrections,
            "cefr": table
        })
    
    except Exception as e:
        # Log the error and return a 500 response
        app.logger.error(f"An error occurred: {e}")
        return jsonify({"error": "An internal error occurred"}), 500

@app.route('/feedback', methods=['GET'])
def get_feedback_template():
    template = {
        "feedback": "This is an example feedback with some speling errors."
    }
    return jsonify(template)

if __name__ == '__main__':
    app.run(debug=True)
