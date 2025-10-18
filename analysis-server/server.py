import fastapi
import uvicorn
import webscraper
import EarlyAlogirthm

app = fastapi.FastAPI()

@app.post("/factcheck_headlines")
def fact_check_headlines():
    
    
    pass

@app.post("/factcheck_article")
def fact_check_article():
    return {

    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
