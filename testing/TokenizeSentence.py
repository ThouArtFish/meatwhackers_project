import spacy
from transformers import pipeline
from textblob import TextBlob


# Load a model that can classify witho
# ut training
classifier = pipeline("zero-shot-classification", 
                      model="facebook/bart-large-mnli")


# Define your categories
categories = ["direct evidence (e.g., eyewitness accounts, video, confessions)",  
              "hearsay evidence (Someonte told me, I heard, the rumour is etc)", 
              "no evidence or simple fact"]



nlp = spacy.load("en_core_web_sm")

text = '''The security camera clearly shows the defendant entering the building at 8:15 PM.
My neighbor told me that John confessed to the crime last night.
The board meeting is scheduled for 2 PM tomorrow.

The DNA test results prove with 99.9% accuracy he was at the scene.
According to office gossip, she was planning to resign for weeks.
The company headquarters is located in central London.

I personally witnessed the CEO signing the contract.
Rumors suggest the evidence was tampered with.
The conference will be held in the main auditorium.

The signed confession admits to all charges in detail.
Someone mentioned that the police found new clues.
The museum opens at 9 AM daily.

The email from the minister explicitly authorizes the payment.
I heard from a colleague that the witness changed their story.
The flight from London takes approximately 6 hours.

The bank records show the transfer came from his account.
People are saying the results were fabricated.
The building has twenty floors and two basements.

The audio recording captures his admission of guilt.
A source claims the documents were altered.
The policy change takes effect next quarter.

The medical report confirms the defensive wounds.
Word around the office is that the merger is happening.
She graduated from Oxford University in 2015.

The fingerprint analysis matched him to the weapon.
There's talk that the data was compromised.
The river flows through three counties before reaching the sea.

The contract bears his signature and date.
I was told by a third party about the arrangement.
The population of the city is approximately 500,000.

The video evidence shows the entire incident unfolding.
According to rumors, the CEO is stepping down.
The new legislation comes into force in April. '''

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

print(CalculateScore(sub_scores, sub_count, polarity(text),evi_count, evi_scores))

    


