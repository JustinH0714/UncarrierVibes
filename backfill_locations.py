#!/usr/bin/env python3
"""
Backfill missing location and coordinates for existing feedback rows by scanning
review text for known city keywords.

Usage:
  python backfill_locations.py

Requires DATABASE_URL in environment or .env to be loaded by src.db.database.
"""
import os
from typing import Optional
from src.db.database import get_db, Feedback
from src.ml.location import extract_location


def backfill(batch_size: int = 500) -> None:
    updated = 0
    scanned = 0
    session = next(get_db())
    try:
        # Select rows missing location OR missing coords
        q = session.query(Feedback).filter(
            (Feedback.location == None) | (Feedback.latitude == None) | (Feedback.longitude == None)  # noqa: E711
        ).order_by(Feedback.id.asc())
        for fb in q.yield_per(batch_size):
            scanned += 1
            auto = extract_location(fb.text or "")
            if not auto:
                continue
            loc, lat, lon = auto
            changed = False
            if fb.location is None:
                fb.location = loc
                changed = True
            if fb.latitude is None:
                fb.latitude = lat
                changed = True
            if fb.longitude is None:
                fb.longitude = lon
                changed = True
            if changed:
                updated += 1
        session.commit()
    finally:
        session.close()
    print(f"Scanned={scanned}, Updated={updated}")


if __name__ == "__main__":
    backfill()
