import json
import re
from typing import Optional, Dict, Any, Union
import spacy
from textblob import TextBlob
from spacy.matcher import Matcher
from retry.models.rules import Rules, Rule
# Adjust the import based on your project structure
from retry.parser import ContentParser
from .logger import logger  # Adjust the import based on your project structure

logger.name = 'extractor'


# The updated ContentExtractor class
class ContentExtractor:
    def __init__(self,
                 parser: ContentParser = None,
                 rules: Union[Dict[str, Any], Rules] = None,
                 match_patterns: Optional[Dict[str, Any]] = None,
                 extractor_config: Optional[Any] = None):  # Adjust type as needed
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

        # Validate and parse rules if they are provided as dict
        if isinstance(self.rules, dict):
            self.rules = Rules.model_validate(self.rules)
        elif isinstance(self.rules, Rules):
            self.rules = self.rules.__root__
        else:
            raise ValueError(
                "Invalid rules format. Must be a dict or Rules object.")

        self.nlp = spacy.load('en_core_web_sm')
        self.matcher = Matcher(self.nlp.vocab)
        if self.match_patterns:
            for key, pattern in self.match_patterns.items():
                self.matcher.add(key, pattern)

    def extract(self):
        data = {}
        for key, rule in self.rules.root.items():
            try:
                data[key] = self._process_rule(self.parser, rule)
                logger.debug(f"Extracted {key}: {data[key]}")
            except Exception as e:
                logger.error(f"Error extracting data for {key}: {e}")
                data[key] = None
        return data

    def _process_rule(self, parser, rule: Rule):
        fields = rule.fields
        if fields:
            item = {}
            for field_name, field_rule in fields.items():
                try:
                    # Use the same parser for nested fields unless a new parser is needed
                    item[field_name] = self._process_rule(parser, field_rule)
                    logger.debug(f"Extracted {field_name}: {item[field_name]}")
                except Exception as e:
                    logger.error(
                        f"Error extracting data for {field_name}: {e}")
                    item[field_name] = None
            return item
        else:
            # Handle extraction based on extractor_type
            if rule.extractor_type == 'nlp':
                return self._extract_nlp(rule, parser=parser)
            else:
                return self._extract_data(parser, rule)

    def _extract_data(self, parser: ContentParser, rule: Rule):

        if rule.type == 'json':
            elements = parser.select_json(rule.selector)
        else:
            elements = parser.select(rule.selector, rule.type) if rule.selector else [
                parser.content]

        results = []
        for element in elements:
            # Extract value from element
            if isinstance(element, dict):
                # Handle JSON elements
                value = element.get(
                    rule.attribute) if rule.attribute else element
            elif hasattr(element, 'get'):  # For BeautifulSoup elements
                if rule.attribute:
                    value = element.get(rule.attribute, '').strip()
                else:
                    value = element.text.strip()
            else:
                value = str(element).strip()

            if rule.regex:
                match = re.search(rule.regex, value)
                value = match.group(1) if match else None

            if rule.processor and callable(rule.processor):
                value = rule.processor(value)

            if value is not None:
                results.append(value)

            if not rule.multiple:
                break

        data = results if rule.multiple else (results[0] if results else None)
        return data

    def _extract_nlp(self, rule: Rule, parser=None):
        nlp_task = rule.nlp_task
        text_source = rule.text_source or 'content'

        # Use the provided parser or default to self.parser
        parser = parser or self.parser

        # Get the text to process
        if text_source == 'content':
            text = parser.get_text()
        else:
            # If text_source is a selector, extract text using that selector
            elements = parser.select(
                text_source, rule.type) if rule.type and text_source else [parser.content]
            texts = [element.get_text(strip=True) for element in elements]
            text = ' '.join(texts)

        doc = self.nlp(text)

        if nlp_task == 'ner':
            entity_type = rule.entity_type
            entities = [ent.text for ent in doc.ents if ent.label_ ==
                        entity_type] if entity_type else [ent.text for ent in doc.ents]
            return entities

        elif nlp_task == 'keywords':
            # Simple keyword extraction using part-of-speech tagging
            keywords = [
                token.text for token in doc if token.pos_ in ['NOUN', 'PROPN']]
            return keywords

        elif nlp_task == 'sentiment':
            blob = self._analyze_sentiment(text)
            return blob

        elif nlp_task == 'summary':
            # Placeholder for summary task
            return "Summary functionality not implemented."

        elif nlp_task == 'match_patterns':
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
