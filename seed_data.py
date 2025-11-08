#!/usr/bin/env python3
import requests
import random
import time

BASE_URL = "http://localhost:8000"

positive = [
    "T-Mobile's 5G speed is blazing fast!",
    "Customer support was super helpful and quick.",
    "Great coverage in my area, loving it!",
    "Affordable plans and excellent service.",
    "Switched from another carrier and it's been fantastic."
]

negative = [
    "My calls keep dropping in downtown.",
    "Billing issues again this month, very frustrating.",
    "Support wait times are too long.",
    "5G barely works in my neighborhood.",
    "Data throttling is making it unusable."
]

mixed = [
    "Great speeds but sometimes inconsistent.",
    "Good value, but coverage could be better.",
    "Love the plan, not happy with recent outages.",
    "Customer service is friendly, but slow.",
    "Signal is strong at home but weak at work."
]

all_feedback = [
    (positive, "positive"),
    (negative, "negative"),
    (mixed, "mixed")
]

def submit(text: str):
    r = requests.post(f"{BASE_URL}/api/v1/feedback/submit", params={"text": text})
    if r.status_code == 200:
        data = r.json()
        print(f"✓ {data['sentiment']:<8} {data['confidence']:.2f}  | {text}")
    else:
        print(f"✗ {r.status_code}  | {text}")

if __name__ == "__main__":
    print("Seeding feedback data...\n")
    for bucket, _ in all_feedback:
        for text in bucket:
            submit(text)
            time.sleep(0.2)
    print("\nDone. Try the dashboard at http://localhost:8501 and API at http://localhost:8000/docs")
