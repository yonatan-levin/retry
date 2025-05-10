"""
Natural Language Processing (NLP) modules for honeygrabber.

This package provides NLP capabilities for the retry library,
including named entity recognition, keyword extraction, sentiment analysis,
and text summarization.
"""

from honeygrabber.nlp.processor import NLPProcessor
from honeygrabber.nlp.entities import EntityExtractor
from honeygrabber.nlp.keywords import KeywordExtractor
from honeygrabber.nlp.sentiment import SentimentAnalyzer
from honeygrabber.nlp.summarization import TextSummarizer

__all__ = [
    "NLPProcessor",
    "EntityExtractor",
    "KeywordExtractor",
    "SentimentAnalyzer",
    "TextSummarizer",
] 
