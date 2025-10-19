import spacy
from transformers import pipeline
from textblob import TextBlob
import torch
import math

class TextAnalyzer:
    def __init__(self, text, articles_count):
        self.text = text
        self.articles_count = articles_count
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
                "evidence", "secondhand", "hearsay", "neutral"
        ]

        self.highlighted_sentences = {"evidence": []}
        self.months = {'january', 'february', 'march', 'april', 'may', 'june', 'july',
                       'august', 'september', 'october', 'november', 'december',
                       'jan', 'feb', 'mar', 'apr', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'}

    
    def get_polarity(self, sentence):
        return TextBlob(sentence).polarity


    def get_subjectivity(self, sentence):
        return TextBlob(sentence).subjectivity

    # --- Evidence Scoring ---
    def get_highlighted_sentences(self, sentence, score):
        if score == 1 or score == 0.5:
            self.highlighted_sentences["evidence"].append(sentence)
        elif score == -1:
            self.highlighted_sentences.setdefault("hearsay", []).append(sentence)


    def get_evidence_score(self, phrase):
        result = self.classifier(phrase, self.categories)
        label = result['labels'][0]
        score = 0
        if label == self.categories[0]:
            score = 1
        elif label == self.categories[1]:
            score = 0.5
        elif label == self.categories[2]:
            score = -1
        else:
            score = 0


        self.get_highlighted_sentences(phrase, score)
        multiplier = result['scores'][0]
        return multiplier * score

    # --- Line-level Scores ---
    def get_line_scores(self):
        return [
            [phrase, self.subjectivity(phrase), self.evidence_score(phrase)]
            for phrase in self.phrases
        ]

    # --- Entity Highlighting ---
    def get_highlighted_words(self):
       
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
                if any(char.isdigit() for char in ent.text) or ent.text.lower() in self.months and len(ent.text) > 2:
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
            
        

        highlighted_list = []
        for category, entities in categories.items():
            highlighted_list.extend([{"text": item, "type": category} for item in set(entities)])

        return highlighted_list


    def get_highlighted_phrases(self):
        final_highlighted = []

        for phrase in self.phrases:
            # 1. Check if the sentence is highlighted
            for typ, sentences in self.highlighted_sentences.items():
                if phrase in sentences:
                    final_highlighted.append({"text": phrase, "type": typ})
                    break  # stop after finding the type

            # 2. Get entities in this specific sentence
            doc_phrase = self.nlp(phrase)
            for ent in doc_phrase.ents:
                label = ent.label_
                word_type = None
                if label == "PERSON":
                    word_type = "person"
                elif label == "ORG":
                    word_type = "org"
                elif label == "GPE":
                    word_type = "gpe"
                elif label == "DATE":
                    if any(char.isdigit() for char in ent.text) or (ent.text.lower() in self.months and len(ent.text) > 2):
                        word_type = "date"
                elif label == "TIME":
                    word_type = "time"
                elif label == "MONEY":
                    word_type = "money"
                elif label == "PERCENT":
                    word_type = "percent"
                elif label == "CARDINAL":
                    word_type = "cardinal"
                elif label == "LAW":
                    word_type = "law"
                elif label == "EVENT":
                    word_type = "event"

                if word_type:
                    final_highlighted.append({"text": ent.text, "type": word_type})

        return final_highlighted
    
    # --- Aggregate Score ---
    def calculate_score(self):
        sub_scores = sum(self.get_subjectivity(p) for p in self.phrases)
        evi_scores = sum(self.get_evidence_score(p) for p in self.phrases)
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
    
                
        highlighted_words = self.get_highlighted_words()
        #add score per evidence
        total += 0.01 * len(highlighted_words)

        # Adujst total score based on authors number of written articles
        
        #if no author provided for article
        if self.articles_count == None: 
            adjustment = -0.05
    
        elif self.articles_count < 5:  
            adjustment = -0.025
        else:
            adjustment = 0.05 * math.log10(self.articles_count + 1)  # small boost for more pages

        total += adjustment

        total = max(min(total, 1), -1)

        return subjectivity, polarity, evidence, round(total, 2), self.get_highlighted_phrases()
#ss
#sadasdas
if __name__ == '__main__':
    text = '''Gaza's Hamas-run civil defence says 11 people were killed, all from the same family, after the bus they were in was hit by an Israeli tank shell in northern Gaza.

The Abu Shaaban family, it said, were trying to reach their home to inspect it when the incident happened in the Zeitoun neighbourhood of Gaza City on Friday night.

This is the deadliest single incident involving Israeli soldiers in Gaza since the start of the ceasefire eight days ago.

The Israeli military said soldiers had fired at a "suspicious vehicle" that had crossed the so-called yellow line demarcating the area still occupied by Israeli forces in Gaza.

Israeli soldiers continue to operate in more than half of the Gaza Strip, under the terms of the first phase of the ceasefire agreement.

Civil defence spokesman Mahmud Bassal told AFP news agency the victims were killed while "trying to check on their home" in the area.

The dead included women and children, according to the civil defence.

The Israel Defence Forces (IDF) said a "suspicious vehicle was identified crossing the yellow line and approaching IDF troops operating in the northern Gaza Strip" on Friday, prompting it to fire "warning shots" towards the vehicle.

It said the vehicle "continued to approach the troops in a way that caused an imminent threat to them" and "troops opened fire to remove the threat, in accordance with the agreement."

Hamas said the family had been targeted without justification.

The IDF has warned Palestinians from entering areas in Gaza still under its control.

With limited internet access, many Palestinians do not know the position of Israeli troops as the yellow demarcation line is not physically marked, and it is unclear if the area where the bus was travelling did cross it.

The BBC has asked the IDF for coordinates of the incident.

Israeli Defence Minister Israel Katz said on Friday the army would set up visual signs to indicate the location of the line.

In a separate development, Hamas on Friday released the body of Israeli hostage Eliyahu Margalit to the Red Cross, which returned it to Israel.

Mr Margalit was the tenth deceased hostage to be returned from Gaza. The remains of another 18 people are yet to be repatriated.

Israel handed the bodies of 15 more Palestinians over to officials in Gaza via the Red Cross, the Hamas-run health ministry said, bringing the total number of bodies it has received to 135.

There has been anger in Israel that Hamas has not returned all of the dead hostages' bodies, in line with last week's ceasefire deal - though the US has downplayed the suggestion it amounts to a breach.

The IDF has stressed that Hamas must "uphold the agreement and take the necessary steps to return all the hostages".

Hamas has blamed Israel for making the task difficult because Israeli strikes have reduced so many buildings to rubble and it does not allow heavy machinery and diggers into Gaza to be able to search for the hostages' bodies.

As part of the US-brokered ceasefire deal, Israel freed 250 Palestinian prisoners in Israeli jails and 1,718 detainees from Gaza.

Hamas also returned all 20 living hostages to Israel.

The Israeli military launched a campaign in Gaza in response to the 7 October 2023 attack, in which Hamas-led gunmen killed about 1,200 people in southern Israel and took 251 others hostage.

At least 67,900 people have been killed by Israeli attacks in Gaza since then, according to the territory's Hamas-run health ministry, whose figures are seen by the UN as reliable.'''
    
    analyzer = TextAnalyzer(text, 29)
    S,P,E,T,HP= analyzer.report()
    print(S,P,E,T,HP)
