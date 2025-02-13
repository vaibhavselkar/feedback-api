class DictionaryIndex:
    def __init__(self):
        self.words = set()

    def add_word(self, word):
        self.words.add(word)

    def check_word(self, word):
        return word in self.words
