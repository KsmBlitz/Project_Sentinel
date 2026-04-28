from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routers.urls import router as urls_router
from workers.checker import run_checks
from workers.etl import run_etl


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_checks, "interval", minutes=5, id="checker")
    scheduler.add_job(run_etl, "interval", hours=1, id="etl")
    scheduler.start()

    run_checks()
    run_etl()

    yield

    scheduler.shutdown()


app = FastAPI(
    title="Sentinel",
    description="Monitor de disponibilidad de URLs",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(urls_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
