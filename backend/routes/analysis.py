from fastapi import APIRouter
from pydantic import BaseModel

from services.fraud_detector import analyze_text


router = APIRouter(
    prefix="/analysis",
    tags=["Analysis"]
)


class AnalysisRequest(BaseModel):
    text: str


@router.post("/")
def analyze_offer(request: AnalysisRequest):

    result = analyze_text(request.text)

    return {
        "success": True,
        "data": result
    }