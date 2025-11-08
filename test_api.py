#!/usr/bin/env python3
"""
Test script for UncarrierVibes API
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_root():
    """Test the root endpoint"""
    response = requests.get(f"{BASE_URL}/")
    print(f"✓ Root endpoint: {response.json()}")

def test_submit_feedback():
    """Test submitting feedback"""
    feedback_examples = [
        "T-Mobile has amazing 5G coverage!",
        "The customer service was terrible today.",
        "I love my new phone plan!",
        "My internet keeps dropping, very frustrating.",
        "Best mobile carrier I've ever had!"
    ]
    
    print("\n📝 Submitting feedback...")
    for text in feedback_examples:
        response = requests.post(f"{BASE_URL}/api/v1/feedback/submit", params={"text": text})
        if response.status_code == 200:
            data = response.json()
            print(f"  • '{text[:40]}...' → {data['sentiment']} ({data['confidence']:.2f})")
        else:
            print(f"  ✗ Error submitting: {text}")

def test_get_stats():
    """Test getting feedback statistics"""
    response = requests.get(f"{BASE_URL}/api/v1/feedback/stats")
    print(f"\n📊 Feedback Statistics:")
    stats = response.json()
    print(f"  • Total feedback: {stats['total']}")
    print(f"  • Positive: {stats['positive']}")
    print(f"  • Negative: {stats['negative']}")
    print(f"  • Positive percentage: {stats['positive_percentage']:.1f}%")

def test_metrics_summary():
    """Test metrics summary"""
    response = requests.get(f"{BASE_URL}/api/v1/metrics/summary")
    print(f"\n📈 Metrics Summary:")
    metrics = response.json()
    print(f"  • Total feedback: {metrics['total_feedback']}")
    print(f"  • Average sentiment: {metrics['average_sentiment']:.2f}")
    print(f"  • Positive percentage: {metrics['positive_percentage']:.1f}%")

if __name__ == "__main__":
    print("🚀 Testing UncarrierVibes API\n")
    print("=" * 50)
    
    try:
        test_root()
        test_submit_feedback()
        test_get_stats()
        test_metrics_summary()
        print("\n" + "=" * 50)
        print("✅ All tests completed successfully!")
        print(f"\n🌐 Visit http://localhost:8000/docs for API documentation")
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to the API server.")
        print("   Make sure the server is running with:")
        print("   uvicorn src.api.main:app --reload")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")