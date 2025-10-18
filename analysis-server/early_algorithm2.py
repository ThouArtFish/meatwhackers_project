import spacy
from transformers import pipeline
from textblob import TextBlob
import torch


class TextAnalyzer:
    def __init__(self, text):
        self.text = text
        self.nlp = spacy.load("en_core_web_lg")
        self.doc = self.nlp(text)
        self.phrases = [sent.text for sent in self.doc.sents]

        self.classifier = pipeline(
            "zero-shot-classification",
            model="typeform/distilbert-base-uncased-mnli",
            device=0 if torch.cuda.is_available() else -1,
            batch_size=16,
            truncation=True
        )

        self.categories = [
            "direct evidence (e.g., eyewitness accounts, video, confessions)",
            "hearsay evidence (Someonte told me, I heard, the rumour is etc)",
            "no evidence or simple fact"
        ]

        self.highlight_sentences = {"evidence": []}
        self.months = {'january', 'february', 'march', 'april', 'may', 'june', 'july',
                       'august', 'september', 'october', 'november', 'december',
                       'jan', 'feb', 'mar', 'apr', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'}


    def polarity(self, sentence):
        return TextBlob(sentence).polarity


    def subjectivity(self, sentence):
        return TextBlob(sentence).subjectivity

    # --- Evidence Scoring ---
    def _highlight_sentence(self, sentence, score):
        if score == 1:
            self.highlight_sentences["evidence"].append(sentence)
        elif score == -1:
            self.highlight_sentences.setdefault("hearsay", []).append(sentence)

    def evidence_score(self, phrase):
        result = self.classifier(phrase, self.categories)
        label = result['labels'][0]
        score = 0
        if label == self.categories[0]:
            score = 1
        elif label == self.categories[1]:
            score = -1

        self._highlight_sentence(phrase, score)
        multiplier = result['scores'][0]
        return multiplier * score

    # --- Line-level Scores ---
    def line_scores(self):
        return [
            [phrase, self.subjectivity(phrase), self.evidence_score(phrase)]
            for phrase in self.phrases
        ]

    # --- Entity Highlighting ---
    def highlight_words(self):
        categories = {
            "person": [], "org": [], "gpe": [], "date": [], "time": [],
            "money": [], "percent": [], "cardinal": [], "law": [], "event": []
        }

        for ent in self.doc.ents:
            label = ent.label_
            if label == "PERSON":
                categories["person"].append(ent.text)
            elif label == "ORG":
                categories["org"].append(ent.text)
            elif label == "GPE":
                categories["gpe"].append(ent.text)
            elif label == "DATE":
                if any(char.isdigit() for char in ent.text) or ent.text.lower() in self.months:
                    categories["date"].append(ent.text)
            elif label == "TIME":
                categories["time"].append(ent.text)
            elif label == "MONEY":
                categories["money"].append(ent.text)
            elif label == "PERCENT":
                categories["percent"].append(ent.text)
            elif label == "CARDINAL":
                categories["cardinal"].append(ent.text)
            elif label == "LAW":
                categories["law"].append(ent.text)
            elif label == "EVENT":
                categories["event"].append(ent.text)

        return {k: set(v) for k, v in categories.items() if v}

    # --- Aggregate Score ---
    def calculate_score(self):
        sub_scores = sum(self.subjectivity(p) for p in self.phrases)
        evi_scores = sum(self.evidence_score(p) for p in self.phrases)
        sub_count = len(self.phrases)
        evi_count = len(self.phrases)
        polarity_score = TextBlob(self.text).polarity

      
        subjectivity_scaled = (sub_scores / sub_count * 2) - 1
        evidence_scaled = max(min(evi_scores / evi_count, 1), -1)
        polarity_score = max(min(polarity_score, 1), -1)

        total = max(min((subjectivity_scaled + polarity_score + evidence_scaled) / 3, 1), -1)

        return round(subjectivity_scaled, 2), round(polarity_score, 2), round(evidence_scaled, 2), round(total, 2)

    # --- Main Report ---
    def report(self):
        subjectivity, polarity, evidence, total = self.calculate_score()
        highlighted_sentences = self.highlight_sentences
        highlighted_words = self.highlight_words()
        return subjectivity, polarity, evidence, total, {"highlighted_sentences": highlighted_sentences}, {"highlighted_words": highlighted_words}


if __name__ == '__main__':
    text = ''''The brother of Virginia Giuffre has called on King Charles to strip Prince Andrew of the title "prince" after he announced he is giving up his other titles, including the Duke of York.

    Ms Giuffre alleged she was forced to have sex with the prince on three occasions, including when she was aged 17 at the home of his friend Ghislaine Maxwell in London in 2001.

    The prince made a financial payment to Ms Giuffre in an out-of-court settlement in 2022, after she had brought a civil case against him. He denies all the accusations against him.

    Sky Roberts told BBC Newsnight his sister, who took her own life earlier this year, would be "very proud" of the latest development regarding Prince Andrew.

    The prince has been under increasing pressure over his links with sex offender Jeffrey Epstein, with calls for Buckingham Palace to take action against him.

    On Friday, the prince announced that he was deciding to voluntarily hand back his titles and to give up membership of the Order of the Garter, the oldest and most senior order of chivalry in Britain.

    He will also cease be the Duke of York, a title received from his mother, the late Queen Elizabeth II.

    But Mr Roberts said he would like to see the King go a step further, saying: "We would call on the King to potentially go ahead and take out the prince in the Andrew."

    "I think anybody that was implicated in this should have some sort of resolve. They should have some sort of responsibility and accountability for these survivors," he said, adding that he would "welcome any contact from the King, from members of parliament".

    When Prince Andrew was born in 1960, he was automatically a prince as the son of a monarch. This could only be changed if a Letters Patent was issued by the King. '''
    
    analyzer = TextAnalyzer(text)
    S,P,E,T,HS,HW= analyzer.report()
    print(S,P,E,T,HS,HW)