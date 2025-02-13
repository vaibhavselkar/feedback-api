from spellchecker import SpellChecker

def check_spelling(text: str) -> str:
    spell = SpellChecker()
    words = text.split()
    corrected_words = [spell.correction(word) if spell.unknown([word]) else word for word in words]
    return " ".join(corrected_words)
