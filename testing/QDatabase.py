import sqlite3


#Connecting the GraphSoftareDataBase to the software
database = sqlite3.connect("WebpageDB.db")

#Creating a cursors that allows to execute SQL commands
cur = database.cursor()



exists1 = cur.execute("SELECT name FROM sqlite_master WHERE name = 'Webpages'")

#If doesn't exists, create table

if (exists1.fetchone() is None) == True:
    cur.execute("CREATE TABLE Webpages(Title, url, subjevivity, evidence, total, journalist, article_count, h_words, h_sentences, responses)")




exists2 = cur.execute("SELECT name FROM sqlite_master WHERE name = ''Matchcomments")

