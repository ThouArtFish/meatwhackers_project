import fastapi
import uvicorn
import webscraper
import early_algorithm

app = fastapi.FastAPI()



@app.get("/")
def root():
    return {"message": "You have reached the API."}


@app.get("/factcheck_headlines")
def fact_check_headlines():
    scraper = webscraper.BBCBusinessScraper()
    headlines = scraper.fetch_headlines()
    
    headline_scores = []
    for headline in headlines:
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
    return {"results": headline_scores}



    
    

@app.post("/factcheck_article")
def fact_check_article():

    subjectivity,polarity,evidence,total = early_algorithm.MainScore(text)
    return {
        
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
