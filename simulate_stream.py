#!/usr/bin/env python3
"""Simulate a live stream of customer feedback into the UncarrierVibes API.
Stops cleanly with Ctrl+C.
"""
import requests
import random
import time
import signal
import sys
from datetime import datetime

BASE_URL = "http://localhost:8000"
SUBMIT_ENDPOINT = f"{BASE_URL}/api/v1/feedback/submit"

positive = [
    "Love the ultra fast 5G today!",
    "Chat support solved my issue instantly.",
    "Roaming worked flawlessly on my trip.",
    "Great upgrade deals this week!",
]
negative = [
    "Network slow in the stadium.",
    "App keeps crashing when I check usage.",
    "Dropped calls during commute again.",
    "Still waiting for promised callback.",
]
mixed = [
    "Good speeds but upload is weak.",
    "Helpful rep, but resolution took too long.",
    "Coverage improved but billing confusion remains.",
]

all_buckets = [positive, negative, mixed]

running = True

def handle_sigint(signum, frame):
    global running
    print("\n⏹ Stopping stream...")
    running = False

signal.signal(signal.SIGINT, handle_sigint)

print("🚿 Starting simulated feedback stream. Press Ctrl+C to stop.\n")

counter = 0
while running:
    bucket = random.choice(all_buckets)
    text = random.choice(bucket)
    # Add a little variation
    text_variant = f"{text} (evt {counter})" if random.random() < 0.4 else text
    try:
        r = requests.post(SUBMIT_ENDPOINT, params={"text": text_variant})
        if r.status_code == 200:
            data = r.json()
            print(f"[{datetime.utcnow().isoformat()}] {data['sentiment']:<8} {data['confidence']:.2f} | {text_variant}")
        else:
            print(f"Error {r.status_code} sending: {text_variant}")
    except Exception as e:
        print(f"Exception: {e}")
    counter += 1
    # Pace the stream (adjust for faster/slower demo)
    time.sleep(random.uniform(0.8, 2.0))

print("Done.")
