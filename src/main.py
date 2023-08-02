from fastapi import FastAPI

from src.analysis.router import router as router_analysis

app = FastAPI(
    title="Poker app",
)

app.include_router(router_analysis)
