from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from src.db.database import get_db, Feedback
from src.ml.sentiment import SentimentAnalyzer
from src.ml.location import extract_location
from typing import List, Dict, Optional
from datetime import datetime

router = APIRouter()
sentiment_analyzer = SentimentAnalyzer()

@router.post("/submit")
async def submit_feedback(
    text: str,
    location: Optional[str] = None,
    latitude: Optional[float] = Query(default=None, description="Latitude of the feedback origin"),
    longitude: Optional[float] = Query(default=None, description="Longitude of the feedback origin"),
    db: Session = Depends(get_db)
) -> Dict:
    """Submit new feedback with optional location and analyze its sentiment.

    Simple outage classification: mark is_outage True if text contains outage keywords.
    """
    analysis = sentiment_analyzer.analyze(text)

    outage_keywords = ["outage", "power", "blackout", "no service", "network down", "cant connect", "cannot connect"]
    lowered = text.lower()
    is_outage = any(k in lowered for k in outage_keywords)

    # Auto extract location if none provided (heuristic city keyword match)
    if location is None:
        auto = extract_location(text)
        if auto:
            auto_loc, auto_lat, auto_lon = auto
            location = auto_loc
            if latitude is None:
                latitude = auto_lat
            if longitude is None:
                longitude = auto_lon

    feedback = Feedback(
        text=text,
        sentiment=analysis["sentiment"],
        confidence=analysis["confidence"],
        sentiment_score=analysis["sentiment_score"],
        timestamp=datetime.utcnow(),
        location=location,
        latitude=latitude,
        longitude=longitude,
        is_outage=is_outage
    )

    db.add(feedback)
    db.commit()
    db.refresh(feedback)

    return {
        "id": feedback.id,
        "text": feedback.text,
        "sentiment": feedback.sentiment,
        "confidence": feedback.confidence,
        "sentiment_score": feedback.sentiment_score,
        "timestamp": feedback.timestamp,
        "location": feedback.location,
        "latitude": feedback.latitude,
        "longitude": feedback.longitude,
        "is_outage": feedback.is_outage
    }
@router.get("/latest")
async def get_latest_feedback(limit: int = 10, db: Session = Depends(get_db)):
    """Get the latest feedback entries"""
    feedback = db.query(Feedback)\
        .order_by(Feedback.timestamp.desc())\
        .limit(limit)\
        .all()
    
    return feedback

@router.get("/outages")
async def get_outage_feedback(limit: int = 50, db: Session = Depends(get_db)):
    """Get recent outage-related feedback entries"""
    feedback = db.query(Feedback)\
        .filter(Feedback.is_outage == True)\
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