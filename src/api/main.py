from fastapi import FastAPI

app = FastAPI(
    title="Sentinel",
    description="Monitor de disponibilidad de URLs",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    return {"status": "ok"}
