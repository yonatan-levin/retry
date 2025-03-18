"""
Main NLP processor module for retry.

This module provides the NLPProcessor class that orchestrates different
NLP tasks and manages NLP models.
"""

import os
from typing import Dict, List, Optional, Any, Union, Set

import spacy
from spacy.language import Language
from textblob import TextBlob

from retry.utils.logger import get_logger
from retry.utils.exceptions import NLPError, ConfigurationError

logger = get_logger(__name__)


class NLPProcessor:
    """
    Main NLP processor that orchestrates different NLP tasks.
    
    This class manages NLP models and provides methods for various NLP tasks
    such as named entity recognition, keyword extraction, sentiment analysis,
    and text summarization.
    
    Attributes:
        model_name: Name of the spaCy model to use
        nlp: Loaded spaCy model
        use_textblob: Whether to use TextBlob for certain tasks
        use_transformers: Whether to use transformers for certain tasks
    """
    
    # Default spaCy model
    DEFAULT_MODEL = "en_core_web_sm"
    
    # Available models
    AVAILABLE_MODELS = {
        "en_core_web_sm": "Small English model",
        "en_core_web_md": "Medium English model with word vectors",
        "en_core_web_lg": "Large English model with word vectors",
    }
    
    def __init__(self,
                 model_name: str = DEFAULT_MODEL,
                 use_textblob: bool = True,
                 use_transformers: bool = False,
                 load_model: bool = True):
        """
        Initialize an NLPProcessor.
        
        Args:
            model_name: Name of the spaCy model to use
            use_textblob: Whether to use TextBlob for certain tasks
            use_transformers: Whether to use transformers for certain tasks
            load_model: Whether to load the model immediately
        
        Raises:
            ConfigurationError: If the specified model is not available
        """
        self.model_name = model_name
        self.use_textblob = use_textblob
        self.use_transformers = use_transformers
        self.nlp: Optional[Language] = None
        
        # Dictionary to store additional models
        self._additional_models: Dict[str, Any] = {}
        
        if load_model:
            self.load_model()
        
        logger.debug(f"Initialized NLPProcessor with model: {model_name}")
    
    def load_model(self) -> None:
        """
        Load the spaCy model.
        
        Raises:
            ConfigurationError: If the model cannot be loaded
        """
        try:
            self.nlp = spacy.load(self.model_name)
            logger.debug(f"Loaded spaCy model: {self.model_name}")
        except OSError as e:
            error_msg = f"Could not load spaCy model '{self.model_name}'. "
            error_msg += f"Please install it with: python -m spacy download {self.model_name}"
            logger.error(error_msg)
            raise ConfigurationError(error_msg) from e
    
    def ensure_model_loaded(self) -> None:
        """
        Ensure that the spaCy model is loaded.
        
        Raises:
            ConfigurationError: If the model is not loaded
        """
        if self.nlp is None:
            self.load_model()
    
    def process_text(self, text: str) -> Any:
        """
        Process text with the spaCy model.
        
        Args:
            text: Text to process
            
        Returns:
            Processed spaCy Doc object
            
        Raises:
            NLPError: If there is an error processing the text
        """
        self.ensure_model_loaded()
        
        try:
            return self.nlp(text)
        except Exception as e:
            error_msg = f"Error processing text with spaCy: {str(e)}"
            logger.error(error_msg)
            raise NLPError("process_text", error_msg) from e
    
    def extract_entities(self,
                        text: str,
                        entity_types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Extract named entities from text.
        
        Args:
            text: Text to extract entities from
            entity_types: List of entity types to extract (e.g., ["PERSON", "ORG"])
            
        Returns:
            List of dictionaries with entity information
            
        Raises:
            NLPError: If there is an error extracting entities
        """
        try:
            doc = self.process_text(text)
            
            entities = []
            for ent in doc.ents:
                if entity_types is None or ent.label_ in entity_types:
                    entities.append({
                        "text": ent.text,
                        "label": ent.label_,
                        "start": ent.start_char,
                        "end": ent.end_char,
                    })
            
            return entities
        
        except Exception as e:
            if isinstance(e, NLPError):
                raise
            error_msg = f"Error extracting entities: {str(e)}"
            logger.error(error_msg)
            raise NLPError("extract_entities", error_msg) from e
    
    def extract_keywords(self,
                        text: str,
                        pos_tags: Optional[List[str]] = None,
                        top_n: int = 10) -> List[Dict[str, Any]]:
        """
        Extract keywords from text.
        
        Args:
            text: Text to extract keywords from
            pos_tags: List of part-of-speech tags to include (e.g., ["NOUN", "ADJ"])
            top_n: Number of top keywords to return
            
        Returns:
            List of dictionaries with keyword information
            
        Raises:
            NLPError: If there is an error extracting keywords
        """
        try:
            doc = self.process_text(text)
            
            # Default to nouns and proper nouns if no POS tags are specified
            if pos_tags is None:
                pos_tags = ["NOUN", "PROPN"]
            
            # Extract tokens with the specified POS tags
            keywords = []
            for token in doc:
                if token.pos_ in pos_tags and not token.is_stop and not token.is_punct:
                    keywords.append({
                        "text": token.text,
                        "lemma": token.lemma_,
                        "pos": token.pos_,
                        "score": token.prob,  # Log probability
                    })
            
            # Sort by score (higher is better) and take top_n
            keywords.sort(key=lambda x: x["score"], reverse=True)
            return keywords[:top_n]
        
        except Exception as e:
            if isinstance(e, NLPError):
                raise
            error_msg = f"Error extracting keywords: {str(e)}"
            logger.error(error_msg)
            raise NLPError("extract_keywords", error_msg) from e
    
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
            if self.use_textblob:
                # Use TextBlob for sentiment analysis
                blob = TextBlob(text)
                sentiment = blob.sentiment
                
                return {
                    "polarity": sentiment.polarity,  # -1.0 to 1.0
                    "subjectivity": sentiment.subjectivity,  # 0.0 to 1.0
                    "assessment": "positive" if sentiment.polarity > 0 else "negative" if sentiment.polarity < 0 else "neutral",
                }
            else:
                # Use spaCy for basic sentiment analysis
                doc = self.process_text(text)
                
                # Simple heuristic based on positive and negative words
                positive_words = sum(1 for token in doc if token.sentiment > 0)
                negative_words = sum(1 for token in doc if token.sentiment < 0)
                
                polarity = (positive_words - negative_words) / max(1, len(doc))
                
                return {
                    "polarity": polarity,
                    "positive_words": positive_words,
                    "negative_words": negative_words,
                    "assessment": "positive" if polarity > 0 else "negative" if polarity < 0 else "neutral",
                }
        
        except Exception as e:
            if isinstance(e, NLPError):
                raise
            error_msg = f"Error analyzing sentiment: {str(e)}"
            logger.error(error_msg)
            raise NLPError("analyze_sentiment", error_msg) from e
    
    def summarize_text(self, text: str, ratio: float = 0.2, max_sentences: int = 5) -> str:
        """
        Summarize text.
        
        Args:
            text: Text to summarize
            ratio: Ratio of sentences to include in the summary
            max_sentences: Maximum number of sentences to include
            
        Returns:
            Summarized text
            
        Raises:
            NLPError: If there is an error summarizing text
        """
        try:
            doc = self.process_text(text)
            
            # Split text into sentences
            sentences = [sent.text.strip() for sent in doc.sents]
            
            # Create a simple summary by taking the first few sentences
            # In a real implementation, we would use a more sophisticated algorithm
            num_sentences = min(max_sentences, int(len(sentences) * ratio))
            
            # A very simple summarization approach: take the first few sentences
            summary = " ".join(sentences[:num_sentences])
            
            return summary
        
        except Exception as e:
            if isinstance(e, NLPError):
                raise
            error_msg = f"Error summarizing text: {str(e)}"
            logger.error(error_msg)
            raise NLPError("summarize_text", error_msg) from e
    
    def match_patterns(self, text: str, patterns: List[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        Match patterns in text using spaCy's matcher.
        
        Args:
            text: Text to match patterns in
            patterns: List of patterns to match
            
        Returns:
            List of dictionaries with match information
            
        Raises:
            NLPError: If there is an error matching patterns
        """
        try:
            self.ensure_model_loaded()
            
            from spacy.matcher import Matcher
            matcher = Matcher(self.nlp.vocab)
            
            # Add patterns
            for i, pattern in enumerate(patterns):
                matcher.add(f"pattern_{i}", [pattern])
            
            # Process text and find matches
            doc = self.process_text(text)
            matches = matcher(doc)
            
            # Prepare results
            results = []
            for match_id, start, end in matches:
                span = doc[start:end]
                results.append({
                    "pattern_id": matcher.vocab.strings[match_id],
                    "start": span.start_char,
                    "end": span.end_char,
                    "text": span.text,
                })
            
            return results
        
        except Exception as e:
            if isinstance(e, NLPError):
                raise
            error_msg = f"Error matching patterns: {str(e)}"
            logger.error(error_msg)
            raise NLPError("match_patterns", error_msg) from e
    
    @staticmethod
    def list_available_models() -> Dict[str, str]:
        """
        List available spaCy models.
        
        Returns:
            Dictionary of available models
        """
        return NLPProcessor.AVAILABLE_MODELS
    
    @staticmethod
    def is_model_installed(model_name: str) -> bool:
        """
        Check if a spaCy model is installed.
        
        Args:
            model_name: Name of the model to check
            
        Returns:
            True if the model is installed, False otherwise
        """
        try:
            spacy.load(model_name)
            return True
        except OSError:
            return False 