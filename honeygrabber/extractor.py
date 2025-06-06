import enum
import re
from typing import Optional, Dict, Any, Union
import spacy
from textblob import TextBlob
from spacy.matcher import Matcher
from honeygrabber.models.rules import Rules, Rule
from honeygrabber.parser import ContentParser
from .logger import getLogger   

logger = getLogger(__name__)


class ContentExtractor:

    def __init__(self,
                 parser: ContentParser = None,
                 rules: Union[Dict[str, Any], Rules] = None,
                 match_patterns: Optional[Dict[str, Any]] = None,
                 extractor_config: Optional[Any] = None):

        self._rules = None
        self.data = {}

        if extractor_config:
            self.parser = extractor_config.parser or parser
            if extractor_config.rules and any(value is not None for value in extractor_config.rules.values()):
                self.rules = extractor_config.rules
            else:
                self.rules = rules or {}
            self.match_patterns = extractor_config.match_patterns or match_patterns or {}
        else:
            self.parser = parser
            self.rules = rules or {}
            self.match_patterns = match_patterns or {}

        self.nlp = spacy.load('en_core_web_sm')
        self.matcher = Matcher(self.nlp.vocab)
        if self.match_patterns:
            for key, pattern in self.match_patterns.items():
                self.matcher.add(key, pattern)

    @property
    def rules(self):
        return self._rules

    @rules.setter
    def rules(self, rules):
        if rules is None:
            self._rules = {}
        elif isinstance(rules, Rules):
            # Directly unwrap if a Rules instance is provided
            self._rules = rules.root
        elif isinstance(rules, dict):
            # Validate dict against the Rules root model
            validated = Rules.model_validate(rules)
            self._rules = validated.root
        else:
            raise ValueError("Invalid rules format. Must be a dict or Rules object.")

    def extract(self):  
        for key, rule in self.rules.items():
            try:
                data = self._process_rule(self.parser, rule)                                  
                self.data[key] = data
                logger.debug(f"Extracted {key}: {self.data[key]}")
            except Exception as e:
                logger.error(f"Error extracting data for {key}: {e}")
                self.data[key] = None
        return self.data

    def _process_rule(self, parser: ContentParser, rule: Rule, is_multiple: bool = None):

        # Determine is_multiple: if provided, use it; else use rule.multiple
        if is_multiple is None and rule.multiple is not None:
            is_multiple = rule.multiple

        fields = rule.fields

        if fields:
            self.item = {}
            for field_name, field_rule in fields.items():
                try:
                    self.item[field_name] = self._process_rule(parser, field_rule, is_multiple=is_multiple)
                    logger.debug(f"Extracted {field_name}: {self.item[field_name]}")
                except Exception as e:
                    logger.error(f"Error extracting data for {field_name}: {e}")
                    self.item[field_name] = None
            return self.item
        else:
            # Handle extraction based on extractor_type
            if rule.extractor_type == 'nlp':
                return self._extract_nlp(rule, parser, is_multiple)
            else:
                return self._extract_data(rule, parser, is_multiple)

    def _extract_data(self, rule: Rule, parser: ContentParser, is_multiple: bool = None):

        if rule.type == 'json':
            elements = parser.select_json(rule.selector)
        else:
            elements = parser.select(rule.selector, rule.type) if rule.selector else [parser.content]

        results = []
        for element in elements:
            try:
                # Extract value from element
                value = None
                if isinstance(element, dict):
                    # Handle JSON elements
                    value = element.get(rule.attribute) if rule.attribute else element
                elif hasattr(element, 'get'):  # For BeautifulSoup elements
                    if rule.attribute:
                        attr_value = element.get(rule.attribute, '')
                        if isinstance(attr_value, list):
                            # Process each item in the list
                            value = ' '.join(item.strip()
                                            for item in attr_value if isinstance(item, str))
                        elif isinstance(attr_value, str):
                            value = attr_value.strip()
                        else:
                            value = str(attr_value).strip()
                    else:
                        value = element.text.strip()
                else:
                    # Default handling for other element types
                    value = str(element).strip() if element is not None else None

                if rule.regex and value is not None and isinstance(value, str):
                    match = re.search(rule.regex, value)
                    value = match.group(1) if match else None

                if rule.processor and callable(rule.processor) and value is not None:
                    value = rule.processor(value)

                if value is not None:
                    results.append(value)

                if not is_multiple:
                    break
                    
            except Exception as e:
                logger.error(f"Error extracting data: {e}")
                continue

        data = results if is_multiple else (results[0] if results else None)
        return data

    def _extract_nlp(self, rule: Rule, parser: ContentParser, is_multiple: bool = None):

        nlp_task = rule.nlp_task
        text_source = rule.text_source
        
        # Get the text to process
        if text_source.value == 'content':
            text = parser.parsed_content.get_text() 
        elif text_source.value == 'dependent':
            text = self.item[rule.dependent_item]
        else:
            # If text_source is a selector, extract text using that selector
            elements = parser.select(rule.selector, rule.type) if rule.selector else [parser.content]
            texts = []
            for element in elements:
                text_content = element.get_text(strip=True)
                texts.append(text_content)
                if not is_multiple:
                    break
            text = ' '.join(texts)

        doc = self.nlp(text)

        if nlp_task.value == 'ner':
            entity_type = rule.entity_type
            entities = [ent.text for ent in doc.ents if ent.label_ ==
                        entity_type] if entity_type else [ent.text for ent in doc.ents]
            return entities

        elif nlp_task.value == 'keywords':
            # Simple keyword extraction using part-of-speech tagging
            # Allow customization of POS tags
            # Other options include: 'ADJ', 'ADV', 'VERB', 'PRON', 'DET', 'ADP', 'CONJ', 'NUM', 'PUNCT', 'SYM', 'X'
            pos_tags = rule.pos_tags or ['NOUN', 'PROPN']
            
            # Convert all items in pos_tags to strings (if they are enum.Enum)
            pos_tags_str = []
            for tag in pos_tags:
                if isinstance(tag, enum.Enum):
                    pos_tags_str.append(tag.value)
                else:
                    pos_tags_str.append(tag)
            
            keywords = [token.text for token in doc if token.pos_ in pos_tags_str]
            
            return keywords

        elif nlp_task.value == 'sentiment':
            blob = self._analyze_sentiment(text)
            return blob

        elif nlp_task.value == 'summary':
            # Placeholder for summary task
            return "Summary functionality not implemented."

        elif nlp_task.value == 'match_patterns':
            extracted_data = self._match_patterns(doc)
            return extracted_data
        else:
            return None

    def _analyze_sentiment(self, text):
        # Create a TextBlob object
        blob = TextBlob(text)

        # Get the sentiment polarity
        polarity = blob.sentiment.polarity

        # Get the sentiment subjectivity
        subjectivity = blob.sentiment.subjectivity

        # Determine sentiment label
        if polarity >= 0.75:
            sentiment = "Positive"
        elif polarity < 0:
            sentiment = "Negative"
        else:
            sentiment = "Neutral"

        # Round polarity and subjectivity to 2 decimal places
        polarity = round(polarity, 2)
        subjectivity = round(subjectivity, 2)

        return {
            "sentiment": sentiment,
            "polarity": polarity,
            "subjectivity": subjectivity
        }

    def _match_patterns(self, doc):
        matches = self.matcher(doc)
        extracted_data = {}
        for match_id, start, end in matches:
            span = doc[start:end]
            label = self.nlp.vocab.strings[match_id]
            extracted_data.setdefault(label, []).append(span.text)
        return extracted_data
