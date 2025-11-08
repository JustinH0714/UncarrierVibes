from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.db.database import get_db
from src.ml.sentiment import SentimentAnalyzer
from typing import List, Dict

router = APIRouter()
sentiment_analyzer = SentimentAnalyzer()

@router.post("/analyze")
async def analyze_sentiment(text: str) -> Dict:
    """Analyze sentiment of a single text"""
    return sentiment_analyzer.analyze(text)

@router.post("/batch-analyze")
async def batch_analyze_sentiment(texts: List[str]) -> List[Dict]:
    """Analyze sentiment of multiple texts"""
    return sentiment_analyzer.batch_analyze(texts)