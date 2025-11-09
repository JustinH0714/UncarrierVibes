import os
import time
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
try:
    import pydeck as pdk  # For map visualization
except ImportError:  # Gracefully handle missing dependency
    pdk = None
from datetime import datetime, timedelta
import httpx

# Configure the page
st.set_page_config(
    page_title="UncarrierVibes Dashboard",
    page_icon="📊",
    layout="wide"
)

# Global CSS for professional styling
st.markdown(
    """
    <style>
    .hero {background: linear-gradient(90deg, rgba(226,0,116,0.12), rgba(226,0,116,0.02)); border: 1px solid rgba(226,0,116,0.25); padding: 16px 20px; border-radius: 16px;}
    .hero h1 {margin: 0; font-size: 1.4rem;}
    .tagline {margin: 2px 0 0 0; opacity: 0.85;}
    .stTabs [role="tablist"] button[role="tab"] { padding: 10px 14px; border-radius: 10px; margin-right: 6px; }
    .stTabs [role="tablist"] button[aria-selected="true"] { background: rgba(226,0,116,0.16); color: #E20074; }
    div[data-testid="stMetric"] { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); padding: 12px; border-radius: 12px; }
    .block-container { padding-top: 1rem; }
    </style>
    """,
    unsafe_allow_html=True
)

# Initialize session state
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=[
        "id", "timestamp", "sentiment_score", "sentiment", "confidence", "text", "location", "latitude", "longitude", "is_outage"
    ])

# Allow overriding the API base via environment variable only
# Do NOT access st.secrets to avoid FileNotFoundError when secrets.toml is missing
API_BASE = os.getenv("API_BASE", "http://localhost:8000")

def _normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure correct dtypes and columns for dashboard usage."""
    if df.empty:
        return df
    # Parse timestamps and ensure column order exists
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    for col in ["sentiment_score", "confidence", "latitude", "longitude"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    # Coerce outage flag to boolean for proper checkbox rendering
    if "is_outage" in df.columns:
        if df["is_outage"].dtype != bool:
            df["is_outage"] = df["is_outage"].fillna(False).astype(bool)
    # Keep expected columns if present (include id for de-dup and reference)
    cols = ["id", "timestamp", "sentiment_score", "sentiment", "confidence", "text", "location", "latitude", "longitude", "is_outage"]
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
                if st.session_state.data.empty:
                    combined = new_df.copy()
                else:
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
st.markdown(
        """
        <div class="hero">
            <div class="hero-content">
                <h1>UncarrierVibes Intelligence</h1>
                <p class="tagline">Real-time sentiment pulse, outage awareness, and customer insight for the T‑Mobile experience.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
)

# Tabs / Channels (separate Pulse & Insights for cleaner layout)
tab_overview, tab_pulse, tab_insights, tab_all, tab_outages, tab_submit = st.tabs([
    "Overview", "Pulse", "Insights", "All Reviews", "Outages", "Submit Review"
])

# Controls
with st.sidebar:
    st.markdown("### Data Controls")
    auto_refresh = st.checkbox("Auto-refresh every 5s", value=False)
    fetch_limit = st.slider("Fetch limit", min_value=10, max_value=200, value=50, step=10)
    if st.button("Refresh now", use_container_width=True):
        fetch_latest_data(limit=fetch_limit)
        st.success("Data refreshed.")
    st.markdown("---")
    st.caption("Brand theme applied. Auto-refresh will also update Pulse and Insights tabs.")

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
            title="Customer Sentiment Over Time",
        )
        fig.update_layout(margin=dict(l=10, r=10, t=60, b=10))
        st.plotly_chart(fig, use_container_width=True)

    # Recent feedback table (channel snippet)
    st.subheader("Recent Feedback")
    if not st.session_state.data.empty:
        recent_data = st.session_state.data.tail(15).sort_values("timestamp", ascending=False)
        show_cols = [c for c in ["timestamp", "text", "sentiment", "confidence", "location"] if c in recent_data.columns]
        st.dataframe(
            recent_data[show_cols],
            use_container_width=True
        )

    # Keep Overview focused on core metrics & recent feedback only.
