"""
Entity extraction module for honeygrabber.

This module provides the EntityExtractor class for extracting named entities from text.
"""

from typing import Dict, List, Optional, Any, Union, Set, Tuple
import re

from honeygrabber.nlp.processor import NLPProcessor
from honeygrabber.utils.logger import get_logger
from honeygrabber.utils.exceptions import NLPError

logger = get_logger(__name__)


class EntityExtractor:
    """
    Specialized class for named entity recognition.
    
    This class provides methods for extracting named entities from text
    using spaCy's named entity recognition capabilities.
    
    Attributes:
        nlp_processor: NLP processor instance
        entity_types: List of entity types to extract
        custom_patterns: Dictionary of custom entity patterns
    """
    
    # Standard entity types in spaCy
    STANDARD_ENTITY_TYPES = {
        "PERSON": "People, including fictional",
        "NORP": "Nationalities or religious or political groups",
        "FAC": "Buildings, airports, highways, bridges, etc.",
        "ORG": "Companies, agencies, institutions, etc.",
        "GPE": "Countries, cities, states",
        "LOC": "Non-GPE locations, mountain ranges, bodies of water",
        "PRODUCT": "Objects, vehicles, foods, etc. (not services)",
        "EVENT": "Named hurricanes, battles, wars, sports events, etc.",
        "WORK_OF_ART": "Titles of books, songs, etc.",
        "LAW": "Named documents made into laws",
        "LANGUAGE": "Any named language",
        "DATE": "Absolute or relative dates or periods",
        "TIME": "Times smaller than a day",
        "PERCENT": "Percentage, including '%'",
        "MONEY": "Monetary values, including unit",
        "QUANTITY": "Measurements, as of weight or distance",
        "ORDINAL": "First, second, etc.",
        "CARDINAL": "Numerals that do not fall under another type",
    }
    
    def __init__(self,
                 nlp_processor: Optional[NLPProcessor] = None,
                 entity_types: Optional[List[str]] = None,
                 custom_patterns: Optional[Dict[str, List[str]]] = None):
        """
        Initialize an EntityExtractor.
        
        Args:
            nlp_processor: NLP processor instance to use
            entity_types: List of entity types to extract (None for all)
            custom_patterns: Dictionary of custom entity patterns
        """
        self.nlp_processor = nlp_processor or NLPProcessor()
        self.entity_types = entity_types
        self.custom_patterns = custom_patterns or {}
        
        # Compile regex patterns for custom entities
        self._compiled_patterns: Dict[str, List[re.Pattern]] = {}
        for entity_type, patterns in self.custom_patterns.items():
            self._compiled_patterns[entity_type] = [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
        
        logger.debug(f"Initialized EntityExtractor with {len(self.custom_patterns)} custom patterns")

    def extract_entities(self, text: str, include_custom: bool = True) -> List[Dict[str, Any]]:
        """
        Extract entities from text.
        
        Args:
            text: Text to extract entities from
            include_custom: Whether to include custom entity patterns
            
        Returns:
            List of dictionaries with entity information
            
        Raises:
            NLPError: If there is an error extracting entities
        """
        try:
            # Extract standard entities
            entities = self.nlp_processor.extract_entities(text, self.entity_types)
            
            # Extract custom entities if requested
            if include_custom and self.custom_patterns:
                custom_entities = self._extract_custom_entities(text)
                entities.extend(custom_entities)
                
                # Sort entities by their position in the text
                entities.sort(key=lambda x: x["start"])
            
            return entities
        
        except Exception as e:
            if isinstance(e, NLPError):
                raise
            error_msg = f"Error extracting entities: {str(e)}"
            logger.error(error_msg)
            raise NLPError("extract_entities", error_msg) from e
    
    def _extract_custom_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract custom entities using regex patterns.
        
        Args:
            text: Text to extract entities from
            
        Returns:
            List of dictionaries with entity information
        """
        custom_entities = []
        
        for entity_type, patterns in self._compiled_patterns.items():
            for pattern in patterns:
                for match in pattern.finditer(text):
                    custom_entities.append({
                        "text": match.group(0),
                        "label": entity_type,
                        "start": match.start(),
                        "end": match.end(),
                        "source": "custom_pattern",
                    })
        
        return custom_entities
    
    def add_custom_pattern(self, entity_type: str, pattern: str) -> None:
        """
        Add a custom entity pattern.
        
        Args:
            entity_type: Type of the entity
            pattern: Regex pattern to match the entity
        """
        if entity_type not in self.custom_patterns:
            self.custom_patterns[entity_type] = []
        
        self.custom_patterns[entity_type].append(pattern)
        self._compiled_patterns.setdefault(entity_type, []).append(re.compile(pattern, re.IGNORECASE))
        
        logger.debug(f"Added custom pattern for {entity_type}: {pattern}")
    
    def remove_custom_pattern(self, entity_type: str, pattern: str) -> bool:
        """
        Remove a custom entity pattern.
        
        Args:
            entity_type: Type of the entity
            pattern: Regex pattern to remove
            
        Returns:
            True if the pattern was removed, False otherwise
        """
        if entity_type in self.custom_patterns and pattern in self.custom_patterns[entity_type]:
            self.custom_patterns[entity_type].remove(pattern)
            
            # Recompile all patterns for this entity type
            self._compiled_patterns[entity_type] = [re.compile(p, re.IGNORECASE) for p in self.custom_patterns[entity_type]]
            
            logger.debug(f"Removed custom pattern for {entity_type}: {pattern}")
            return True
        
        return False
    
    def clear_custom_patterns(self, entity_type: Optional[str] = None) -> None:
        """
        Clear custom entity patterns.
        
        Args:
            entity_type: Type of the entity to clear patterns for (None for all)
        """
        if entity_type is None:
            self.custom_patterns.clear()
            self._compiled_patterns.clear()
            logger.debug("Cleared all custom patterns")
        elif entity_type in self.custom_patterns:
            self.custom_patterns.pop(entity_type)
            self._compiled_patterns.pop(entity_type, None)
            logger.debug(f"Cleared custom patterns for {entity_type}")
    
    def extract_entity_relations(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract entity relations from text.
        
        Args:
            text: Text to extract entity relations from
            
        Returns:
            List of dictionaries with relation information
            
        Raises:
            NLPError: If there is an error extracting relations
        """
        try:
            self.nlp_processor.ensure_model_loaded()
            doc = self.nlp_processor.process_text(text)
            
            relations = []
            
            # A simple approach: look for subject-verb-object patterns
            for sent in doc.sents:
                # Find subjects and objects
                subjects = []
                objects = []
                verb = None
                
                for token in sent:
                    # Find the main verb
                    if token.pos_ == "VERB" and token.dep_ in ("ROOT", "xcomp"):
                        verb = token
                    
                    # Find subjects
                    if token.dep_ in ("nsubj", "nsubjpass") and token.ent_type_:
                        subjects.append(token)
                    
                    # Find objects
                    if token.dep_ in ("dobj", "pobj") and token.ent_type_:
                        objects.append(token)
                
                # Create relations
                if verb and subjects and objects:
                    for subj in subjects:
                        for obj in objects:
                            relations.append({
                                "subject": {
                                    "text": subj.text,
                                    "label": subj.ent_type_,
                                },
                                "predicate": verb.text,
                                "object": {
                                    "text": obj.text,
                                    "label": obj.ent_type_,
                                },
                                "sentence": sent.text,
                            })
            
            return relations
        
        except Exception as e:
            if isinstance(e, NLPError):
                raise
            error_msg = f"Error extracting entity relations: {str(e)}"
            logger.error(error_msg)
            raise NLPError("extract_entity_relations", error_msg) from e
    
    def get_entity_counts(self, text: str) -> Dict[str, Dict[str, int]]:
        """
        Get entity counts by type.
        
        Args:
            text: Text to extract entities from
            
        Returns:
            Dictionary with entity counts by type
            
        Raises:
            NLPError: If there is an error extracting entities
        """
        try:
            entities = self.extract_entities(text)
            
            counts: Dict[str, Dict[str, int]] = {}
            
            for entity in entities:
                entity_type = entity["label"]
                entity_text = entity["text"].lower()
                
                if entity_type not in counts:
                    counts[entity_type] = {}
                
                counts[entity_type][entity_text] = counts[entity_type].get(entity_text, 0) + 1
            
            return counts
        
        except Exception as e:
            if isinstance(e, NLPError):
                raise
            error_msg = f"Error getting entity counts: {str(e)}"
            logger.error(error_msg)
            raise NLPError("get_entity_counts", error_msg) from e
    
    @staticmethod
    def list_standard_entity_types() -> Dict[str, str]:
        """
        List standard entity types.
        
        Returns:
            Dictionary of standard entity types and their descriptions
        """
        return EntityExtractor.STANDARD_ENTITY_TYPES 
