import fastapi
import uvicorn

app = fastapi.FastAPI()

@app.post("/factcheck")
def fact_check():
    return "Fact-checking result"

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
