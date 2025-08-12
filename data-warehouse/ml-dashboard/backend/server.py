from fastapi import FastAPI
from backend.ml_routes import router as ml_router

app = FastAPI()
app.include_router(ml_router)  # ← this alone is perfect
