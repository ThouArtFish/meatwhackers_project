from fastapi import FastAPI, Query
import uvicorn
import webscraper
import early_algorithm

app = FastAPI()



@app.get("/")
def root():
    return {"message": "You have reached the API."}


@app.get("/factcheck_headlines")
def fact_check_headlines():
    scraper = webscraper.BBCBusinessScraper()
    headlines = scraper.fetch_headlines()
    
    headline_scores = []
    for headline in headlines[:10]:
        text = scraper.fetch_article_text(headline)
        subjectivity, polarity, evidence, total = early_algorithm.MainScore(text)

        headline_scores.append({
            "title": headline.title,
            "link": headline.link,
            "subjectivity": subjectivity,
            "polarity": polarity,
            "evidence": evidence,
            "total": total
        })
    print(headline_scores)
    # Return automatically as JSON
    return {headline_scores}



    
    

@app.get("/factcheck_article")
def fact_check_article(url: str = Query(..., description="BBC article URL")):
    # Initialize the scraper with the given article URL
    scraper = webscraper.BBCArticleScraper(url)

    # Get article details
    title = scraper.get_heading()
    text = scraper.get_text_content()
    journalist_info = scraper.get_journalist()
    related_articles = scraper.get_related_articles()
    if not text:
        return {"error": "Could not fetch article text."}

    # Run your scoring algorithm
    subjectivity, polarity, evidence, total = early_algorithm.MainScore(text)

    related_articles_json = [
            {"title": t, "link": l} for t, l in related_articles
    ] if related_articles else []

    # Return everything as JSON
    return {
        "title": title,
        "url": url,
        "journalist": journalist_info[0] if journalist_info else None,
        "articles_by_journalist": journalist_info[1] if journalist_info else None,
        "subjectivity": subjectivity,
        "polarity": polarity,
        "evidence": evidence,
        "total": total,
        "related_articles": related_articles_json
    }

if __name__ == "__main__":
    uvicorn.run("server:app", host='127.0.0.1', port=8000, reload=True,timeout_keep_alive=300)
