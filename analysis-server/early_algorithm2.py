import spacy
from transformers import pipeline
from textblob import TextBlob
import torch
import math

class TextAnalyzer:
    def __init__(self, text, articles_count):
        self.text = text
        self.articles_count = articles_count
        self.nlp = spacy.load("en_core_web_trf")
        self.doc = self.nlp(text)
        self.phrases = [sent.text for sent in self.doc.sents]

        self.classifier = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli",
            device=0 if torch.cuda.is_available() else -1,
            batch_size=16,
            truncation=True
        )

        

        self.categories = [
                
                    "direct_quote",       # X said, exact quote
                    "official_statement", # from authorities or organizations
                    "fact",               # objective, verifiable info
                    "analysis",           # commentary or opinion
                    "rumor",     
                    "eyewitness",
                    "suspection",
                    "neutral",
                    "analysis",
                    "commentary", 
                    "hearsay"
                
        ]
        
        self.category_weights = {
            "direct_quote": 0.95,
            "fact": 1.0,
            "official_statement": 0.8,
            "eyewitness": 0.5,
            "analysis": 0.0,
            "rumor": -0.5,
            "neutral": 0.0,
            "suspection":-0.5,
            "analysis":0.0,
            "commentary":0.0,
            "hearsay": -0.5

        }


        self.highlighted_sentences = {"direct quote": []}
        self.months = {'january', 'february', 'march', 'april', 'may', 'june', 'july',
                       'august', 'september', 'october', 'november', 'december',
                       'jan', 'feb', 'mar', 'apr', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'}

    
    def get_polarity(self, sentence):
        return TextBlob(sentence).polarity


    def get_subjectivity(self, sentence):
        return TextBlob(sentence).subjectivity

    # --- Evidence Scoring ---
    def get_highlighted_sentences(self, sentence, score):
        if score == 0.95:
            self.highlighted_sentences["direct quote"].append(sentence)
        elif score == 1.0:
            self.highlighted_sentences.setdefault("fact", []).append(sentence)
        elif score == 0.8:
            self.highlighted_sentences.setdefault("official statement", []).append(sentence)
        elif score == 0.7:
            self.highlighted_sentences.setdefault("attributed statement", []).append(sentence)
        elif score == -0.5:
            self.highlighted_sentences.setdefault("hearsay", []).append(sentence)
        elif score == 0.5:
            self.highlighted_sentences.setdefault("eyewitness", []).append(sentence)
        elif score == -0.3:
            self.highlighted_sentences.setdefault("uncertainty statement", []).append(sentence)

        


    def get_evidence_score(self, phrase):

        phrase = phrase.strip()
        if not phrase:
            return 0.0  # skip empty strings

        doc_phrase = self.nlp(phrase)
        result = self.classifier(phrase, self.categories)
        
        label = result['labels'][0]

        # Step 1: Check for quotes first
        if '"' in doc_phrase.text or "“" in doc_phrase.text or "”" in doc_phrase.text:
            label = "direct_quote"

        # Step 2: Only if no quotes, check for entities
        elif label in ["rumor", "hearsay"]:
            if any(ent.label_ in ["ORG", "GPE", "DATE", "MONEY", "PERCENT"] for ent in doc_phrase.ents):
                label = "analysis"
                
        
        # Check if label is analysis/neutral/commentary
        if label in ["analysis", "neutral", "commentary"]:
        # Check if the phrase has numeric/date/money entities
            if any(ent.label_ in ["CARDINAL", "DATE", "MONEY", "PERCENT"] for ent in doc_phrase.ents):
                label = "fact"
            
            # Check if there are quotation marks anywhere in the text
            if '"' in doc_phrase.text or "“" in doc_phrase.text or "”" in doc_phrase.text:
                label = "direct_quote"
                
        score = self.category_weights[label]

        print(score)

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
            if not phrase.strip():
                continue  # skip empty or whitespace-only phrases

            # 1. Check if the sentence was classified as one of the evidence types
            for typ, sentences in self.highlighted_sentences.items():
                if phrase in sentences:
                    final_highlighted.append({"text": phrase, "type": typ})
                    break  # stop after finding the type

            # 2. Extract entities from the same sentence
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
                    if any(char.isdigit() for char in ent.text) or (
                        ent.text.lower() in self.months and len(ent.text) > 2
                    ):
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
    text = '''The US State Department says it has "credible reports" that Hamas is planning an "imminent" attack on civilians in Gaza, which it says would violate the ceasefire agreement.

A statement released on Saturday said a planned attack against Palestinians would be a "direct and grave" violation of the ceasefire agreement and "undermine the significant progress achieved through mediation efforts".

The state department did not not provide further details on the attack and it is unclear what reports it was citing.

The first phase of the ceasefire deal between Hamas and Israel is currently in progress - all living hostages have been released and bodies of the deceased are still being returned to Israel.

Also part of the agreement, Israel freed 250 Palestinian prisoners in its jails and 1,718 detainees from Gaza.

Washington said it had already informed other guarantors of the Gaza peace agreement - which include Egypt, Qatar and Turkey - and demanded Hamas uphold its end of the ceasefire terms.

"Should Hamas proceed with this attack, measures will be taken to protect the people of Gaza and preserve the integrity of the ceasefire," the statement said, external.

Hamas has not yet commented on the statement.

President Donald Trump has previously warned Hamas against the killing of civilians.

"If Hamas continues to kill people in Gaza, which was not the Deal, we will have no choice but to go in and kill them," Trump said in a post on Truth Social earlier this week.

He later clarified that he would not be sending US troops into Gaza.

Last week, BBC Verify authenticated graphic videos that showed a public execution carried out by Hamas gunmen in Gaza.

The videos showed several men with guns line up eight people, whose arms were tied behind their backs, before killing them in a crowded square.

BBC Verify could not confirm the identity of the masked gunmen, though some appeared to be wearing the green headbands associated with Hamas.

On Saturday, Israel said it had received two more bodies from Gaza that Hamas said are hostages, though they have yet to be formally identified.

So far, the remains of 10 out of 28 deceased hostages had been returned to Israel.

Israeli Prime Minister Benjamin Netanyahu on Saturday said the Rafah border crossing between Gaza and Egypt would remain closed until Hamas returns the remaining bodies.

The Rafah crossing is a vital gateway for Palestinians who need medical assistance to leave Gaza, and for thousands of others to return.

Separately on Saturday, 11 members of one Palestinian family were killed by an Israeli tank shell, according to the Hamas-run civil defence ministry, in what was the deadliest single incident involving Israeli soldiers in Gaza since the start of the ceasefire.

The Israeli military said soldiers had fired at a "suspicious vehicle" that had crossed the so-called yellow line demarcating the area still occupied by Israeli forces in Gaza.

There are no physical markers of this line, and it is unclear if the bus did cross it. The BBC has asked the IDF for the coordinates of the incident.

The Israeli military launched a campaign in Gaza in response to the 7 October 2023 attack, in which Hamas-led gunmen killed about 1,200 people in southern Israel and took 251 others hostage.

At least 68,000 people have been killed by Israeli attacks in Gaza since then, according to the Hamas-run health ministry, whose figures are seen by the UN as reliable.

In September, a UN commission of inquiry said Israel had committed genocide against Palestinians in Gaza. Israel categorically rejected the report as "distorted and false".'''
    analyzer = TextAnalyzer(text, 29)
    S,P,E,T,HP= analyzer.report()
    print(S,P,E,T,HP)