with tab_pulse:
    st.header("Emotion Pulse")
    st.caption("Real-time sentiment values (text only – visuals removed as requested).")
    # Fetch current pulse metric (no charts, just key metrics)
    try:
        with httpx.Client(timeout=10.0) as client:
            pulse = client.get(f"{API_BASE}/api/v1/metrics/pulse", params={"window_minutes": 5}).json()
        val = float(pulse.get("average_sentiment", 0.0))
        intensity = float(pulse.get("intensity", 0.0))
        count = int(pulse.get("count", 0))
        pos_ratio = float(pulse.get("positive_ratio", 0.0))
        st.write(f"Avg Sentiment (5m): {val:.2f}")
        st.write(f"Intensity: {intensity:.2f}")
        st.write(f"Samples: {count}")
        st.write(f"Positive Ratio: {pos_ratio:.2f}")
    except Exception as e:
        st.warning(f"Pulse unavailable: {e}")
    st.caption("Tip: Enable auto-refresh in the sidebar to keep these numbers live.")

with tab_insights:
    st.header("Live Insights")
    st.caption("Automatic summaries (text only – visuals removed as requested).")
    try:
        with httpx.Client(timeout=15.0) as client:
            insights = client.get(f"{API_BASE}/api/v1/metrics/insights", params={"lookback_minutes": 60}).json()
        for line in insights.get("insights", [])[:5]:
            st.markdown(f"- {line}")
    except Exception as e:
        st.warning(f"Insights unavailable: {e}")

with tab_all:
    st.header("All Reviews Channel")
    if st.button("Reload All Reviews", use_container_width=True):
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

        show_all_cols = [c for c in ["timestamp", "text", "sentiment", "confidence", "location", "is_outage"] if c in page_df.columns]
        # Configure boolean column as checkbox and rename for clarity
        column_config = {}
        if "is_outage" in show_all_cols:
            try:
                column_config = {
                    "is_outage": st.column_config.CheckboxColumn(
                        label="Outage",
                        help="Checked when text suggests an outage",
                        default=False,
                        disabled=True,
                    )
                }
            except Exception:
                column_config = {"is_outage": "Outage"}

        st.dataframe(page_df[show_all_cols], use_container_width=True, column_config=column_config)
    else:
        st.info("No reviews available.")

with tab_outages:
    st.header("Outage Reports & Map")
    
    # Fetch outage-specific data directly (independent of latest cache) if requested
    if st.button("Refresh Outages", use_container_width=True):
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(f"{API_BASE}/api/v1/feedback/outages", params={"limit": 200})
                resp.raise_for_status()
                outage_payload = resp.json()
                outage_df = _normalize_dataframe(pd.DataFrame(outage_payload))
                st.session_state.outages = outage_df
                st.success(f"Loaded {len(outage_df)} outage entries")
        except Exception as e:
            st.error(f"Failed to load outages: {e}")

    outage_df = st.session_state.get("outages", pd.DataFrame())
    
    # Location filter controls
    col_filter1, col_filter2 = st.columns([2, 1])
    with col_filter1:
        user_location = st.text_input("Your location (City)", placeholder="e.g., Seattle, Chicago, New York")
    with col_filter2:
        radius_km = st.slider("Radius (km)", min_value=10, max_value=500, value=100, step=10)
    
    # Parse user location
    user_lat, user_lon = None, None
    if user_location:
        # Geocoding: major US cities
        cities = {
            "seattle": (47.6062, -122.3321),
            "chicago": (41.8781, -87.6298),
            "new york": (40.7128, -74.0060),
            "los angeles": (34.0522, -118.2437),
            "miami": (25.7617, -80.1918),
            "austin": (30.2672, -97.7431),
            "san francisco": (37.7749, -122.4194),
            "boston": (42.3601, -71.0589),
            "dallas": (32.7767, -96.7970),
            "houston": (29.7604, -95.3698),
            "atlanta": (33.7490, -84.3880),
            "denver": (39.7392, -104.9903),
            "phoenix": (33.4484, -112.0740),
            "portland": (45.5152, -122.6784),
            "las vegas": (36.1699, -115.1398),
        }
        key = user_location.lower().strip()
        if key in cities:
            user_lat, user_lon = cities[key]
        else:
            st.info(f"City '{user_location}' not recognized. Try: Seattle, Chicago, New York, Los Angeles, Miami, Austin, San Francisco, Boston, Dallas, Houston, Atlanta, Denver, Phoenix, Portland, or Las Vegas.")
    
    # Filter outages by proximity if user location is set
    filtered_outages = outage_df.copy()
    if not filtered_outages.empty and user_lat is not None and user_lon is not None:
        if {"latitude", "longitude"}.issubset(filtered_outages.columns):
            # Haversine distance approximation
            def haversine_km(lat1, lon1, lat2, lon2):
                from math import radians, sin, cos, sqrt, atan2
                R = 6371.0  # Earth radius in km
                lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
                dlat = lat2 - lat1
                dlon = lon2 - lon1
                a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
                c = 2 * atan2(sqrt(a), sqrt(1-a))
                return R * c
            
            filtered_outages = filtered_outages.dropna(subset=["latitude", "longitude"])
            filtered_outages["distance_km"] = filtered_outages.apply(
                lambda row: haversine_km(user_lat, user_lon, row["latitude"], row["longitude"]), axis=1
            )
            filtered_outages = filtered_outages[filtered_outages["distance_km"] <= radius_km].sort_values("distance_km")
    
    if not filtered_outages.empty:
        st.metric("Outage Reports in Range", len(filtered_outages))
        
        # Global outage map
        if pdk is not None and {"latitude", "longitude"}.issubset(filtered_outages.columns):
            map_df = filtered_outages.dropna(subset=["latitude", "longitude"])
            if not map_df.empty:
                # Default center: median of outages or user location
                if user_lat and user_lon:
                    center_lat, center_lon = user_lat, user_lon
                    zoom = 7
                else:
                    center_lat = float(map_df["latitude"].median())
                    center_lon = float(map_df["longitude"].median())
                    zoom = 4
                
                # Outage markers (orange)
                map_df["color"] = [[255, 149, 0, 200]] * len(map_df)
                layers = [
                    pdk.Layer(
                        "ScatterplotLayer",
                        data=map_df,
                        get_position='[longitude, latitude]',
                        get_fill_color='color',
                        get_radius=200,
                        pickable=True,
                    )
                ]
                
                # User location marker (blue)
                if user_lat and user_lon:
                    user_marker = pd.DataFrame([{"latitude": user_lat, "longitude": user_lon, "color": [0, 122, 255, 255]}])
                    layers.append(
                        pdk.Layer(
                            "ScatterplotLayer",
                            data=user_marker,
                            get_position='[longitude, latitude]',
                            get_fill_color='color',
                            get_radius=300,
                            pickable=False,
                        )
                    )
                
                tooltip = {"html": "<b>Outage</b><br/>{text}<br/>{location}", "style": {"backgroundColor": "#222", "color": "white"}}
                deck = pdk.Deck(
                    layers=layers,
                    initial_view_state=pdk.ViewState(latitude=center_lat, longitude=center_lon, zoom=zoom, pitch=0),
                    tooltip=tooltip,
                    map_style="mapbox://styles/mapbox/dark-v10"
                )
                st.pydeck_chart(deck, use_container_width=True)
        
        # Outage table
        st.subheader("Outage Details")
        show_out_cols = [c for c in ["timestamp", "text", "location", "sentiment", "confidence", "distance_km"] if c in filtered_outages.columns]
        st.dataframe(filtered_outages[show_out_cols].head(50), use_container_width=True)
    else:
        st.info("Press 'Refresh Outages' to load outage reports.")

