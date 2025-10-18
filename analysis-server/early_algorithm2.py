import spacy
from transformers import pipeline
from textblob import TextBlob
import torch

from webscraper import BBCArticleScraper

def MainScore(scraper: BBCArticleScraper):
    text = scraper.get_text_content()

    # Initialise classifier for evidence categories
    classifier = pipeline("zero-shot-classification",
                     model="typeform/distilbert-base-uncased-mnli",
                     device=0 if torch.cuda.is_available() else -1,
                     batch_size=16,
                     truncation=True)

    # Define your categories
    categories = ["direct evidence (e.g., eyewitness accounts, video, confessions)",  
                "hearsay evidence (Someonte told me, I heard, the rumour is etc)", 
                "no evidence or simple fact"]

    nlp = spacy.load("en_core_web_lg")

    months = {'january','february','march','april','may','june','july', 
              'august','september','october','november','december',
              'jan','feb','mar','apr','jun','jul','aug','sep','oct','nov','dec'}

    doc = nlp(text)
    phrases = [sent.text for sent in doc.sents]

    highlight_sentences = []

    def HighlightSentence(sentence, result):
        if result == 1:
            highlight_sentences.append({"text": sentence, "type": "evidence"})
        elif result == -1:
            highlight_sentences.append({"text": sentence, "type": "hearsay"})

    def EvidenceScore(phrase):
        result = classifier(phrase, categories)
        label = result['labels'][0]
        score = 0
        if label == categories[0]:
            score = 1
        elif label == categories[1]:
            score = -1
        HighlightSentence(phrase, score)
        return score * result['scores'][0]

    sub_scores = sum([TextBlob(p).subjectivity for p in phrases])
    evi_scores = sum([EvidenceScore(p) for p in phrases])
    scount = len(phrases)
    ecount = len(phrases)
    pol = TextBlob(text).polarity

    # Scale and combine scores
    subjectivity_scaled = (sub_scores / scount) * 2 - 1
    evidence_scaled = max(min(evi_scores / ecount, 1), -1)
    pol = max(min(pol, 1), -1)
    total = max(min((subjectivity_scaled + evidence_scaled + pol)/3, 1), -1)

    # Extract entities
    entities = {"person": [], "org": [], "gpe": [], "date": [], "time": [],
                "money": [], "percent": [], "cardinal": [], "law": [], "event": []}
    for ent in doc.ents:
        key = ent.label_.lower() if ent.label_ != "GPE" else "gpe"
        if key in entities:
            if key == "date" and not (any(c.isdigit() for c in ent.text) or ent.text.lower() in months):
                continue
            entities[key].append(ent.text)
    entities = {k: list(set(v)) for k,v in entities.items() if v}

    # Minimal change: return as dictionary
    result = {
        "scores": {
            "subjectivity": round(subjectivity_scaled, 2),
            "polarity": round(pol, 2),
            "evidence": round(evidence_scaled, 2),
            "total": round(total, 2)
        },
        "highlighted_sentences": highlight_sentences,
        "entities": entities
    }

    return result