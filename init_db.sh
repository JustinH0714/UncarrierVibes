#!/bin/bash

# Create database
createdb uncarrier_vibes

# Initialize schema
psql uncarrier_vibes << EOF
CREATE TABLE IF NOT EXISTS feedback (
    id SERIAL PRIMARY KEY,
    text TEXT NOT NULL,
    sentiment VARCHAR(10) NOT NULL,
    confidence FLOAT NOT NULL,
    sentiment_score FLOAT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_feedback_timestamp ON feedback(timestamp);
CREATE INDEX IF NOT EXISTS idx_feedback_sentiment ON feedback(sentiment);
EOF

echo "Database initialized successfully!"