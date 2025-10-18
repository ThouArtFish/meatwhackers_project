import spacy

nlp = spacy.load("en_core_web_sm")


doc = nlp("""
Elon Musk announced on March 15th that Tesla 
would invest $2 billion in a new factory in Austin . 
The company aims to increase production by 25%  this year. 
According to the recent quarterly report, they delivered 500,000. 
vehicles last quarter. The announcement came at 3:00 PM during 
a press conference at their Nevada facility. This follows the Clean Air Act 
requirements and coincides with the Annual Tech Summit next month.
""")




for ent in doc.ents:
        # People
    if ent.label_ == "PERSON":
        print(f"Specific person: {ent.text}")

    # Companies & Organizations  
    if ent.label_ == "ORG":
        print(f"Specific organization: {ent.text}")

    # Locations (Countries, cities, states)
    if ent.label_ == "GPE":
        print(f"Specific location: {ent.text}")

    # Dates
    if ent.label_ == "DATE":
        print(f"Specific date: {ent.text}")

    # Times  
    if ent.label_ == "TIME":
        print(f"Specific time: {ent.text}")

    # Monetary amounts
    if ent.label_ == "MONEY":
        print(f"Specific amount: {ent.text}")

    # Percentages
    if ent.label_ == "PERCENT":
        print(f"Specific percentage: {ent.text}")

    # Numbers
    if ent.label_ == "CARDINAL":
        print(f"Specific number: {ent.text}")

    # Laws/Legal documents (limited)
    if ent.label_ == "LAW":
        print(f"Specific law/document: {ent.text}")

    # Events
    if ent.label_ == "EVENT":
        print(f"Specific event: {ent.text}")
