import nltk
from nltk.corpus import wordnet as wn

words = ["Some may say"]

synonyms = set()

for word in words:
    for synset in wn.synsets(word):
        for lemma in synset.lemmas():
            synonyms.add(lemma.name())

print(sorted(synonyms))