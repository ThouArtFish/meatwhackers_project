import fastapi

app = fastapi.FastAPI()

@app.post("/factcheck")
def fact_check():
    return "Fact-checking result"
