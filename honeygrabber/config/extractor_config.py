from typing import Dict, Any, Union
from dataclasses import dataclass
from honeygrabber.models.rules import Rules
from honeygrabber.parser import ContentParser

@dataclass
class ExtractorConfig:
    match_patterns: list[dict] = None
    rules: Union[Dict[str, Any], Rules] = None,                 
    parser: ContentParser = None
