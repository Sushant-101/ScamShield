from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.analysis import router as analysis_router


app = FastAPI(title="ScamShield API")


# -----------------------------
# CORS Configuration
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------
# Routes
# -----------------------------
app.include_router(analysis_router)


# -----------------------------
# Home
# -----------------------------
@app.get("/")
def home():
    return {
        "message": "ScamShield Backend is running!"
    }