with tab_submit:
    st.header("Submit Your Review")
    st.markdown("Share your experience with T-Mobile service. Your feedback helps improve the network.")
    
    with st.form(key="review_form", clear_on_submit=True):
        review_text = st.text_area(
            "Your Review",
            placeholder="Describe your experience (e.g., 'Great coverage in downtown Seattle' or 'Dropped calls near Phoenix airport')",
            height=150,
            help="Be specific! Mention location keywords if you want auto-detection."
        )
        
        col1, col2 = st.columns(2)
        with col1:
            user_city = st.text_input(
                "City (Optional)",
                placeholder="e.g., Seattle, Austin, Miami",
                help="Leave blank to auto-detect from your review text."
            )
        with col2:
            # Placeholder for future enhancements (manual coords, etc.)
            st.empty()
        
        submit_button = st.form_submit_button("Submit Review", type="primary")
        
        if submit_button:
            if not review_text or len(review_text.strip()) < 5:
                st.error("Please write at least a few words in your review.")
            else:
                # Submit to API
                url = f"{API_BASE}/api/v1/feedback/submit"
                params = {"text": review_text.strip()}
                if user_city and user_city.strip():
                    # User provided city; backend will use it or auto-extract if missing coords
                    params["location"] = user_city.strip()

                try:
                    with httpx.Client(timeout=10.0) as client:
                        resp = client.post(url, params=params)
                        resp.raise_for_status()
                        created = resp.json()
                        st.success(f"✅ Review submitted! (ID: {created.get('id')})")
                        st.balloons()
                        # Refresh data to show new review
                        fetch_latest_data(limit=fetch_limit)
                except httpx.HTTPError as e:
                    st.error(f"Failed to submit review: {e}")
                except Exception as e:
                    st.error(f"Unexpected error: {e}")

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
    try:
        st.rerun()
    except Exception:
        st.experimental_rerun()