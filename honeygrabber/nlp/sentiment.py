"""
Sentiment analysis module for honeygrabber.

This module provides the SentimentAnalyzer class for analyzing sentiment in text.
"""

from typing import Dict, List, Optional, Any, Union, Set
import statistics
from textblob import TextBlob

from honeygrabber.nlp.processor import NLPProcessor
from honeygrabber.utils.logger import get_logger
from honeygrabber.utils.exceptions import NLPError

logger = get_logger(__name__)


class SentimentAnalyzer:
    """
    Specialized class for sentiment analysis.
    
    This class provides methods for analyzing sentiment in text,
    including polarity, subjectivity, and emotional content.
    
    Attributes:
        nlp_processor: NLP processor instance
        use_textblob: Whether to use TextBlob for sentiment analysis
        use_transformers: Whether to use transformers for sentiment analysis
    """
    
    def __init__(self,
                 nlp_processor: Optional[NLPProcessor] = None,
                 use_textblob: bool = True,
                 use_transformers: bool = False):
        """
        Initialize a SentimentAnalyzer.
        
        Args:
            nlp_processor: NLP processor instance to use
            use_textblob: Whether to use TextBlob for sentiment analysis
            use_transformers: Whether to use transformers for sentiment analysis
        """
        self.nlp_processor = nlp_processor or NLPProcessor()
        self.use_textblob = use_textblob
        self.use_transformers = use_transformers
        
        logger.debug(f"Initialized SentimentAnalyzer with TextBlob: {use_textblob}, Transformers: {use_transformers}")
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of text.
        
        Args:
            text: Text to analyze sentiment of
            
        Returns:
            Dictionary with sentiment information
            
        Raises:
            NLPError: If there is an error analyzing sentiment
        """
        try:
            if not text or not text.strip():
                return {
                    "polarity": 0.0,
                    "subjectivity": 0.0,
                    "assessment": "neutral",
                    "confidence": 0.0,
                }
            
            if self.use_textblob:
                return self._analyze_with_textblob(text)
            elif self.use_transformers:
                return self._analyze_with_transformers(text)
            else:
                return self._analyze_with_spacy(text)
        
        except Exception as e:
            if isinstance(e, NLPError):
                raise
            error_msg = f"Error analyzing sentiment: {str(e)}"
            logger.error(error_msg)
            raise NLPError("analyze_sentiment", error_msg) from e
    
    def _analyze_with_textblob(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment using TextBlob.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with sentiment information
        """
        blob = TextBlob(text)
        sentiment = blob.sentiment
        
        # Determine assessment
        if sentiment.polarity > 0.1:
            assessment = "positive"
        elif sentiment.polarity < -0.1:
            assessment = "negative"
        else:
            assessment = "neutral"
        
        # Calculate confidence based on polarity and subjectivity
        confidence = abs(sentiment.polarity) * sentiment.subjectivity
        
        return {
            "polarity": sentiment.polarity,  # -1.0 to 1.0
            "subjectivity": sentiment.subjectivity,  # 0.0 to 1.0
            "assessment": assessment,
            "confidence": confidence,
        }
    
    def _analyze_with_transformers(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment using transformers (placeholder).
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with sentiment information
            
        Note:
            This is a placeholder for transformer-based analysis.
            In a real implementation, this would use a pre-trained transformer model.
        """
        # Placeholder for transformer-based analysis
        # In a real implementation, this would use a pre-trained transformer model
        logger.warning("Transformer-based sentiment analysis is not implemented")
        
        # Fall back to TextBlob
        return self._analyze_with_textblob(text)
    
    def _analyze_with_spacy(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment using spaCy.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with sentiment information
        """
        doc = self.nlp_processor.process_text(text)
        
        # Simple heuristic based on positive and negative words
        positive_words = sum(1 for token in doc if token.sentiment > 0)
        negative_words = sum(1 for token in doc if token.sentiment < 0)
        total_words = sum(1 for token in doc if not token.is_punct)
        
        if total_words == 0:
            return {
                "polarity": 0.0,
                "subjectivity": 0.0,
                "assessment": "neutral",
                "confidence": 0.0,
            }
        
        # Calculate polarity as a ratio
        polarity = (positive_words - negative_words) / total_words
        
        # Calculate subjectivity as a ratio of opinionated words
        subjectivity = (positive_words + negative_words) / total_words
        
        # Determine assessment
        if polarity > 0.1:
            assessment = "positive"
        elif polarity < -0.1:
            assessment = "negative"
        else:
            assessment = "neutral"
        
        # Calculate confidence based on polarity and subjectivity
        confidence = abs(polarity) * subjectivity
        
        return {
            "polarity": polarity,
            "subjectivity": subjectivity,
            "assessment": assessment,
            "confidence": confidence,
            "positive_words": positive_words,
            "negative_words": negative_words,
        }
    
    def get_polarity(self, text: str) -> float:
        """
        Get polarity of text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Polarity score (-1.0 to 1.0)
            
        Raises:
            NLPError: If there is an error analyzing sentiment
        """
        try:
            sentiment = self.analyze_sentiment(text)
            return sentiment["polarity"]
        
        except Exception as e:
            if isinstance(e, NLPError):
                raise
            error_msg = f"Error getting polarity: {str(e)}"
            logger.error(error_msg)
            raise NLPError("get_polarity", error_msg) from e
    
    def get_subjectivity(self, text: str) -> float:
        """
        Get subjectivity of text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Subjectivity score (0.0 to 1.0)
            
        Raises:
            NLPError: If there is an error analyzing sentiment
        """
        try:
            sentiment = self.analyze_sentiment(text)
            return sentiment["subjectivity"]
        
        except Exception as e:
            if isinstance(e, NLPError):
                raise
            error_msg = f"Error getting subjectivity: {str(e)}"
            logger.error(error_msg)
            raise NLPError("get_subjectivity", error_msg) from e
    
    def is_positive(self, text: str, threshold: float = 0.1) -> bool:
        """
        Check if text is positive.
        
        Args:
            text: Text to analyze
            threshold: Polarity threshold for positivity
            
        Returns:
            True if text is positive, False otherwise
            
        Raises:
            NLPError: If there is an error analyzing sentiment
        """
        try:
            polarity = self.get_polarity(text)
            return polarity > threshold
        
        except Exception as e:
            if isinstance(e, NLPError):
                raise
            error_msg = f"Error checking if text is positive: {str(e)}"
            logger.error(error_msg)
            raise NLPError("is_positive", error_msg) from e
    
    def is_negative(self, text: str, threshold: float = -0.1) -> bool:
        """
        Check if text is negative.
        
        Args:
            text: Text to analyze
            threshold: Polarity threshold for negativity
            
        Returns:
            True if text is negative, False otherwise
            
        Raises:
            NLPError: If there is an error analyzing sentiment
        """
        try:
            polarity = self.get_polarity(text)
            return polarity < threshold
        
        except Exception as e:
            if isinstance(e, NLPError):
                raise
            error_msg = f"Error checking if text is negative: {str(e)}"
            logger.error(error_msg)
            raise NLPError("is_negative", error_msg) from e
    
    def is_neutral(self, text: str, threshold: float = 0.1) -> bool:
        """
        Check if text is neutral.
        
        Args:
            text: Text to analyze
            threshold: Polarity threshold for neutrality
            
        Returns:
            True if text is neutral, False otherwise
            
        Raises:
            NLPError: If there is an error analyzing sentiment
        """
        try:
            polarity = self.get_polarity(text)
            return abs(polarity) <= threshold
        
        except Exception as e:
            if isinstance(e, NLPError):
                raise
            error_msg = f"Error checking if text is neutral: {str(e)}"
            logger.error(error_msg)
            raise NLPError("is_neutral", error_msg) from e
    
    def is_subjective(self, text: str, threshold: float = 0.5) -> bool:
        """
        Check if text is subjective.
        
        Args:
            text: Text to analyze
            threshold: Subjectivity threshold
            
        Returns:
            True if text is subjective, False otherwise
            
        Raises:
            NLPError: If there is an error analyzing sentiment
        """
        try:
            subjectivity = self.get_subjectivity(text)
            return subjectivity >= threshold
        
        except Exception as e:
            if isinstance(e, NLPError):
                raise
            error_msg = f"Error checking if text is subjective: {str(e)}"
            logger.error(error_msg)
            raise NLPError("is_subjective", error_msg) from e
    
    def is_objective(self, text: str, threshold: float = 0.5) -> bool:
        """
        Check if text is objective.
        
        Args:
            text: Text to analyze
            threshold: Subjectivity threshold
            
        Returns:
            True if text is objective, False otherwise
            
        Raises:
            NLPError: If there is an error analyzing sentiment
        """
        try:
            subjectivity = self.get_subjectivity(text)
            return subjectivity < threshold
        
        except Exception as e:
            if isinstance(e, NLPError):
                raise
            error_msg = f"Error checking if text is objective: {str(e)}"
            logger.error(error_msg)
            raise NLPError("is_objective", error_msg) from e
    
    def analyze_sentence_sentiments(self, text: str) -> List[Dict[str, Any]]:
        """
        Analyze sentiments of individual sentences.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of dictionaries with sentiment information for each sentence
            
        Raises:
            NLPError: If there is an error analyzing sentiment
        """
        try:
            doc = self.nlp_processor.process_text(text)
            
            sentence_sentiments = []
            for sent in doc.sents:
                sentiment = self.analyze_sentiment(sent.text)
                sentiment["sentence"] = sent.text
                sentiment["start"] = sent.start_char
                sentiment["end"] = sent.end_char
                sentence_sentiments.append(sentiment)
            
            return sentence_sentiments
        
        except Exception as e:
            if isinstance(e, NLPError):
                raise
            error_msg = f"Error analyzing sentence sentiments: {str(e)}"
            logger.error(error_msg)
            raise NLPError("analyze_sentence_sentiments", error_msg) from e
    
    def analyze_sentiment_distribution(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment distribution across sentences.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with sentiment distribution information
            
        Raises:
            NLPError: If there is an error analyzing sentiment distribution
        """
        try:
            sentence_sentiments = self.analyze_sentence_sentiments(text)
            
            if not sentence_sentiments:
                return {
                    "overall": "neutral",
                    "distribution": {
                        "positive": 0,
                        "negative": 0,
                        "neutral": 0,
                    },
                    "avg_polarity": 0.0,
                    "avg_subjectivity": 0.0,
                    "polarity_std": 0.0,
                    "subjectivity_std": 0.0,
                }
            
            # Count sentiments by category
            distribution = {
                "positive": sum(1 for sent in sentence_sentiments if sent["assessment"] == "positive"),
                "negative": sum(1 for sent in sentence_sentiments if sent["assessment"] == "negative"),
                "neutral": sum(1 for sent in sentence_sentiments if sent["assessment"] == "neutral"),
            }
            
            # Calculate overall sentiment
            if distribution["positive"] > distribution["negative"] and distribution["positive"] > distribution["neutral"]:
                overall = "positive"
            elif distribution["negative"] > distribution["positive"] and distribution["negative"] > distribution["neutral"]:
                overall = "negative"
            else:
                overall = "neutral"
            
            # Calculate statistics
            polarities = [sent["polarity"] for sent in sentence_sentiments]
            subjectivities = [sent["subjectivity"] for sent in sentence_sentiments]
            
            return {
                "overall": overall,
                "distribution": distribution,
                "avg_polarity": statistics.mean(polarities),
                "avg_subjectivity": statistics.mean(subjectivities),
                "polarity_std": statistics.stdev(polarities) if len(polarities) > 1 else 0.0,
                "subjectivity_std": statistics.stdev(subjectivities) if len(subjectivities) > 1 else 0.0,
            }
        
        except Exception as e:
            if isinstance(e, NLPError):
                raise
            error_msg = f"Error analyzing sentiment distribution: {str(e)}"
            logger.error(error_msg)
            raise NLPError("analyze_sentiment_distribution", error_msg) from e 
