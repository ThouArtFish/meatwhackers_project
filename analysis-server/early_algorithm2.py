import spacy
from transformers import pipeline
from textblob import TextBlob
import torch
import math

class TextAnalyzer:
    def __init__(self, text, journalist_info):
        self.text = text
        self.journalist_info = journalist_info
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
                "verifiable or authoritative evidence (includes official reports, named expert quotes, data, or primary sources)",
                "second-hand but attributed information (includes statements by named sources, organizations, or officials — not anonymous)",
                "anonymous or speculative information (includes rumors, vague claims, or unverified reports)",
    "           neutral or background description (factual context without claims)"
        ]

        self.highlight_sentences = {"evidence": []}
        self.months = {'january', 'february', 'march', 'april', 'may', 'june', 'july',
                       'august', 'september', 'october', 'november', 'december',
                       'jan', 'feb', 'mar', 'apr', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'}

    def empty(function):
        pass
    def polarity(self, sentence):
        return TextBlob(sentence).polarity


    def subjectivity(self, sentence):
        return TextBlob(sentence).subjectivity

    # --- Evidence Scoring ---
    def _highlight_sentence(self, sentence, score):
        if score == 1 or score == 0.5:
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
            score = 0.5
        elif label == self.categories[2]:
            score = -1
        else:
            score = 0


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
        for k, v in categories.items():
            highlighted_list.extend([{"text": item, "type": k} for item in set(v)])

        return highlighted_list

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
        highlighted_sentences = [
                {"text": s, "type": typ} 
                for typ, sentences in self.highlight_sentences.items() 
                for s in sentences
            ]

        highlighted_words = self.highlight_words()
        #add score per evidence
        total += 0.01 * len(highlighted_words)

        boost = min(0.15, 0.05 * math.log10(self.journalist_info + 1))

        total += boost

        total = max(min(total, 1), -1)

        return subjectivity, polarity, evidence, total, highlighted_sentences, highlighted_words
#ss
#sadasdas
if __name__ == '__main__':
    text = ''''Every week it seems US financial markets are hit by another bout of fear.

The latest worries spread this week from the banking sector in the US, after two regional lenders warned they would be hit by losses from alleged fraud.

But before that, markets swooned over signs of rekindled US-China tensions, as the two superpowers face off over tariffs, advanced technology and access to rare earths.

The bankruptcies of car parts supplier First Brands and subprime car lender Tricolor acted as a trigger for nervous chatter in September.

Over the last month, US shares, which had been climbing since their tariff-induced rout in April, have flattened.

But in many ways the market swings so far - down roughly 3% at the steepest - are not unusual.

Zooming out, the major indexes have still posted gains since the start of the year, with the S&P 500 up roughly 13%. That's smaller than 2024 but still solid.

"The market has done surprisingly well so far this year ... driven by an improvement in corporate profits and the enthusiasm surrounding AI," says Sam Stovall, chief investment strategist at CFRA Research.

The resilience of the stock market is, ironically, exactly what is driving some of the jitters.

Put simply, when set against other standard metrics like profits, share prices in the US are very high.

Meanwhile, concerns about a possible bubble emerging in the artificial intelligence (AI) industry have generated a steady undercurrent of talk since the start of the year - discussions that have ramped up as analysts struggle to see how the vast sums of money the biggest players are throwing at one another all fit together.

The Bank of England warned recently of "stretched valuations" and rising risk of a "sharp market correction".

Those concerns were echoed in remarks from JP Morgan Chase boss Jamie Dimon and to some extent US central bank chair Jerome Powell.

The International Monetary Fund was the latest to chime in this week.

"Markets appear complacent as the ground shifts," it said in its financial stability report, which noted risks from trade tensions, geopolitical uncertainty and rising sovereign indebtedness.

James Reilley, senior markets economist at Capital Economics, said the market falls triggered by the regional banks were a sign of investors alert to risk and moving quickly to reduce exposure amid uncertainty about whether the losses were indicative of wider issues.

But he said the brief nature of the drops showed how quickly such worries could clear.

Many investors remain optimistic, with analysts at firms such as Goldman Sachs and Wells Fargo in recent weeks boosting their forecasts for where the S&P 500 might climb by the end of the year.

David Lefkowitz, head of US equities at UBS Global Wealth Management, said he thought a sharp sell-off was unlikely at a time when growth in the US remains solid and the US central bank is lowering borrowing costs.

He is expecting the S&P 500 to end the year hovering around 6,900 points, about 4% higher than where it sits on Friday.

While he acknowledged the troubles popping up at banks, he noted that the lenders involved have alleged fraud.

He said the overall picture, when looking at default levels, appears healthy, and he saw little risk that demand for AI would suddenly decline, puncturing valuations.

"I'm not saying we're in a bubble. I'm not saying we're not in a bubble. The question is what's going to drive the downside," he said. "Things don't usually spontaneously decline."

A typical bull market - when shares are rising - lasts about four and a half years, said Mr Stovall.

With inflation still sticky, and investors wary of events in Washington, like the government shutdown and Trump administration's efforts to influence the US central bank, this year's market rally has been "unloved", said Mr Stovall.

On the other hand, he noted: "It's just a matter of time. Corrections and bear markets have not been repealed. They might simply be delayed'''
    
    analyzer = TextAnalyzer(text, 29)
    S,P,E,T,HS,HW= analyzer.report()
    print(S,P,E,T,HS,HW)
