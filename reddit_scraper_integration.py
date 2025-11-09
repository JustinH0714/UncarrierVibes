"""
Reddit Scraper Integration for Real-time Dashboard Data
Scrapes Reddit posts and comments, analyzes sentiment, and feeds to API
"""
import os
import time
import httpx
from dotenv import load_dotenv
import praw
from datetime import datetime
from openai import OpenAI
from pathlib import Path

# Load environment variables from the correct location
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
API_BASE = os.getenv("API_BASE", "http://localhost:8000")

# Validate required env vars
if not all([REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, OPENAI_API_KEY]):
    raise ValueError(
        "Missing required environment variables. Please ensure .env contains:\n"
        "- REDDIT_CLIENT_ID\n"
        "- REDDIT_CLIENT_SECRET\n"
        "- REDDIT_USER_AGENT\n"
        "- OPENAI_API_KEY"
    )

# Initialize Reddit client
reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent=REDDIT_USER_AGENT
)

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

def extract_location_from_text(text):
    """Extract location mentions from text using OpenAI"""
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Extract only the city or location name from the text. If no specific location is mentioned, respond with 'Unknown'. Return only the location name, nothing else."},
                {"role": "user", "content": text}
            ],
            max_tokens=20,
            temperature=0.3
        )
        location = response.choices[0].message.content.strip()
        return location if location.lower() != "unknown" else None
    except Exception as e:
        print(f"[WARNING] Location extraction failed: {e}")
        return None

def detect_outage(text):
    """Detect if text mentions an outage or service issue"""
    outage_keywords = [
        "outage", "down", "not working", "no service", "no signal",
        "dropped call", "can't connect", "connection issue", "network down",
        "service down", "tower down", "no coverage", "dead zone"
    ]
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in outage_keywords)

def submit_to_api(text, location=None):
    """Submit feedback to the UncarrierVibes API"""
    try:
        url = f"{API_BASE}/api/v1/feedback/submit"
        params = {"text": text}
        if location:
            params["location"] = location
        
        with httpx.Client(timeout=30.0) as http_client:
            response = http_client.post(url, params=params)
            response.raise_for_status()
            result = response.json()
            print(f"✓ Submitted: {result['sentiment']} ({result['confidence']:.2f}) - {text[:50]}...")
            return result
    except Exception as e:
        print(f"✗ API submission failed: {e}")
        return None

def scrape_and_stream(
    subreddit_name="tmobile",
    post_limit=10,
    comment_limit=5,
    continuous=False,
    interval_minutes=5
):
    """
    Scrape Reddit and stream data to the API
    
    Args:
        subreddit_name: Name of subreddit to scrape
        post_limit: Number of posts to fetch per run
        comment_limit: Number of comments per post
        continuous: If True, run continuously
        interval_minutes: Minutes to wait between runs (if continuous)
    """
    iteration = 0
    
    while True:
        iteration += 1
        print(f"\n{'='*60}")
        print(f"Scraping iteration {iteration} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        
        try:
            subreddit = reddit.subreddit(subreddit_name)
            posts = list(subreddit.new(limit=post_limit))
            total_submitted = 0
            
            for idx, post in enumerate(posts, 1):
                print(f"\n[Post {idx}/{len(posts)}] {post.title[:60]}...")
                
                # Submit post title + selftext
                post_text = f"{post.title}. {post.selftext}".strip()
                if len(post_text) > 10:  # Only submit if meaningful
                    location = extract_location_from_text(post_text)
                    result = submit_to_api(post_text, location)
                    if result:
                        total_submitted += 1
                
                # Process comments
                post.comments.replace_more(limit=0)
                comments = post.comments[:comment_limit]
                
                for comment_idx, comment in enumerate(comments, 1):
                    comment_text = comment.body.strip()
                    if len(comment_text) > 15:  # Filter out short/meaningless comments
                        print(f"  [Comment {comment_idx}/{len(comments)}]")
                        location = extract_location_from_text(comment_text)
                        result = submit_to_api(comment_text, location)
                        if result:
                            total_submitted += 1
                        
                        # Rate limiting to avoid overwhelming OpenAI API
                        time.sleep(0.5)
                
                # Small delay between posts
                time.sleep(1)
            
            print(f"\n{'='*60}")
            print(f"✓ Iteration {iteration} complete: {total_submitted} items submitted")
            print(f"{'='*60}")
            
        except Exception as e:
            print(f"\n✗ Error during scraping: {e}")
        
        if not continuous:
            break
        
        # Wait before next iteration
        wait_seconds = interval_minutes * 60
        print(f"\n⏱  Waiting {interval_minutes} minutes until next scrape...")
        time.sleep(wait_seconds)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Reddit scraper for UncarrierVibes")
    parser.add_argument("--subreddit", default="tmobile", help="Subreddit to scrape")
    parser.add_argument("--posts", type=int, default=10, help="Number of posts per run")
    parser.add_argument("--comments", type=int, default=5, help="Comments per post")
    parser.add_argument("--continuous", action="store_true", help="Run continuously")
    parser.add_argument("--interval", type=int, default=5, help="Minutes between runs (if continuous)")
    
    args = parser.parse_args()
    
    print("🚀 Reddit Scraper for UncarrierVibes Dashboard")
    print(f"Subreddit: r/{args.subreddit}")
    print(f"Mode: {'Continuous' if args.continuous else 'One-time'}")
    if args.continuous:
        print(f"Interval: {args.interval} minutes")
    print()
    
    try:
        scrape_and_stream(
            subreddit_name=args.subreddit,
            post_limit=args.posts,
            comment_limit=args.comments,
            continuous=args.continuous,
            interval_minutes=args.interval
        )
    except KeyboardInterrupt:
        print("\n\n⏹  Scraper stopped by user")
    except Exception as e:
        print(f"\n\n✗ Fatal error: {e}")
