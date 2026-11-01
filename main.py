from fastapi import FastAPI

app = FastAPI(title="Enterprise Identity Security Lab")

@app.get("/health")
def health():
    return {"status": "ok"}
