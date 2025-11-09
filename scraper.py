import os
import json
import time
from typing import Optional
from dotenv import load_dotenv
import praw
import httpx

# OpenAI is optional; import lazily
try:
    import openai  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    openai = None  # type: ignore

# Load environment variables (.env in same dir or project root)
print("[INFO] Loading environment variables...")
load_dotenv()
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "UncarrierVibes scraper")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")
SUBREDDITS = [s.strip() for s in os.getenv("SUBREDDITS", "tmobile").split(",") if s.strip()]
POST_LIMIT = int(os.getenv("POST_LIMIT", "10"))
COMMENT_LIMIT = int(os.getenv("COMMENT_LIMIT", "5"))
OUTPUT_FILE = os.getenv("SCRAPER_OUTPUT", "reddit_sentiment.jsonl")
USE_OPENAI_SUMMARY = os.getenv("USE_OPENAI_SUMMARY", "0") == "1"

# Initialize Reddit client
print("[INFO] Initializing Reddit client...")
if not REDDIT_CLIENT_ID or not REDDIT_CLIENT_SECRET:
    raise RuntimeError("Missing REDDIT_CLIENT_ID/REDDIT_CLIENT_SECRET in environment")
reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent=REDDIT_USER_AGENT,
)

# Configure OpenAI (optional)
if openai and OPENAI_API_KEY:
    try:
        # Support both legacy and new SDKs; assign key if attr exists
        setattr(openai, "api_key", OPENAI_API_KEY)
        print("[INFO] OpenAI enabled (optional summarization)")
    except Exception:
        print("[WARN] OpenAI SDK not configured; continuing without summarization")
        openai = None
else:
    print("[INFO] OpenAI not configured; skipping summarization")

def maybe_summarize(text: str, max_chars: int = 500) -> str:
    """Optionally summarize/trim long text before sending to API (keeps it concise)."""
    if not text:
        return text
    if not USE_OPENAI_SUMMARY or not openai or not OPENAI_API_KEY:
        return text if len(text) <= max_chars else (text[: max_chars - 3] + "...")
    try:
        # Use legacy ChatCompletion if available; otherwise return truncated text
        if hasattr(openai, "ChatCompletion"):
            resp = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Summarize user text into a concise 1-2 sentence gist."},
                    {"role": "user", "content": text},
                ],
                temperature=0.3,
                max_tokens=120,
            )
            return resp["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"[WARN] OpenAI summarize failed: {e}")
    return text if len(text) <= max_chars else (text[: max_chars - 3] + "...")


def submit_feedback(text: str) -> Optional[dict]:
    """Send feedback text to our FastAPI backend. Returns the created record JSON or None."""
    if not text:
        return None
    url = f"{API_BASE}/api/v1/feedback/submit"
    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.post(url, params={"text": text})
            r.raise_for_status()
            return r.json()
    except Exception as e:
        print(f"[ERROR] Failed to submit feedback: {e} ({url})")
        return None

# Scrape and score posts/comments
def scrape_and_submit(subreddit_name: str, post_limit: int, comment_limit: int, output_file: Optional[str] = OUTPUT_FILE):
    print(f"[INFO] Scraping r/{subreddit_name}...")
    results = []
    subreddit = reddit.subreddit(subreddit_name)
    posts = list(subreddit.new(limit=post_limit))

    for i, post in enumerate(posts):
        title = post.title or ""
        body = post.selftext or ""
        text = (title + "\n\n" + body).strip()
        short = maybe_summarize(text)
        print(f"[INFO] Post {i+1}/{len(posts)}: {title[:80]}...")
        created = submit_feedback(short)
        if created:
            results.append({"kind": "post", "id": created.get("id"), "title": title, "timestamp": post.created_utc})

        # Comments
        try:
            post.comments.replace_more(limit=0)
            for j, comment in enumerate(post.comments[:comment_limit]):
                ctext = (comment.body or "").strip()
                if not ctext:
                    continue
                cshort = maybe_summarize(ctext)
                print(f"  [INFO] Comment {j+1}/{comment_limit}: {ctext[:60]}...")
                created_c = submit_feedback(cshort)
                if created_c:
                    results.append({"kind": "comment", "id": created_c.get("id"), "timestamp": comment.created_utc, "parent": title[:120]})
                # Be nice to rate limits
                time.sleep(0.3)
        except Exception as e:
            print(f"[WARN] Skipping comments due to error: {e}")
        # Light throttle between posts
        time.sleep(0.5)

    # Optional save to JSONL for audit/debug
    if output_file:
        print(f"[INFO] Saving IDs to {output_file}...")
        with open(output_file, "w") as f:
            for item in results:
                f.write(json.dumps(item) + "\n")
        print(f"[DONE] Saved {len(results)} items to {output_file}")

# Entry point
if __name__ == "__main__":
    start = time.time()
    print("[START] Reddit scraper -> API submitter")
    for sub in SUBREDDITS:
        scrape_and_submit(subreddit_name=sub, post_limit=POST_LIMIT, comment_limit=COMMENT_LIMIT, output_file=OUTPUT_FILE)
    print(f"[COMPLETE] Finished in {round(time.time() - start, 2)}s.")
