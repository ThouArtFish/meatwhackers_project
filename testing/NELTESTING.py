import spacy

nlp = spacy.load("en_core_web_lg")

months = {'january', 'february', 'march', 'april', 'may', 'june', 'july', 
          'august', 'september', 'october', 'november', 'december',
          'jan', 'feb', 'mar', 'apr', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'}

doc = nlp("""
The brother of Virginia Giuffre has called on King Charles to strip Prince Andrew of the title "prince" after he announced he is giving up his other titles, including the Duke of York.

Ms Giuffre alleged she was forced to have sex with the prince on three occasions, including when she was aged 17 at the home of his friend Ghislaine Maxwell in London in 2001.

The prince made a financial payment to Ms Giuffre in an out-of-court settlement in 2022, after she had brought a civil case against him. He denies all the accusations against him.

Sky Roberts told BBC Newsnight his sister, who took her own life earlier this year, would be "very proud" of the latest development regarding Prince Andrew.

The prince has been under increasing pressure over his links with sex offender Jeffrey Epstein, with calls for Buckingham Palace to take action against him.

On Friday, the prince announced that he was deciding to voluntarily hand back his titles and to give up membership of the Order of the Garter, the oldest and most senior order of chivalry in Britain.

He will also cease be the Duke of York, a title received from his mother, the late Queen Elizabeth II.

But Mr Roberts said he would like to see the King go a step further, saying: "We would call on the King to potentially go ahead and take out the prince in the Andrew."

"I think anybody that was implicated in this should have some sort of resolve. They should have some sort of responsibility and accountability for these survivors," he said, adding that he would "welcome any contact from the King, from members of parliament".

When Prince Andrew was born in 1960, he was automatically a prince as the son of a monarch. This could only be changed if a Letters Patent was issued by the King.
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
        if any(char.isdigit() for char in ent.text) or ent.text.lower() in months:
            print(f"Specific date: {ent.text}")
        

    # Times  
    if ent.label_ == "TIME":
        print(f"Specific time: {ent.text}")

    # Numbers
    if ent.label_ == "CARDINAL":
        print(f"Specific number: {ent.text}")

    # Laws/Legal documents (limited)
    if ent.label_ == "LAW":
        print(f"Specific law/document: {ent.text}")

    # Events
    if ent.label_ == "EVENT":
        print(f"Specific event: {ent.text}")


print("ALL ENTITIES FOUND:")
print("=" * 40)
for ent in doc.ents:
    print(f"'{ent.text}' -> {ent.label_}")