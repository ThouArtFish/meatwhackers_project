from fastapi import FastAPI, Query, HTTPException
import uvicorn
import webscraper
import early_algorithm2
from gemini_flask import GeminiResponse
import sqlite3
import json



def init_db():
    conn = sqlite3.connect("factcheck.db")
    c = conn.cursor()

    # Main table for article analysis
    c.execute('''
        CREATE TABLE IF NOT EXISTS factcheck_articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            url TEXT,
            journalist TEXT,
            articles_by_journalist TEXT,
            subjectivity REAL,
            polarity REAL,
            evidence REAL,
            total REAL,
            highlighted_phrases,
            related_articles TEXT,
            response TEXT
        )
    ''')

    # Table for storing comments
    c.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            comment_text TEXT NOT NULL
        )
    ''')

    # Linking table between factcheck_articles and comments
    c.execute('''
        CREATE TABLE IF NOT EXISTS article_comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id INTEGER NOT NULL,
            comment_id INTEGER NOT NULL,
            FOREIGN KEY(article_id) REFERENCES factcheck_articles(id),
            FOREIGN KEY(comment_id) REFERENCES comments(id)
        )
    ''')

    # Table for upvotes and downvotes
    c.execute('''
        CREATE TABLE IF NOT EXISTS article_votes (
            article_id INTEGER PRIMARY KEY,
            upvotes INTEGER DEFAULT 0,
            downvotes INTEGER DEFAULT 0,
            FOREIGN KEY(article_id) REFERENCES factcheck_articles(id)
        )
    ''')



    c.execute('''
    CREATE TABLE IF NOT EXISTS headlines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        link TEXT,
        subjectivity REAL,
        polarity REAL,
        evidence REAL,
        total REAL
    )
    ''')

    conn.commit()
    conn.close()

init_db()


def save_factcheck_result(data: dict):
    conn = sqlite3.connect("factcheck.db")
    c = conn.cursor()

    c.execute('''
        INSERT INTO factcheck_articles (
            title, url, journalist, articles_by_journalist, subjectivity,
            polarity, evidence, total, highlighted_phrases, related_articles, response
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data["title"],
        data["url"],
        data.get("journalist"),
        json.dumps(data.get("articles_by_journalist")),
        data.get("subjectivity"),
        data.get("polarity"),
        data.get("evidence"),
        data.get("total"),
        json.dumps(data.get("highlighted_phrases")),
        
        json.dumps(data.get("related_articles")),
        data.get("response")
    ))

    # Get article ID of newly inserted record
    article_id = c.lastrowid

    # Initialize vote record for this article
    c.execute('''
        INSERT INTO article_votes (article_id, upvotes, downvotes)
        VALUES (?, 0, 0)
    ''', (article_id,))

    conn.commit()
    conn.close()

app = FastAPI()




@app.get("/")
def root():
    return {"message": "welcome to the API"}

