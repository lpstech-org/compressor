from fastapi import FastAPI
from .routes import health, optimize

app = FastAPI(title="AI Compress Backend")

app.include_router(health.router, prefix="/api")
app.include_router(optimize.router, prefix="/api")
