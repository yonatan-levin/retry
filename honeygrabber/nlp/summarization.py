"""
Text summarization module for honeygrabber.

This module provides the TextSummarizer class for summarizing text using various techniques.
"""

from typing import Dict, List, Optional, Any, Union, Set, Tuple
from collections import Counter
import re
import math

import spacy
from spacy.language import Language

from honeygrabber.nlp.processor import NLPProcessor
from honeygrabber.utils.logger import get_logger
from honeygrabber.utils.exceptions import NLPError

logger = get_logger(__name__)


class TextSummarizer:
    """
    Specialized class for text summarization.
    
    This class provides methods for summarizing text using various techniques
    such as extractive summarization, keyword-based summarization, and more.
    
    Attributes:
        nlp_processor: NLP processor instance
        default_ratio: Default ratio of sentences to include in the summary
        max_sentences: Maximum number of sentences to include in the summary
        use_transformers: Whether to use transformers for summarization
    """
    
    def __init__(self,
                 nlp_processor: Optional[NLPProcessor] = None,
                 default_ratio: float = 0.2,
                 max_sentences: int = 5,
                 use_transformers: bool = False):
        """
        Initialize a TextSummarizer.
        
        Args:
            nlp_processor: NLP processor instance to use
            default_ratio: Default ratio of sentences to include in the summary
            max_sentences: Maximum number of sentences to include in the summary
            use_transformers: Whether to use transformers for summarization
        """
        self.nlp_processor = nlp_processor or NLPProcessor()
        self.default_ratio = default_ratio
        self.max_sentences = max_sentences
        self.use_transformers = use_transformers
        
        logger.debug(f"Initialized TextSummarizer with default_ratio: {default_ratio}, max_sentences: {max_sentences}")
    
    def summarize(self, 
                  text: str, 
                  ratio: Optional[float] = None, 
                  max_sentences: Optional[int] = None,
                  method: str = "extractive") -> str:
        """
        Summarize text.
        
        Args:
            text: Text to summarize
            ratio: Ratio of sentences to include in the summary
            max_sentences: Maximum number of sentences to include in the summary
            method: Method to use for summarization
            
        Returns:
            Summarized text
            
        Raises:
            NLPError: If there is an error summarizing text
            ValueError: If an invalid method is specified
        """
        ratio = ratio or self.default_ratio
        max_sentences = max_sentences or self.max_sentences
        
        return self.summarize_with_method(text, method, ratio, max_sentences)
    
    def summarize_with_method(self, 
                             text: str, 
                             method: str, 
                             ratio: float, 
                             max_sentences: int) -> str:
        """
        Summarize text with a specific method.
        
        Args:
            text: Text to summarize
            method: Method to use for summarization
            ratio: Ratio of sentences to include in the summary
            max_sentences: Maximum number of sentences to include in the summary
            
        Returns:
            Summarized text
            
        Raises:
            NLPError: If there is an error summarizing text
            ValueError: If an invalid method is specified
        """
        methods = {
            "extractive": self.extractive_summarize,
            "keyword": self.keyword_summarize,
            "position": self.position_summarize,
        }
        
        if method not in methods:
            raise ValueError(f"Invalid method: {method}. Valid methods are: {', '.join(methods.keys())}")
        
        try:
            return methods[method](text, ratio, max_sentences)
        
        except Exception as e:
            if isinstance(e, ValueError):
                raise
            if isinstance(e, NLPError):
                raise
            error_msg = f"Error summarizing text with method '{method}': {str(e)}"
            logger.error(error_msg)
            raise NLPError("summarize_with_method", error_msg) from e
    
    def extractive_summarize(self, text: str, ratio: float, max_sentences: int) -> str:
        """
        Perform extractive summarization.
        
        Args:
            text: Text to summarize
            ratio: Ratio of sentences to include in the summary
            max_sentences: Maximum number of sentences to include in the summary
            
        Returns:
            Summarized text
            
        Raises:
            NLPError: If there is an error summarizing text
        """
        try:
            doc = self.nlp_processor.process_text(text)
            
            # Split text into sentences
            sentences = [sent.text.strip() for sent in doc.sents]
            
            if not sentences:
                return ""
            
            # Score sentences based on word frequencies
            scores = self._score_sentences(sentences)
            
            # Calculate the number of sentences to include
            num_sentences = min(max_sentences, int(len(sentences) * ratio))
            num_sentences = max(1, num_sentences)  # Ensure at least one sentence
            
            # Sort sentences by score and get the top ones
            ranked_sentences = sorted(((scores[i], i, s) for i, s in enumerate(sentences)), reverse=True)
            top_sentences = [s for _, i, s in ranked_sentences[:num_sentences]]
            
            # Sort sentences by their original order
            top_indices = [i for _, i, _ in ranked_sentences[:num_sentences]]
            summary_sentences = [sentences[i] for i in sorted(top_indices)]
            
            # Join the sentences
            summary = " ".join(summary_sentences)
            
            return summary
        
        except Exception as e:
            if isinstance(e, NLPError):
                raise
            error_msg = f"Error performing extractive summarization: {str(e)}"
            logger.error(error_msg)
            raise NLPError("extractive_summarize", error_msg) from e
    
    def keyword_summarize(self, text: str, ratio: float, max_sentences: int) -> str:
        """
        Perform keyword-based summarization.
        
        Args:
            text: Text to summarize
            ratio: Ratio of sentences to include in the summary
            max_sentences: Maximum number of sentences to include in the summary
            
        Returns:
            Summarized text
            
        Raises:
            NLPError: If there is an error summarizing text
        """
        try:
            doc = self.nlp_processor.process_text(text)
            
            # Split text into sentences
            sentences = [sent.text.strip() for sent in doc.sents]
            
            if not sentences:
                return ""
            
            # Extract keywords
            keywords = self._extract_keywords(text, 10)
            
            # Score sentences based on keyword presence
            scores = []
            for sentence in sentences:
                score = sum(1 for keyword in keywords if keyword.lower() in sentence.lower())
                scores.append(score)
            
            # Calculate the number of sentences to include
            num_sentences = min(max_sentences, int(len(sentences) * ratio))
            num_sentences = max(1, num_sentences)  # Ensure at least one sentence
            
            # Sort sentences by score and get the top ones
            ranked_sentences = sorted(((scores[i], i, s) for i, s in enumerate(sentences)), reverse=True)
            
            # Sort sentences by their original order
            top_indices = [i for _, i, _ in ranked_sentences[:num_sentences]]
            summary_sentences = [sentences[i] for i in sorted(top_indices)]
            
            # Join the sentences
            summary = " ".join(summary_sentences)
            
            return summary
        
        except Exception as e:
            if isinstance(e, NLPError):
                raise
            error_msg = f"Error performing keyword-based summarization: {str(e)}"
            logger.error(error_msg)
            raise NLPError("keyword_summarize", error_msg) from e
    
    def position_summarize(self, text: str, ratio: float, max_sentences: int) -> str:
        """
        Perform position-based summarization.
        
        Args:
            text: Text to summarize
            ratio: Ratio of sentences to include in the summary
            max_sentences: Maximum number of sentences to include in the summary
            
        Returns:
            Summarized text
            
        Raises:
            NLPError: If there is an error summarizing text
        """
        try:
            doc = self.nlp_processor.process_text(text)
            
            # Split text into sentences
            sentences = [sent.text.strip() for sent in doc.sents]
            
            if not sentences:
                return ""
            
            # Calculate the number of sentences to include
            num_sentences = min(max_sentences, int(len(sentences) * ratio))
            num_sentences = max(1, num_sentences)  # Ensure at least one sentence
            
            # Assign scores based on position
            # First sentences get higher scores
            scores = []
            for i in range(len(sentences)):
                # Give higher scores to sentences at the beginning and end
                if i < len(sentences) / 2:
                    # First half: score decreases from 1.0 to 0.5
                    score = 1.0 - 0.5 * (i / (len(sentences) / 2))
                else:
                    # Second half: score increases from 0.5 to 0.7
                    score = 0.5 + 0.2 * ((i - len(sentences) / 2) / (len(sentences) / 2))
                scores.append(score)
            
            # Sort sentences by score and get the top ones
            ranked_sentences = sorted(((scores[i], i, s) for i, s in enumerate(sentences)), reverse=True)
            
            # Sort sentences by their original order
            top_indices = [i for _, i, _ in ranked_sentences[:num_sentences]]
            summary_sentences = [sentences[i] for i in sorted(top_indices)]
            
            # Join the sentences
            summary = " ".join(summary_sentences)
            
            return summary
        
        except Exception as e:
            if isinstance(e, NLPError):
                raise
            error_msg = f"Error performing position-based summarization: {str(e)}"
            logger.error(error_msg)
            raise NLPError("position_summarize", error_msg) from e
    
    def _score_sentences(self, sentences: List[str]) -> List[float]:
        """
        Score sentences based on word frequencies.
        
        Args:
            sentences: List of sentences to score
            
        Returns:
            List of scores for each sentence
        """
        # Tokenize and count word frequencies
        all_words = []
        for sentence in sentences:
            words = re.findall(r'\w+', sentence.lower())
            all_words.extend(words)
        
        # Count word frequencies
        word_freq = Counter(all_words)
        
        # Calculate scores
        scores = []
        for sentence in sentences:
            words = re.findall(r'\w+', sentence.lower())
            if not words:
                scores.append(0)
                continue
            
            # Score is the sum of word frequencies divided by sentence length
            score = sum(word_freq[word] for word in words) / len(words)
            scores.append(score)
        
        return scores
    
    def _extract_keywords(self, text: str, top_n: int = 10) -> List[str]:
        """
        Extract keywords from text.
        
        Args:
            text: Text to extract keywords from
            top_n: Number of top keywords to return
            
        Returns:
            List of keywords
        """
        doc = self.nlp_processor.process_text(text)
        
        # Get filtered tokens
        filtered_tokens = [
            token.lemma_.lower()
            for token in doc
            if (token.pos_ in ["NOUN", "PROPN", "ADJ"]
                and not token.is_stop
                and not token.is_punct
                and len(token.text) > 2)
        ]
        
        # Count word frequencies
        word_freq = Counter(filtered_tokens)
        
        # Get top keywords
        keywords = [word for word, _ in word_freq.most_common(top_n)]
        
        return keywords
    
    def get_summary_statistics(self, original_text: str, summary: str) -> Dict[str, Any]:
        """
        Get statistics about the summary.
        
        Args:
            original_text: Original text
            summary: Summarized text
            
        Returns:
            Dictionary with summary statistics
            
        Raises:
            NLPError: If there is an error getting summary statistics
        """
        try:
            # Process texts
            original_doc = self.nlp_processor.process_text(original_text)
            summary_doc = self.nlp_processor.process_text(summary)
            
            # Count sentences
            original_sentences = list(original_doc.sents)
            summary_sentences = list(summary_doc.sents)
            
            # Count words
            original_words = [token.text for token in original_doc if not token.is_punct]
            summary_words = [token.text for token in summary_doc if not token.is_punct]
            
            # Calculate compression ratio
            if len(original_words) > 0:
                compression_ratio = len(summary_words) / len(original_words)
            else:
                compression_ratio = 0.0
            
            return {
                "original_sentences": len(original_sentences),
                "summary_sentences": len(summary_sentences),
                "original_words": len(original_words),
                "summary_words": len(summary_words),
                "compression_ratio": compression_ratio,
                "sentence_reduction": 1.0 - (len(summary_sentences) / max(1, len(original_sentences))),
                "word_reduction": 1.0 - (len(summary_words) / max(1, len(original_words))),
            }
        
        except Exception as e:
            if isinstance(e, NLPError):
                raise
            error_msg = f"Error getting summary statistics: {str(e)}"
            logger.error(error_msg)
            raise NLPError("get_summary_statistics", error_msg) from e 
