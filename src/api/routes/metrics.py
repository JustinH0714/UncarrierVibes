from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session
from src.db.database import get_db, Feedback
from datetime import datetime, timedelta
import os
import math
from typing import Dict, Any, List
try:
    import openai  # Optional refinement
except ImportError:
    openai = None

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

@router.get("/pulse")
async def get_emotion_pulse(window_minutes: int = 5, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Real-time emotion pulse metric.
    Computes average sentiment_score, intensity (avg absolute score), volume, and positive ratio over a recent window.
    Used by dashboard for the animated pulse visualization.
    """
    cutoff = datetime.utcnow() - timedelta(minutes=window_minutes)
    query = db.query(Feedback).filter(Feedback.timestamp >= cutoff)
    count = query.count()
    if count == 0:
        return {
            "window_minutes": window_minutes,
            "count": 0,
            "average_sentiment": 0.0,
            "intensity": 0.0,
            "positive_ratio": 0.0
        }

    # Aggregate in DB for efficiency
    avg_sentiment = db.query(func.avg(Feedback.sentiment_score)).filter(Feedback.timestamp >= cutoff).scalar() or 0.0
    avg_intensity = db.query(func.avg(func.abs(Feedback.sentiment_score))).filter(Feedback.timestamp >= cutoff).scalar() or 0.0
    positive_count = db.query(func.count(Feedback.id)).filter(Feedback.timestamp >= cutoff, Feedback.sentiment == "POSITIVE").scalar() or 0
    positive_ratio = positive_count / count if count else 0.0
    return {
        "window_minutes": window_minutes,
        "count": count,
        "average_sentiment": float(avg_sentiment),  # Range roughly [-1,1]
        "intensity": float(avg_intensity),          # Range [0,1]
        "positive_ratio": positive_ratio            # Range [0,1]
    }

def _tokenize(text: str) -> List[str]:
    """Lightweight tokenizer splitting on non-alphabetic chars and lowercasing."""
    tokens = []
    current = []
    for ch in text.lower():
        if ch.isalpha():
            current.append(ch)
        else:
            if current:
                tokens.append(''.join(current))
                current = []
    if current:
        tokens.append(''.join(current))
    return tokens

_STOPWORDS = {
    "the","and","a","an","to","for","of","in","on","at","with","my","our","it","is","was","are","be","have","has","had","this","that","very","so","up","down","out","all","no","not","just","keep","about","new","your","their","we","they","t"  # lightweight list
}

def _extract_keywords(feedback_rows: List[Feedback], limit: int = 8, negative_only: bool = False) -> List[str]:
    from collections import Counter
    counter = Counter()
    for row in feedback_rows:
        if negative_only and row.sentiment != "NEGATIVE":
            continue
        tokens = _tokenize(row.text)
        for tok in tokens:
            if tok in _STOPWORDS or len(tok) < 3:
                continue
            counter[tok] += 1
    return [w for w,_ in counter.most_common(limit)]

@router.get("/insights")
async def get_live_insights(lookback_minutes: int = 60, max_keywords: int = 8, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Generate lightweight live insights for the last period.
    Heuristic summary optionally refined by OpenAI if key present.
    """
    cutoff = datetime.utcnow() - timedelta(minutes=lookback_minutes)
    rows = db.query(Feedback).filter(Feedback.timestamp >= cutoff).order_by(Feedback.timestamp.desc()).all()
    total = len(rows)
    if total == 0:
        return {
            "lookback_minutes": lookback_minutes,
            "total": 0,
            "insights": ["No recent feedback in the selected time window."],
            "raw_summary": "No data"
        }
    negatives = [r for r in rows if r.sentiment == "NEGATIVE"]
    positives = [r for r in rows if r.sentiment == "POSITIVE"]
    neg_kw = _extract_keywords(negatives, limit=max_keywords, negative_only=False)
    pos_kw = _extract_keywords(positives, limit=max_keywords, negative_only=False)
    # Locations: top 3 locations for negative items
    from collections import Counter
    loc_counter = Counter([r.location for r in negatives if r.location])
    top_locs = [loc for loc,_ in loc_counter.most_common(3)]
    neg_ratio = len(negatives)/total if total else 0
    pos_ratio = len(positives)/total if total else 0
    raw_parts = []
    raw_parts.append(f"Total {total} feedback items; {pos_ratio*100:.1f}% positive, {neg_ratio*100:.1f}% negative.")
    if neg_kw:
        raw_parts.append("Frequent complaint keywords: " + ", ".join(neg_kw))
    if top_locs:
        raw_parts.append("Most mentioned negative locations: " + ", ".join(top_locs))
    if pos_kw:
        raw_parts.append("Positive buzz around: " + ", ".join(pos_kw))
    raw_summary = " " .join(raw_parts)

    insights = [raw_summary]
    # Optional refinement using OpenAI
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key and openai:
        try:
            openai.api_key = api_key
            prompt = ("You are an analyst. Turn the following bullet style aggregate metrics into 2 concise, "
                      "actionable insight sentences (no fluff):\n" + raw_summary)
            completion = openai.Completion.create(
                engine="text-davinci-003",
                prompt=prompt,
                max_tokens=120,
                temperature=0.3
            )
            ai_text = completion.choices[0].text.strip()
            if ai_text:
                # Split into sentences, keep first 2
                sent_list = [s.strip() for s in ai_text.split('.') if s.strip()]
                insights = sent_list[:2] or insights
        except Exception:
            # Fail silently, keep heuristic summary
            pass
    return {
        "lookback_minutes": lookback_minutes,
        "total": total,
        "insights": insights,
        "raw_summary": raw_summary,
        "negative_locations": top_locs,
        "positive_keywords": pos_kw,
        "negative_keywords": neg_kw
    }