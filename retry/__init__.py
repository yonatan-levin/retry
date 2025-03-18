"""
retry - Advanced web scraping library with support for asynchronous programming and NLP.

This package provides a comprehensive set of tools for web scraping,
including request handling, content parsing, data extraction, and more.
"""

__version__ = "0.2.0"

# Core components
from retry.retry import Retry as RetrySC  # Import the main class from retry.py

# Models
from retry.models.rules import Rules, Rule

# Utils
from retry.utils.cache import SimpleCache, MemoryCache, FileCache
from retry.utils.pagination import PaginationHandler
from retry.utils.rate_limiter import RateLimiter
from retry.utils.session_manager import SessionManager
from retry.utils.authentication import (
    BasicAuth,
    FormAuth,
    TokenAuth,
    AuthManager
)

# NLP components
try:
    from retry.nlp.processor import NLPProcessor
    from retry.nlp.entities import EntityExtractor
    from retry.nlp.keywords import KeywordExtractor
    from retry.nlp.sentiment import SentimentAnalyzer
    from retry.nlp.summarization import TextSummarizer
    
    NLP_AVAILABLE = True
except ImportError:
    NLP_AVAILABLE = False

# Parser and Extractors
from retry.parser import ContentParser
from retry.extractor import ContentExtractor
from retry.formatter import OutputFormatter
from retry.cleaner import Cleaner
from retry.fetcher import Fetcher

# Configuration
from retry.utils.logger import get_logger, setup_file_logging, set_log_level

__all__ = [
    # Core
    "RetrySC",
    
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