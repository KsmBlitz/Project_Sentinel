from fastapi import FastAPI

from src.api.routers.urls import router as urls_router

app = FastAPI(
    title="Sentinel",
    description="Monitor de disponibilidad de URLs",
    version="0.1.0",
)

app.include_router(urls_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
