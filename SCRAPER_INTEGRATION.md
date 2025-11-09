# Reddit Scraper Integration for Real-Time Dashboard

This integration scrapes Reddit posts and comments from r/tmobile (or any subreddit) and feeds them to your UncarrierVibes API in real-time, which then appears on your dashboard.

## How It Works

1. **Scrapes Reddit**: Uses PRAW to fetch recent posts and comments from r/tmobile
2. **Extracts Location**: Uses OpenAI to detect city/location mentions in text
3. **Detects Outages**: Identifies posts mentioning service issues
4. **Submits to API**: Sends each post/comment to your `/api/v1/feedback/submit` endpoint
5. **Dashboard Updates**: Data appears on your Streamlit dashboard in real-time

## Setup

### Prerequisites
Make sure your API server is running:
```bash
cd /Users/justin/UncarrierVibes1
source venv/bin/activate
uvicorn src.api.main:app --reload
```

### Environment Variables
Your `.env` file should already have:
```
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_secret
REDDIT_USER_AGENT=TmobileUTD2025
OPENAI_API_KEY=your_openai_key
API_BASE=http://localhost:8000
```

## Usage

### One-Time Scrape (Default)
```bash
cd /Users/justin/UncarrierVibes1
source venv/bin/activate
python reddit_scraper_integration.py
```

### Continuous Mode (Recommended for Demo)
Runs every 5 minutes to keep dashboard updated:
```bash
python reddit_scraper_integration.py --continuous --interval 5
```

### Custom Options
```bash
# Scrape different subreddit
python reddit_scraper_integration.py --subreddit wirelesscarriers

# More posts per run
python reddit_scraper_integration.py --posts 20 --comments 10

# Continuous with 10-minute intervals
python reddit_scraper_integration.py --continuous --interval 10
```

## Command-Line Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--subreddit` | `tmobile` | Subreddit to scrape |
| `--posts` | `10` | Number of posts to fetch per run |
| `--comments` | `5` | Number of comments per post |
| `--continuous` | `False` | Run continuously (flag) |
| `--interval` | `5` | Minutes between scraping runs |

## What Gets Submitted

For each Reddit post/comment:
- **Text**: Post title + body or comment text
- **Location**: Auto-extracted city/location (if mentioned)
- **Sentiment**: Analyzed by your API's sentiment analyzer
- **Timestamp**: When it was posted
- **Outage Detection**: Flagged if keywords like "outage", "down", "no service" detected

## Example Output

```
🚀 Reddit Scraper for UncarrierVibes Dashboard
Subreddit: r/tmobile
Mode: Continuous
Interval: 5 minutes

============================================================
Scraping iteration 1 - 2025-11-09 14:30:15
============================================================

[Post 1/10] 5G coverage question in Seattle...
✓ Submitted: POSITIVE (0.92) - 5G coverage question in Seattle. I recently moved to...

  [Comment 1/5]
✓ Submitted: NEGATIVE (0.85) - Service has been terrible downtown lately...

============================================================
✓ Iteration 1 complete: 45 items submitted
============================================================

⏱  Waiting 5 minutes until next scrape...
```

## Integration with Dashboard

Once data is submitted to the API, it automatically appears on your dashboard:

1. **Overview Tab**: Shows in recent feedback and sentiment charts
2. **Pulse Tab**: Updates real-time sentiment gauge
3. **Insights Tab**: AI analyzes for themes and keywords
4. **Outages Tab**: Posts mentioning outages appear on the map
5. **All Reviews Tab**: Searchable/filterable view of all data

## Tips for Demo

### Quick Test
1. Start API server: `./start.sh`
2. Start dashboard: `streamlit run src/dashboard/main.py`
3. Run scraper once: `python reddit_scraper_integration.py`
4. Watch dashboard update with real Reddit data!

### Continuous Demo
For a live demo that keeps updating:
```bash
# Terminal 1: API
./start.sh

# Terminal 2: Dashboard
streamlit run src/dashboard/main.py

# Terminal 3: Scraper (continuous)
python reddit_scraper_integration.py --continuous --interval 5
```

Enable "Auto-refresh" on the dashboard sidebar to see updates every 5 seconds.

## Rate Limiting

The scraper includes built-in delays to avoid overwhelming APIs:
- 0.5 seconds between comments (OpenAI rate limiting)
- 1 second between posts
- Configurable interval between full scraping runs

## Troubleshooting

### "API submission failed"
- Check API server is running at http://localhost:8000
- Verify `API_BASE` in `.env`

### "OpenAI API failed"
- Check `OPENAI_API_KEY` in `.env`
- Verify you have credits on OpenAI account

### "Reddit API failed"
- Verify Reddit credentials in `.env`
- Check Reddit app permissions

### No data appearing on dashboard
- Click "Refresh now" in dashboard sidebar
- Enable auto-refresh checkbox
- Check API logs for errors

## Stopping the Scraper

Press `Ctrl+C` to gracefully stop the scraper at any time.

## Next Steps

- Add more subreddits to scrape
- Implement keyword filtering
- Add deduplication to avoid reprocessing same posts
- Store last scraped post ID to only fetch new content
- Add webhook notifications for critical outages
