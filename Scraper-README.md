

## `README.md`

```markdown
# Reddit Sentiment Scraper

This tool scrapes posts and comments from [r/tmobile](https://www.reddit.com/r/tmobile), classifies their sentiment using OpenAI's GPT model, and outputs the results in JSONL format for integration into the UncarrierVibes web console.

---

## Dependencies

Install required Python packages:

```bash
python3 -m pip install --user praw "openai<1" "python-dotenv<1"
```

---

## Environment Setup

Create a `.env` file in the same directory as `scraper.py` with the following credentials:

```env
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USER_AGENT=UncarrierVibes scraper by u/your_reddit_username
OPENAI_API_KEY=your_openai_key
```

> ⚠️ **Important:** Never commit `.env` to GitHub. Add it to `.gitignore`.

---

## 🚀 Running the Scraper

From the `~/scraper` directory:

```bash
python3 scraper.py
```

This will:

- Scrape the latest posts and comments from r/tmobile  
- Score each item using OpenAI sentiment classification  
- Save results to `reddit_sentiment.jsonl`

---

## Output Format

Each line in `reddit_sentiment.jsonl` is a JSON object:

```json
{
  "type": "comment",
  "text": "I love T-Mobile's new plan!",
  "timestamp": 1699470000,
  "parent_post": "New plan announcement",
  "sentiment": "Positive"
}
```

---

## Integration with Web Console

To integrate into the UncarrierVibes web console:

1. **Backend ingestion**  
   Parse `reddit_sentiment.jsonl` into your database or API layer.

2. **Frontend display**  
   Visualize sentiment trends, post/comment breakdowns, or keyword clouds.

3. **Automation (optional)**  
   Use `cron` or GitHub Actions to run `scraper.py` on a schedule.

---

## Testing

To verify setup:

```bash
python3 -c "import praw, openai; from dotenv import load_dotenv; print('Modules OK')"
```

---

##  File Permissions

Ensure correct ownership and access:

```bash
# Set ownership to your user
sudo chown docker:docker ~/scraper

# Set secure permissions
chmod 744 ~/scraper/scraper.py
chmod 600 ~/scraper/.env
chmod 644 ~/scraper/reddit_sentiment.jsonl
```

---

## Author

Developed by **Ben Lean** for [UncarrierVibes](https://github.com/JustinH0714/UncarrierVibes)  
GitHub: [github.com/JustinH0714/UncarrierVibes](https://github.com/JustinH0714/UncarrierVibes)
```

