"""
Keyword extraction module for honeygrabber.

This module provides the KeywordExtractor class for extracting keywords from text.
"""

from typing import Dict, List, Optional, Any, Union, Set, Tuple
from collections import Counter

import math
import re

from honeygrabber.nlp.processor import NLPProcessor
from honeygrabber.utils.logger import get_logger
from honeygrabber.utils.exceptions import NLPError

logger = get_logger(__name__)


class KeywordExtractor:
    """
    Specialized class for keyword extraction.
    
    This class provides methods for extracting keywords from text
    using various approaches such as TF-IDF, POS tagging, and TextRank.
    
    Attributes:
        nlp_processor: NLP processor instance
        pos_tags: List of part-of-speech tags to include
        stop_words: Set of stop words to exclude
        min_word_length: Minimum word length to include
    """
    
    def __init__(self,
                 nlp_processor: Optional[NLPProcessor] = None,
                 pos_tags: Optional[List[str]] = None,
                 stop_words: Optional[Set[str]] = None,
                 min_word_length: int = 3):
        """
        Initialize a KeywordExtractor.
        
        Args:
            nlp_processor: NLP processor instance to use
            pos_tags: List of part-of-speech tags to include
            stop_words: Additional stop words to exclude
            min_word_length: Minimum word length to include
        """
        self.nlp_processor = nlp_processor or NLPProcessor()
        
        # Default to nouns, proper nouns, and adjectives if no POS tags are specified
        self.pos_tags = pos_tags or ["NOUN", "PROPN", "ADJ"]
        
        # Get default stop words from spaCy
        self.nlp_processor.ensure_model_loaded()
        self.stop_words = set(self.nlp_processor.nlp.Defaults.stop_words)
        
        # Add user-specified stop words
        if stop_words:
            self.stop_words.update(stop_words)
        
        self.min_word_length = min_word_length
        
        logger.debug(f"Initialized KeywordExtractor with POS tags: {self.pos_tags}")
    
    def extract_keywords(self, text: str, top_n: int = 10, method: str = "default") -> List[Dict[str, Any]]:
        """
        Extract keywords from text.
        
        Args:
            text: Text to extract keywords from
            top_n: Number of top keywords to return
            method: Method to use for extraction (default, tfidf, textrank)
            
        Returns:
            List of dictionaries with keyword information
            
        Raises:
            NLPError: If there is an error extracting keywords
            ValueError: If an invalid method is specified
        """
        methods = {
            "default": self._extract_keywords_default,
            "tfidf": self._extract_keywords_tfidf,
            "textrank": self._extract_keywords_textrank,
        }
        
        if method not in methods:
            raise ValueError(f"Invalid method: {method}. Valid methods are: {', '.join(methods.keys())}")
        
        try:
            return methods[method](text, top_n)
        
        except Exception as e:
            if isinstance(e, ValueError):
                raise
            if isinstance(e, NLPError):
                raise
            error_msg = f"Error extracting keywords with method '{method}': {str(e)}"
            logger.error(error_msg)
            raise NLPError("extract_keywords", error_msg) from e
    
    def _extract_keywords_default(self, text: str, top_n: int = 10) -> List[Dict[str, Any]]:
        """
        Extract keywords using the default approach (frequency + POS filtering).
        
        Args:
            text: Text to extract keywords from
            top_n: Number of top keywords to return
            
        Returns:
            List of dictionaries with keyword information
        """
        doc = self.nlp_processor.process_text(text)
        
        # Extract tokens with the specified POS tags
        keyword_tokens = [
            token for token in doc
            if token.pos_ in self.pos_tags
            and not token.is_stop
            and not token.is_punct
            and len(token.text) >= self.min_word_length
            and token.text.lower() not in self.stop_words
        ]
        
        # Count occurrences of each lemmatized token
        keywords = {}
        for token in keyword_tokens:
            lemma = token.lemma_.lower()
            if lemma not in keywords:
                keywords[lemma] = {
                    "text": token.text,
                    "lemma": lemma,
                    "pos": token.pos_,
                    "count": 0,
                    "score": token.prob,  # Log probability from spaCy
                }
            keywords[lemma]["count"] += 1
        
        # Create a list of keywords and compute a simple score
        keyword_list = list(keywords.values())
        for keyword in keyword_list:
            # Simple scoring: combine frequency with log probability
            keyword["score"] = keyword["count"] * (1.0 - abs(keyword["score"]))
        
        # Sort by score (higher is better) and take top_n
        keyword_list.sort(key=lambda x: x["score"], reverse=True)
        return keyword_list[:top_n]
    
    def _extract_keywords_tfidf(self, text: str, top_n: int = 10) -> List[Dict[str, Any]]:
        """
        Extract keywords using a simplified TF-IDF approach.
        
        Args:
            text: Text to extract keywords from
            top_n: Number of top keywords to return
            
        Returns:
            List of dictionaries with keyword information
        """
        doc = self.nlp_processor.process_text(text)
        
        # Split text into sentences
        sentences = [sent.text for sent in doc.sents]
        
        # Get filtered tokens
        filtered_tokens = [
            token.lemma_.lower()
            for token in doc
            if token.pos_ in self.pos_tags
            and not token.is_stop
            and not token.is_punct
            and len(token.text) >= self.min_word_length
            and token.text.lower() not in self.stop_words
        ]
        
        # Term Frequency (TF)
        tf = Counter(filtered_tokens)
        
        # Inverse Document Frequency (IDF)
        idf = {}
        n_sentences = len(sentences)
        for token in set(filtered_tokens):
            # Count sentences containing the token
            df = sum(1 for sent in sentences if token in sent.lower())
            idf[token] = math.log(n_sentences / (1 + df))
        
        # Compute TF-IDF score
        tfidf = {token: freq * idf.get(token, 0) for token, freq in tf.items()}
        
        # Create keyword dictionaries
        keywords = []
        for token, score in tfidf.items():
            # Find the original form in the document
            original_form = next((t.text for t in doc if t.lemma_.lower() == token), token)
            pos = next((t.pos_ for t in doc if t.lemma_.lower() == token), "")
            
            keywords.append({
                "text": original_form,
                "lemma": token,
                "pos": pos,
                "count": tf[token],
                "score": score,
            })
        
        # Sort by score (higher is better) and take top_n
        keywords.sort(key=lambda x: x["score"], reverse=True)
        return keywords[:top_n]
    
    def _extract_keywords_textrank(self, text: str, top_n: int = 10) -> List[Dict[str, Any]]:
        """
        Extract keywords using a simplified TextRank approach.
        
        Args:
            text: Text to extract keywords from
            top_n: Number of top keywords to return
            
        Returns:
            List of dictionaries with keyword information
        """
        doc = self.nlp_processor.process_text(text)
        
        # Get filtered tokens
        filtered_tokens = [
            token
            for token in doc
            if token.pos_ in self.pos_tags
            and not token.is_stop
            and not token.is_punct
            and len(token.text) >= self.min_word_length
            and token.text.lower() not in self.stop_words
        ]
        
        # Create a simple co-occurrence graph
        # Two tokens co-occur if they are within a window of 2 tokens
        window_size = 2
        graph = {}
        
        for i, token in enumerate(filtered_tokens):
            if token.lemma_.lower() not in graph:
                graph[token.lemma_.lower()] = {}
            
            # Look at tokens within the window
            start = max(0, i - window_size)
            end = min(len(filtered_tokens), i + window_size + 1)
            
            for j in range(start, end):
                if i != j:
                    other_token = filtered_tokens[j]
                    other_lemma = other_token.lemma_.lower()
                    
                    if other_lemma not in graph:
                        graph[other_lemma] = {}
                    
                    # Increase co-occurrence count
                    graph[token.lemma_.lower()][other_lemma] = graph[token.lemma_.lower()].get(other_lemma, 0) + 1
                    graph[other_lemma][token.lemma_.lower()] = graph[other_lemma].get(token.lemma_.lower(), 0) + 1
        
        # Simplified PageRank algorithm
        damping = 0.85
        min_diff = 0.0001
        iterations = 30
        
        # Initialize scores
        scores = {token: 1.0 for token in graph}
        
        # Run iterations
        for _ in range(iterations):
            prev_scores = scores.copy()
            
            # Update scores
            for token in graph:
                score = 1 - damping
                
                # Add contributions from neighbors
                for neighbor, weight in graph[token].items():
                    score += damping * (prev_scores[neighbor] * weight / sum(graph[neighbor].values()))
                
                scores[token] = score
            
            # Check for convergence
            diff = sum(abs(scores[token] - prev_scores[token]) for token in graph)
            if diff < min_diff:
                break
        
        # Create keyword dictionaries
        keywords = []
        for token, score in scores.items():
            # Find the original form in the document
            original_form = next((t.text for t in doc if t.lemma_.lower() == token), token)
            pos = next((t.pos_ for t in doc if t.lemma_.lower() == token), "")
            count = sum(1 for t in filtered_tokens if t.lemma_.lower() == token)
            
            keywords.append({
                "text": original_form,
                "lemma": token,
                "pos": pos,
                "count": count,
                "score": score,
            })
        
        # Sort by score (higher is better) and take top_n
        keywords.sort(key=lambda x: x["score"], reverse=True)
        return keywords[:top_n]
    
    def extract_keyphrases(self, text: str, top_n: int = 5) -> List[Dict[str, Any]]:
        """
        Extract keyphrases from text.
        
        Args:
            text: Text to extract keyphrases from
            top_n: Number of top keyphrases to return
            
        Returns:
            List of dictionaries with keyphrase information
            
        Raises:
            NLPError: If there is an error extracting keyphrases
        """
        try:
            doc = self.nlp_processor.process_text(text)
            
            # Extract noun chunks as potential keyphrases
            keyphrases = []
            for chunk in doc.noun_chunks:
                # Filter out chunks with stop words at the beginning
                if chunk[0].is_stop:
                    continue
                
                # Filter out short chunks
                if len(chunk.text) < self.min_word_length:
                    continue
                
                # Check if chunk has at least one token with desired POS tag
                if any(token.pos_ in self.pos_tags for token in chunk):
                    keyphrases.append({
                        "text": chunk.text,
                        "root": chunk.root.text,
                        "root_pos": chunk.root.pos_,
                        "count": 1,  # Will be updated below
                        "score": chunk.root.prob,  # Initial score
                    })
            
            # Count occurrences of identical phrases
            keyphrase_dict = {}
            for kp in keyphrases:
                text = kp["text"].lower()
                if text not in keyphrase_dict:
                    keyphrase_dict[text] = kp
                else:
                    keyphrase_dict[text]["count"] += 1
            
            # Convert back to list and update scores
            keyphrases = list(keyphrase_dict.values())
            for kp in keyphrases:
                # Update score to factor in frequency
                kp["score"] = kp["count"] * (1.0 - abs(kp["score"]))
            
            # Sort by score (higher is better) and take top_n
            keyphrases.sort(key=lambda x: x["score"], reverse=True)
            return keyphrases[:top_n]
        
        except Exception as e:
            if isinstance(e, NLPError):
                raise
            error_msg = f"Error extracting keyphrases: {str(e)}"
            logger.error(error_msg)
            raise NLPError("extract_keyphrases", error_msg) from e
    
    def add_stop_words(self, words: List[str]) -> None:
        """
        Add additional stop words.
        
        Args:
            words: List of words to add to stop words
        """
        self.stop_words.update(word.lower() for word in words)
        logger.debug(f"Added {len(words)} stop words")
    
    def remove_stop_words(self, words: List[str]) -> None:
        """
        Remove words from stop words.
        
        Args:
            words: List of words to remove from stop words
        """
        for word in words:
            if word.lower() in self.stop_words:
                self.stop_words.remove(word.lower())
        logger.debug(f"Removed {len(words)} stop words")
    
    def reset_stop_words(self) -> None:
        """
        Reset stop words to default.
        """
        self.nlp_processor.ensure_model_loaded()
        self.stop_words = set(self.nlp_processor.nlp.Defaults.stop_words)
        logger.debug("Reset stop words to default")
    
    def get_keyword_density(self, text: str) -> Dict[str, float]:
        """
        Calculate keyword density for a given text.
        
        Args:
            text: Text to calculate keyword density for
            
        Returns:
            Dictionary with keyword densities (percentage of total words)
            
        Raises:
            NLPError: If there is an error calculating keyword density
        """
        try:
            doc = self.nlp_processor.process_text(text)
            
            # Count total tokens excluding punctuation
            total_tokens = sum(1 for token in doc if not token.is_punct)
            
            if total_tokens == 0:
                return {}
            
            # Extract and count keywords
            keywords = [
                token.lemma_.lower()
                for token in doc
                if token.pos_ in self.pos_tags
                and not token.is_stop
                and not token.is_punct
                and len(token.text) >= self.min_word_length
                and token.text.lower() not in self.stop_words
            ]
            
            # Calculate density
            keyword_counts = Counter(keywords)
            keyword_density = {
                keyword: count / total_tokens * 100  # As percentage
                for keyword, count in keyword_counts.items()
            }
            
            return keyword_density
        
        except Exception as e:
            if isinstance(e, NLPError):
                raise
            error_msg = f"Error calculating keyword density: {str(e)}"
            logger.error(error_msg)
            raise NLPError("get_keyword_density", error_msg) from e 
