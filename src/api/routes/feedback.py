from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.db.database import get_db, Feedback
from src.ml.sentiment import SentimentAnalyzer
from typing import List, Dict
from datetime import datetime

router = APIRouter()
sentiment_analyzer = SentimentAnalyzer()

@router.post("/submit")
async def submit_feedback(text: str, db: Session = Depends(get_db)) -> Dict:
    """Submit new feedback and analyze its sentiment"""
    # Analyze sentiment
    analysis = sentiment_analyzer.analyze(text)
    
    # Create feedback entry
    feedback = Feedback(
        text=text,
        sentiment=analysis["sentiment"],
        confidence=analysis["confidence"],
        sentiment_score=analysis["sentiment_score"],
        timestamp=datetime.utcnow()
    )
    
    # Save to database
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    
    return {
        "id": feedback.id,
        "text": feedback.text,
        "sentiment": feedback.sentiment,
        "confidence": feedback.confidence,
        "sentiment_score": feedback.sentiment_score,
        "timestamp": feedback.timestamp
    }

@router.get("/latest")
async def get_latest_feedback(limit: int = 10, db: Session = Depends(get_db)):
    """Get the latest feedback entries"""
    feedback = db.query(Feedback)\
        .order_by(Feedback.timestamp.desc())\
        .limit(limit)\
        .all()
    
    return feedback

@router.get("/stats")
async def get_feedback_stats(db: Session = Depends(get_db)):
    """Get feedback statistics"""
    total = db.query(Feedback).count()
    positive = db.query(Feedback).filter(Feedback.sentiment == "POSITIVE").count()
    negative = total - positive
    
    return {
        "total": total,
        "positive": positive,
        "negative": negative,
        "positive_percentage": (positive / total * 100) if total > 0 else 0
    }