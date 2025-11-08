from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session
from src.db.database import get_db, Feedback
from datetime import datetime, timedelta
import pandas as pd

router = APIRouter()

@router.get("/sentiment-trend")
async def get_sentiment_trend(days: int = 7, db: Session = Depends(get_db)):
    """Get sentiment trend over time"""
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    results = db.query(
        func.date_trunc('hour', Feedback.timestamp).label('hour'),
        func.avg(Feedback.sentiment_score).label('avg_sentiment'),
        func.count(Feedback.id).label('count')
    ).filter(
        Feedback.timestamp >= cutoff
    ).group_by(
        func.date_trunc('hour', Feedback.timestamp)
    ).order_by(
        func.date_trunc('hour', Feedback.timestamp)
    ).all()
    
    return [
        {
            "timestamp": row.hour,
            "average_sentiment": float(row.avg_sentiment),
            "count": row.count
        }
        for row in results
    ]

@router.get("/summary")
async def get_metrics_summary(db: Session = Depends(get_db)):
    """Get summary metrics"""
    total = db.query(Feedback).count()
    
    if total == 0:
        return {
            "total_feedback": 0,
            "average_sentiment": 0,
            "positive_percentage": 0
        }
    
    avg_sentiment = db.query(func.avg(Feedback.sentiment_score)).scalar()
    positive_count = db.query(Feedback).filter(Feedback.sentiment == "POSITIVE").count()
    
    return {
        "total_feedback": total,
        "average_sentiment": float(avg_sentiment),
        "positive_percentage": (positive_count / total) * 100
    }