@app.get("/factcheck_headlines")
def fact_check_headlines():
    scraper = webscraper.BBCBusinessScraper()
    headlines = scraper.fetch_headlines()
    
    results = []
    conn = sqlite3.connect("factcheck.db")
    c = conn.cursor()

    # 🔹 Fetch all existing headlines from DB in one go
    c.execute("SELECT title, link, subjectivity, polarity, evidence, total FROM headlines")
    existing = { (row[0], row[1]): row for row in c.fetchall() }

    for headline in headlines[:10]:
        key = (headline.title, headline.link)

        if key in existing:
            # Use DB values if already stored
            row = existing[key]
            result = {
                "title": row[0],
                "link": row[1],
                "subjectivity": row[2],
                "polarity": row[3],
                "evidence": row[4],
                "total": row[5]
            }
        else:
            # Otherwise fetch, analyze, and save
            text = scraper.fetch_article_text(headline)
            journalist_info = scraper.get_journalist(headline)
            subjectivity, polarity, evidence, total, _ = early_algorithm2.TextAnalyzer(text,(journalist_info[1]if journalist_info else 20)).report()

            # Save to DB
            c.execute('''
                INSERT INTO headlines (title, link, subjectivity, polarity, evidence, total)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (headline.title, headline.link, subjectivity, polarity, evidence, total))
            conn.commit()

            result = {
                "title": headline.title,
                "link": headline.link,
                "subjectivity": subjectivity,
                "polarity": polarity,
                "evidence": evidence,
                "total": total
            }

        results.append(result)

    conn.close()
    return results

@app.get("/factcheck_results")
def get_factcheck_results():
    conn = sqlite3.connect("factcheck.db")
    c = conn.cursor()
    c.execute("SELECT * FROM factcheck_articles")
    rows = c.fetchall()
    conn.close()

    columns = [
        "id", "title", "url", "journalist", "articles_by_journalist",
        "subjectivity", "polarity", "evidence", "total",
        "highlighted_phrases", "related_articles", "response"
    ]
    return [dict(zip(columns, row)) for row in rows]
 


@app.get("/factcheck_article")
def fact_check_article(url: str = Query(..., description="BBC article URL")):
    conn = sqlite3.connect("factcheck.db")
    c = conn.cursor()

    # 🔹 Step 1: Check if the article already exists in DB by URL or title
    c.execute("SELECT * FROM factcheck_articles WHERE url = ?", (url,))
    row = c.fetchone()

    if row:
        # 🔹 Step 2: Convert DB row into JSON-like dict
        columns = [
            "id", "title", "url", "journalist", "articles_by_journalist",
            "subjectivity", "polarity", "evidence", "total",
            "highlighted_phrases", "related_articles", "response"
        ]
        conn.close()

        # Convert JSON fields back from strings
        jsonResponse = dict(zip(columns, row))
        jsonResponse["articles_by_journalist"] = json.loads(jsonResponse["articles_by_journalist"]) if jsonResponse["articles_by_journalist"] else None
        jsonResponse["highlighted_phrases"] = json.loads(jsonResponse["highlighted_phrases"]) if jsonResponse["highlighted_phrases"] else []

        jsonResponse["related_articles"] = json.loads(jsonResponse["related_articles"]) if jsonResponse["related_articles"] else []

        return jsonResponse

    # 🔹 Step 3: If not found — scrape, analyze, and save
    scraper = webscraper.BBCArticleScraper(url)
    title = scraper.get_heading()
    journalist_info = scraper.get_journalist()
    related_articles = scraper.get_related_articles()
    text = scraper.get_text_content()

    if not text:
        conn.close()
        raise HTTPException(status_code=400, detail="Could not fetch article content.")

    subjectivity, polarity, evidence, total, highlighted_phrases = early_algorithm2.TextAnalyzer(
        text, journalist_info[1] if journalist_info else None
    ).report()

    related_articles_json = [
        {"title": t, "link": l} for t, l in related_articles
    ] if related_articles else []

    GPT = GeminiResponse()
    response = GPT.generateResponse(f"""You are now an elite economist who has centered their career around helping ordinary people invest and make smart market decisions. I am a young person who is interested in investing their money to be more financially secure. I have read the following article and I need you to do the following:
                                    1. Read the article and give bullet points with one or two sentences about what ojectively happens in the article and what changes in terms of markets, companies stock and more.
                                    2. Give 4 things on markets or investments that you would recommend to readers after reading this article for economic success. Your respons should be no longer than 20 lines. This is the file below:
                                    {text} You should be serious and concise, no unnecessary speech We also have an index from -1 to 1 to determine if this is a reliable news story media wise. a story is considered good if its total rating is more than 0.1. If the rating is too low for you to honestly give advice money-wise, you can say to not invest as your advice. You should give reasons why. The rating for this story is {total}. You must NOT use markdown language.""")
    response = response.candidates[0].content.parts[0].text

    jsonResponse = {
        "title": title,
        "url": url,
        "journalist": journalist_info[0] if journalist_info else None,
        "articles_by_journalist": journalist_info[1] if journalist_info else None,
        "subjectivity": subjectivity,
        "polarity": polarity,
        "evidence": evidence,
        "total": total,
        "highlighted_phrases": highlighted_phrases,
        "related_articles": related_articles_json,
        "response": response
    }

    save_factcheck_result(jsonResponse)
    conn.close()
    return jsonResponse

@app.post("/articles/{article_id}/comments")
def add_comment(article_id: int, comment: str = Query(..., description="Comment text")):
    conn = sqlite3.connect("factcheck.db")
    c = conn.cursor()

    # Check if article exists
    c.execute("SELECT id FROM factcheck_articles WHERE id=?", (article_id,))
    if not c.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Article not found")

    # Insert comment into comments table
    c.execute("INSERT INTO comments (comment_text) VALUES (?)", (comment,))
    comment_id = c.lastrowid

    # Link comment to article
    c.execute("INSERT INTO article_comments (article_id, comment_id) VALUES (?, ?)", (article_id, comment_id))

    conn.commit()
    conn.close()
    return {"message": "Comment added successfully", "comment_id": comment_id}


@app.get("/articles/{article_id}/comments")
def get_comments(article_id: int):
    conn = sqlite3.connect("factcheck.db")
    c = conn.cursor()

    c.execute('''
        SELECT comments.id, comments.comment_text
        FROM comments
        JOIN article_comments ON comments.id = article_comments.comment_id
        WHERE article_comments.article_id = ?
    ''', (article_id,))

    comments = [{"comment_id": row[0], "comment_text": row[1]} for row in c.fetchall()]
    conn.close()

    return {"article_id": article_id, "comments": comments}


@app.get("/comments")
def get_all_comments():
    conn = sqlite3.connect("factcheck.db")
    c = conn.cursor()
    c.execute("SELECT * FROM comments")
    comments = [{"id": row[0], "comment_text": row[1]} for row in c.fetchall()]
    conn.close()
    return comments

@app.get("/articles/{article_id}/votes")
def get_votes(article_id: int):
    conn = sqlite3.connect("factcheck.db")
    c = conn.cursor()
    c.execute("SELECT upvotes, downvotes FROM article_votes WHERE article_id=?", (article_id,))
    result = c.fetchone()
    conn.close()
    if not result:
        raise HTTPException(status_code=404, detail="Article not found or no votes yet")
    return {"article_id": article_id, "upvotes": result[0], "downvotes": result[1]}


@app.post("/articles/{article_id}/upvote")
def upvote_article(article_id: int):
    conn = sqlite3.connect("factcheck.db")
    c = conn.cursor()
    c.execute("UPDATE article_votes SET upvotes = upvotes + 1 WHERE article_id=?", (article_id,))
    if c.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Article not found")
    conn.commit()
    conn.close()
    return {"message": f"Article {article_id} upvoted successfully"}


@app.post("/articles/{article_id}/downvote")
def downvote_article(article_id: int):
    conn = sqlite3.connect("factcheck.db")
    c = conn.cursor()
    c.execute("UPDATE article_votes SET downvotes = downvotes + 1 WHERE article_id=?", (article_id,))
    if c.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Article not found")
    conn.commit()
    conn.close()
    return {"message": f"Article {article_id} downvoted successfully"}





if __name__ == "__main__":
    uvicorn.run("server:app", host='127.0.0.1', port=8000, reload=True, timeout_keep_alive=300)
