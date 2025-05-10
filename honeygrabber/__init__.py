"""
honeygrabber - Advanced web scraping library with support for asynchronous programming and NLP.

This package provides a comprehensive set of tools for web scraping,
including request handling, content parsing, data extraction, and more.
"""

__version__ = "0.2.0"

# Core components
from honeygrabber.honeygrabber import HoneyGrabber as HoneyGrabberSC  # New preferred alias for backward compatibility

# Models
from honeygrabber.models.rules import Rules, Rule

# Utils
from honeygrabber.utils.cache import SimpleCache, MemoryCache, FileCache
from honeygrabber.utils.pagination import PaginationHandler
from honeygrabber.utils.rate_limiter import RateLimiter
from honeygrabber.utils.session_manager import SessionManager
from honeygrabber.utils.authentication import (
    BasicAuth,
    FormAuth,
    TokenAuth,
    AuthManager
)

# NLP components
try:
    from honeygrabber.nlp.processor import NLPProcessor
    from honeygrabber.nlp.entities import EntityExtractor
    from honeygrabber.nlp.keywords import KeywordExtractor
    from honeygrabber.nlp.sentiment import SentimentAnalyzer
    from honeygrabber.nlp.summarization import TextSummarizer
    
    NLP_AVAILABLE = True
except ImportError:
    NLP_AVAILABLE = False

# Parser and Extractors
from honeygrabber.parser import ContentParser
from honeygrabber.extractor import ContentExtractor
from honeygrabber.formatter import OutputFormatter
from honeygrabber.cleaner import Cleaner
from honeygrabber.fetcher import Fetcher

# Configuration
from honeygrabber.utils.logger import get_logger, setup_file_logging, set_log_level

__all__ = [
    # Core
    "HoneyGrabberSC",
    
    # Models
    "Rules",
    "Rule",
    
    # Utils
    "SimpleCache",
    "MemoryCache",
    "FileCache",
    "PaginationHandler",
    "RateLimiter",
    "SessionManager",
    "BasicAuth",
    "FormAuth",
    "TokenAuth",
    "AuthManager",
    
    # Parser and Extractors
    "ContentParser",
    "ContentExtractor",
    "OutputFormatter",
    "Cleaner",
    "Fetcher",
    
    # Configuration
    "get_logger",
    "setup_file_logging",
    "set_log_level",
]

# Add NLP components if available
if NLP_AVAILABLE:
    __all__.extend([
        "NLPProcessor",
        "EntityExtractor",
        "KeywordExtractor",
        "SentimentAnalyzer",
        "TextSummarizer",
    ])
