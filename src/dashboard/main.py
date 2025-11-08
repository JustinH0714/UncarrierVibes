import os
import time
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
import httpx

# Configure the page
st.set_page_config(
    page_title="UncarrierVibes Dashboard",
    page_icon="📊",
    layout="wide"
)

# Initialize session state
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=[
        "timestamp", "sentiment_score", "sentiment", "confidence", "text"
    ])

# Allow overriding the API base via environment variable first, then optional Streamlit secrets.
# Avoid accessing st.secrets if no secrets file exists.
API_BASE = os.getenv("API_BASE")
if not API_BASE:
    try:
        # Accessing st.secrets may raise FileNotFoundError if no secrets.toml; guard with try/except.
        API_BASE = st.secrets.get("API_BASE", None)  # type: ignore[attr-defined]
    except Exception:
        API_BASE = None
API_BASE = API_BASE or "http://localhost:8000"

def _normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure correct dtypes and columns for dashboard usage."""
    if df.empty:
        return df
    # Parse timestamps and ensure column order exists
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    for col in ["sentiment_score", "confidence"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    # Keep expected columns if present (include id for de-dup and reference)
    cols = ["id", "timestamp", "sentiment_score", "sentiment", "confidence", "text"]
    existing_cols = [c for c in cols if c in df.columns]
    return df[existing_cols]

def fetch_latest_data(limit: int = 50):
    """Fetch latest feedback entries from the API and merge into session state."""
    url = f"{API_BASE}/api/v1/feedback/latest"
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(url, params={"limit": limit})
            response.raise_for_status()
            payload = response.json()
            if isinstance(payload, list) and len(payload) > 0:
                new_df = pd.DataFrame(payload)
                # Normalize and reduce to expected columns
                new_df = _normalize_dataframe(new_df)
                # Merge, de-duplicate by optional 'id' if present
                combined = pd.concat([st.session_state.data, new_df], ignore_index=True)
                if "id" in new_df.columns:
                    combined = combined.drop_duplicates(subset=["id"], keep="last")
                # Sort by timestamp if available
                if "timestamp" in combined.columns:
                    combined = combined.sort_values("timestamp")
                st.session_state.data = combined.reset_index(drop=True)
    except httpx.HTTPError as e:
        st.error(f"API error fetching data from {url}: {e}")
    except Exception as e:
        st.error(f"Unexpected error fetching data: {str(e)}")

# Main dashboard layout
st.title("📊 UncarrierVibes Dashboard")

# Tabs / Channels
tab_overview, tab_all = st.tabs(["Overview", "All Reviews"])

# Controls
with st.sidebar:
    st.markdown("### Data Controls")
    auto_refresh = st.checkbox("Auto-refresh every 5s", value=False)
    fetch_limit = st.slider("Fetch limit", min_value=10, max_value=200, value=50, step=10)
    if st.button("Refresh now"):
        fetch_latest_data(limit=fetch_limit)
        st.success("Data refreshed.")

# Initial fetch on first load if no data
if st.session_state.data.empty:
    fetch_latest_data(limit=50)

with tab_overview:
    # Metrics row (positive vs negative plus total)
    colA, colB, colC, colD = st.columns(4)

    total_feedback = len(st.session_state.data)
    positive_percent = (st.session_state.data["sentiment"] == "POSITIVE").mean() * 100 if total_feedback else 0.0
    negative_percent = 100 - positive_percent if total_feedback else 0.0
    avg_sentiment = st.session_state.data["sentiment_score"].mean() if total_feedback else 0.0

    with colA:
        st.metric("Total Reviews", total_feedback)
    with colB:
        st.metric("Positive %", f"{positive_percent:.1f}%")
    with colC:
        st.metric("Negative %", f"{negative_percent:.1f}%")
    with colD:
        st.metric("Avg Sentiment Score", f"{avg_sentiment:.2f}")

    # Donut chart for positive vs negative distribution
    st.subheader("Sentiment Distribution")
    if total_feedback:
        dist_fig = px.pie(
            names=["Positive", "Negative"],
            values=[positive_percent, negative_percent],
            hole=0.55,
            color=["Positive", "Negative"],
            color_discrete_map={"Positive": "#34c759", "Negative": "#ff3b30"},
        )
        dist_fig.update_layout(showlegend=True)
        st.plotly_chart(dist_fig, use_container_width=True)
    else:
        st.info("No reviews yet.")

    # Sentiment trend chart
    st.subheader("Sentiment Trend")
    if not st.session_state.data.empty:
        fig = px.line(
            st.session_state.data,
            x="timestamp",
            y="sentiment_score",
            title="Customer Sentiment Over Time"
        )
        st.plotly_chart(fig, use_container_width=True)

    # Recent feedback table (channel snippet)
    st.subheader("Recent Feedback")
    if not st.session_state.data.empty:
        recent_data = st.session_state.data.tail(15).sort_values("timestamp", ascending=False)
        st.dataframe(
            recent_data[["timestamp", "text", "sentiment", "confidence"]],
            use_container_width=True
        )

with tab_all:
    st.header("All Reviews Channel")
    if st.button("Reload All Reviews"):
        # Attempt to fetch a larger batch while keeping de-dup logic
        fetch_latest_data(limit=200)
        st.success("Reloaded reviews.")

    search_query = st.text_input("Search reviews", placeholder="Type part of a comment...")
    sentiment_filter = st.multiselect("Filter sentiment", options=["POSITIVE", "NEGATIVE"], default=[])

    df_all = st.session_state.data.copy()
    if not df_all.empty:
        if search_query:
            df_all = df_all[df_all["text"].str.contains(search_query, case=False, na=False)]
        if sentiment_filter:
            df_all = df_all[df_all["sentiment"].isin(sentiment_filter)]
        df_all = df_all.sort_values("timestamp", ascending=False)

        # Simple pagination
        page_size = 25
        total_pages = max(1, (len(df_all) + page_size - 1) // page_size)
        page = st.number_input("Page", min_value=1, max_value=total_pages, value=1, step=1)
        start = (page - 1) * page_size
        end = start + page_size
        page_df = df_all.iloc[start:end]

        st.caption(f"Showing {len(page_df)} of {len(df_all)} filtered reviews (Page {page}/{total_pages})")
        st.dataframe(page_df[["timestamp", "text", "sentiment", "confidence"]], use_container_width=True)
    else:
        st.info("No reviews available.")

# (Moved charts and recent table into tabs above)

# Optional auto-refresh loop
if auto_refresh:
    # Throttle reruns every 5 seconds
    last = st.session_state.get("_last_auto_refresh", 0)
    now = time.time()
    if now - last >= 5:
        fetch_latest_data(limit=fetch_limit)
        st.session_state["_last_auto_refresh"] = now
    # Sleep and rerun to keep the loop going
    time.sleep(5)
    st.experimental_rerun()