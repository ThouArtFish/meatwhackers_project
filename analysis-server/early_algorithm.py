import spacy
from transformers import pipeline
from textblob import TextBlob
import torch
import math

from webscraper import Paragraph, BBCArticleScraper


#yes
def MainScore(scraper: BBCArticleScraper):
    text = scraper.get_text_content()

    #Intialise classifer for evidence categories
    classifier = pipeline("zero-shot-classification",
                     model="typeform/distilbert-base-uncased-mnli",
                     device=0 if torch.cuda.is_available() else -1,
                     batch_size=16,  # Process 8 sentences at once
                     truncation=True)


    # Define your categories
    categories = ["direct evidence (e.g., eyewitness accounts, video, confessions)",  
                "hearsay evidence (Someonte told me, I heard, the rumour is etc)", 
                "no evidence or simple fact"]

    nlp = spacy.load("en_core_web_lg")

    months = {'january', 'february', 'march', 'april', 'may', 'june', 'july', 
            'august', 'september', 'october', 'november', 'december',
            'jan', 'feb', 'mar', 'apr', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'}



    

    doc = nlp(text)
    phrases = []

    sentences = list(doc.sents)


    def tokenize(paragraphs):
        for i, sent in enumerate(sentences):
            phrases.append(sent.text)
        
        return phrases


    def polarity(sentence):

        text = TextBlob(sentence)

        pol_rating = text.polarity

        return pol_rating

    def subjectivity(sentence):

        text = TextBlob(sentence)

        sub_rating = text.subjectivity

        return sub_rating




    tokenize(text)

    highlight_sentences = {"evidence": []}

    def HighlightSentence(sentence, result):
        if result == 1:
            highlight_sentences["evidence"].append(sentence)
        
        elif result == -1:
            highlight_sentences.setdefault("hearsay", []).append(sentence)
      

    

    def EvidenceScore(phrase):
        result = classifier(phrase, categories)

        print(result['labels'][0])
        if result['labels'][0] == "direct evidence (e.g., eyewitness accounts, video, confessions)":
            score = 1
            HighlightSentence(phrase, score)
        elif result['labels'][0] == "hearsay evidence (Someonte told me, I heard, the rumour is etc)":
            score = -1
            HighlightSentence(phrase, score)
        else:
            score = 0
        
        multiplier = result['scores'][0]

        return multiplier*score
        

    sub_scores = 0
    sub_count = 0
    evi_scores = 0
    evi_count = 0

    for phrase in phrases:
        
        
        sub_scores += subjectivity(phrase)
        sub_count += 1
        
        evi_scores += EvidenceScore(phrase)
        evi_count += 1

    rated_sentences = []

    
    def LineScore(sentence):
        
        for sentence in phrases:
            rated_sentences.append([sentence, subjectivity(sentence), EvidenceScore(sentence)])
    
        return rated_sentences
    
    
   
    

    
    def CalculateScore(subjectivity, scount, polarity, ecount, evidence):
        # Average each
        subjectivity = subjectivity / scount
        evidence = evidence / ecount
        polarity = max(min(polarity, 1), -1)  # clamp just in case

        # Scale subjectivity from [0,1] → [-1,1]
        subjectivity_scaled = (subjectivity * 2) - 1

        # Making sure evidence between [-1,1 ]
        evidence_scaled = max(min(evidence, 1), -1)

        #  Compute weighted or simple average
        total = (subjectivity_scaled + polarity + evidence_scaled) / 3

        # Ensure total stays between -1 and 1
        total = max(min(total, 1), -1)

        # Round values for readability
        return (
            round(subjectivity_scaled, 2),
            round(polarity, 2),
            round(evidence_scaled, 2),
            round(total, 2)
        )
        #This returns Subjectivity score, Polarity Score, Evidence score, and Total Score

        


    def HighlightWord():
        categories = {
            "person": [],
            "org": [],
            "gpe": [],
            "date": [],
            "time": [],
            "money": [],
            "percent": [],
            "cardinal": [],
            "law": [],
            "event": [],
        }

        for ent in doc.ents:
            label = ent.label_

            if label == "PERSON":
                categories["person"].append(ent.text)

            elif label == "ORG":
                categories["org"].append(ent.text)

            elif label == "GPE":
                categories["gpe"].append(ent.text)

            elif label == "DATE":
                if (any(char.isdigit() for char in ent.text) or ent.text.lower() in months) and len(ent.text) > 2:
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

        # Convert lists to sets and remove empty ones
        result = {k: set(v) for k, v in categories.items() if v}

        return result
        
    def Highlighted():

        return highlight_sentences, HighlightWord()
    
    
    # subjectivity, polarity, evidence, total, highlighted_sentences, highlighted_words

    return (*CalculateScore(sub_scores, sub_count, polarity(text),evi_count, evi_scores), *Highlighted())

        

if __name__ == '__main__':
    print(MainScore('''The brother of Virginia Giuffre has called on King Charles to strip Prince Andrew of the title "prince" after he announced he is giving up his other titles, including the Duke of York.

    Ms Giuffre alleged she was forced to have sex with the prince on three occasions, including when she was aged 17 at the home of his friend Ghislaine Maxwell in London in 2001.

    The prince made a financial payment to Ms Giuffre in an out-of-court settlement in 2022, after she had brought a civil case against him. He denies all the accusations against him.

    Sky Roberts told BBC Newsnight his sister, who took her own life earlier this year, would be "very proud" of the latest development regarding Prince Andrew.

    The prince has been under increasing pressure over his links with sex offender Jeffrey Epstein, with calls for Buckingham Palace to take action against him.

    On Friday, the prince announced that he was deciding to voluntarily hand back his titles and to give up membership of the Order of the Garter, the oldest and most senior order of chivalry in Britain.

    He will also cease be the Duke of York, a title received from his mother, the late Queen Elizabeth II.

    But Mr Roberts said he would like to see the King go a step further, saying: "We would call on the King to potentially go ahead and take out the prince in the Andrew."

    "I think anybody that was implicated in this should have some sort of resolve. They should have some sort of responsibility and accountability for these survivors," he said, adding that he would "welcome any contact from the King, from members of parliament".

    When Prince Andrew was born in 1960, he was automatically a prince as the son of a monarch. This could only be changed if a Letters Patent was issued by the King. '''))