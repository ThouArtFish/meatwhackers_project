from transformers import pipeline

# Load a model that can classify without training
classifier = pipeline("zero-shot-classification", 
                      model="facebook/bart-large-mnli")
# Define your categories
categories = ["direct evidence", "inferred evidence", "hearsay evidence", "not applicable"]

# Test it on any phrase
phrases = [
    '''Prince Andrew is giving up his titles, including the Duke of York, he has announced in a personal statement.

He has been under increasing pressure over his links with sex offender Jeffrey Epstein, with calls for Buckingham Palace to take action against him.

That now seems to have resulted in the prince deciding to voluntarily hand back his titles and to give up membership of the Order of the Garter, the oldest and most senior order of chivalry in Britain.

In his statement he said he continued to "vigorously deny the accusations against me".

"In discussion with the King, and my immediate and wider family, we have concluded the continued accusations about me distract from the work of His Majesty and the Royal Family," said a statement from Prince Andrew.

"I have decided, as I always have, to put my duty to my family and country first.

"I stand by my decision five years ago to stand back from public life.

"With His Majesty's agreement, we feel I must now go a step further. I will therefore no longer use my title or the honours which have been conferred upon me. As I have said previously, I vigorously deny the accusations against me."

His decision to stop using his titles was made in consultation with William, Prince of Wales, as well as the King.

He will remain a prince - but will cease to be the Duke of York, a title received from his mother, the late Queen Elizabeth.

Prince Andrew had already ceased to be a "working royal" and had lost the use of his HRH title and no longer appeared at official royal events. His role now will be even more diminished.

He is expected to stay in his Windsor home, Royal Lodge, on which he has his own private lease which runs until 2078.

His ex-wife will be known as Sarah Ferguson and no longer Duchess of York, but their daughters will continue to have the title of princess.

The prince has faced a series of scandals over recent years, including a court case he settled with Virginia Giuffre, questions about his finances and his involvement with an alleged Chinese spy.

There had been growing frustration in Buckingham Palace at the scandals that continued to surround the prince.'''
]
for phrase in phrases:
    result = classifier(phrase, categories)
    print(f"'{phrase}' → {result['labels'][0]} ({result['scores'][0]:.2f})")



