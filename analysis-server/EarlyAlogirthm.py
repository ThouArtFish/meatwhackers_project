import spacy
from transformers import pipeline
from textblob import TextBlob

#yes
def MainScore(ntext):

    # Load a model that can classify witho
    # ut training
    classifier = pipeline("zero-shot-classification", 
                        model="facebook/bart-large-mnli")


    # Define your categories
    categories = ["direct evidence (e.g., eyewitness accounts, video, confessions)",  
                "hearsay evidence (Someonte told me, I heard, the rumour is etc)", 
                "no evidence or simple fact"]



    nlp = spacy.load("en_core_web_sm")

    text = ntext

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


    def EvidenceScore(phrase):
        result = classifier(phrase, categories)


        if result['labels'][0] == "direct evidence (e.g., eyewitness accounts, video, confessions)":
            score = 1
        elif result['labels'][0] == "hearsay evidence (Someonte told me, I heard, the rumour is etc":
            score = -1
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

        




    def CalculateScore(subjectivity, scount, polarity, ecount, evidence):

        subjectivity = subjectivity / scount
        evidence = evi_scores / ecount
        total = (subjectivity + polarity + evidence) / 3

        return round(subjectivity,2) , round(polarity,2), round(evidence,2), round(total,2)


    #This returns Subjectivity score, Polarity Score, Evidence score, and Total Score

    return CalculateScore(sub_scores, sub_count, polarity(text),evi_count, evi_scores)

        


