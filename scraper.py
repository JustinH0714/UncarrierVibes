import os
import json
import time
from dotenv import load_dotenv
import praw
import openai

# Load environment variables
print("[INFO] Loading environment variables...")
load_dotenv()
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize Reddit and OpenAI clients
print("[INFO] Initializing Reddit and OpenAI clients...")
reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent=REDDIT_USER_AGENT
)
openai.api_key = OPENAI_API_KEY

# Sentiment scoring function
def get_sentiment(text):
    print(f"[INFO] Scoring sentiment for text: {text[:60]}...")
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a sentiment analysis assistant."},
                {"role": "user", "content": f"Classify the sentiment of this text as Positive, Neutral, or Negative:\n\n{text}"}
            ]
        )
        sentiment = response['choices'][0]['message']['content']
        print(f"[RESULT] Sentiment: {sentiment}")
        return sentiment
    except Exception as e:
        print(f"[ERROR] OpenAI API failed: {e}")
        return "Unknown"

# Scrape and score posts/comments
def scrape_and_score(subreddit_name="tmobile", post_limit=10, comment_limit=5, output_file="reddit_sentiment.jsonl"):
    print(f"[INFO] Scraping r/{subreddit_name}...")
    results = []
    subreddit = reddit.subreddit(subreddit_name)
    posts = list(subreddit.new(limit=post_limit))

    for i, post in enumerate(posts):
        print(f"[INFO] Processing post {i+1}/{len(posts)}: {post.title[:60]}...")
        post_data = {
            "type": "post",
            "title": post.title,
            "text": post.selftext,
            "timestamp": post.created_utc,
            "sentiment": get_sentiment(post.title + " " + post.selftext)
        }
        results.append(post_data)

        post.comments.replace_more(limit=0)
        for j, comment in enumerate(post.comments[:comment_limit]):
            print(f"  [INFO] Processing comment {j+1}/{comment_limit}...")
            comment_data = {
                "type": "comment",
                "text": comment.body,
                "timestamp": comment.created_utc,
                "parent_post": post.title,
                "sentiment": get_sentiment(comment.body)
            }
            results.append(comment_data)

    # Save to JSONL
    print(f"[INFO] Saving results to {output_file}...")
    with open(output_file, "w") as f:
        for item in results:
            f.write(json.dumps(item) + "\n")

    print(f"[DONE] Saved {len(results)} items to {output_file}")

# Entry point
if __name__ == "__main__":
    start = time.time()
    print("[START] Running Reddit sentiment scraper...")
    scrape_and_score()
    print(f"[COMPLETE] Finished in {round(time.time() - start, 2)} seconds.")
