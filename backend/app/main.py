from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import ALLOWED_ORIGIN
from app.routes import compare, health, metrics, predict, samples

app = FastAPI(title="Explainable Pneumonia Detection API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOWED_ORIGIN],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(predict.router)
app.include_router(compare.router)
app.include_router(samples.router)
app.include_router(metrics.router)


@app.get("/")
def root():
    return {"message": "Pneumonia detection API. See /docs for the interactive docs."}
