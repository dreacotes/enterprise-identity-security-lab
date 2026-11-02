from fastapi import FastAPI, HTTPException

app = FastAPI(title="Enterprise Identity Security Lab")

@app.get("/health")
def health():
    return {"status": "ok"}

resources = {
    1: {"id": 1, "name": "Identity security lab"},
}


@app.get("/resources/{resource_id}")
def get_resource(resource_id: int):
    if resource_id not in resources:
        raise HTTPException(status_code=404, detail="Resource not found")

    return resources[resource_id]