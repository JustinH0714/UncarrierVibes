from transformers import pipeline
from typing import Dict, Union
import numpy as np

class SentimentAnalyzer:
    def __init__(self, model_name: str = "distilbert-base-uncased-finetuned-sst-2-english"):
        self.sentiment_pipeline = pipeline("sentiment-analysis", model=model_name)
        
    def analyze(self, text: str) -> Dict[str, Union[str, float]]:
        """
        Analyze the sentiment of given text.
        
        Args:
            text (str): Input text for sentiment analysis
            
        Returns:
            Dict containing sentiment label and score
        """
        result = self.sentiment_pipeline(text)[0]
        
        return {
            "text": text,
            "sentiment": result["label"],
            "confidence": float(np.round(result["score"], 4)),
            "sentiment_score": float(np.round(
                result["score"] if result["label"] == "POSITIVE" else -result["score"],
                4
            ))
        }

    def batch_analyze(self, texts: list[str]) -> list[Dict[str, Union[str, float]]]:
        """
        Analyze sentiment for multiple texts in batch.
        
        Args:
            texts (list[str]): List of input texts
            
        Returns:
            List of dictionaries containing sentiment analysis results
        """
        results = self.sentiment_pipeline(texts)
        
        return [
            {
                "text": text,
                "sentiment": result["label"],
                "confidence": float(np.round(result["score"], 4)),
                "sentiment_score": float(np.round(
                    result["score"] if result["label"] == "POSITIVE" else -result["score"],
                    4
                ))
            }
            for text, result in zip(texts, results)
        ]