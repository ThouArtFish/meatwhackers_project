import fastapi
import uvicorn

app = fastapi.FastAPI()

@app.post("/factcheck_headlines")
def fact_check_headlines():
    
    
    pass

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
