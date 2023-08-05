from fastapi import FastAPI

from analysis.router import router as router_analysis
from auth.router import router as router_auth

app = FastAPI(
    title="Poker app",
)

app.include_router(router_analysis)
app.include_router(router_auth)
