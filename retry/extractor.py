import re
from typing import Optional, Dict, Any, Union
import spacy
from textblob import TextBlob
from spacy.matcher import Matcher
from retry.models.rules import Rules, Rule
from retry.parser import ContentParser
from .logger import getLogger

logger = getLogger(__name__)


class ContentExtractor:

    def __init__(self,
                 parser: ContentParser = None,
                 rules: Union[Dict[str, Any], Rules] = None,
                 match_patterns: Optional[Dict[str, Any]] = None,
                 extractor_config: Optional[Any] = None):

        self._rules = None

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
        if rules is not None:
            # Validate and parse rules if they are provided as dict
            if isinstance(rules, dict):
                validated_rules = Rules.model_validate(rules)
                self._rules = validated_rules.root
            elif isinstance(rules, Rules):
                self._rules = rules.root
            else:
                raise ValueError(
                    "Invalid rules format. Must be a dict or Rules object.")
        else:
            self._rules = {}

    def extract(self):
        self.data = {}
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
            item = {}
            for field_name, field_rule in fields.items():
                try:
                    item[field_name] = self._process_rule(parser, field_rule, is_multiple=is_multiple)
                    logger.debug(f"Extracted {field_name}: {item[field_name]}")
                except Exception as e:
                    logger.error(
                        f"Error extracting data for {field_name}: {e}")
                    item[field_name] = None
            return item
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
            # Extract value from element
            if isinstance(element, dict):
                # Handle JSON elements
                value = element.get(
                    rule.attribute) if rule.attribute else element
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

            if rule.regex and isinstance(value, str):
                match = re.search(rule.regex, value)
                value = match.group(1) if match else None

            if rule.processor and callable(rule.processor):
                value = rule.processor(value)

            if value is not None:
                results.append(value)

            if not is_multiple:
                break

        data = results if is_multiple else (results[0] if results else None)
        return data

    def _extract_nlp(self, rule: Rule, parser: ContentParser, is_multiple: bool = None):

        nlp_task = rule.nlp_task
        text_source = rule.text_source or 'content'

        # Get the text to process
        if text_source == 'content':
            text = parser.parsed_content.get_text()
        elif text_source in self.data:
            text = self.data[text_source]
        else:
            # If text_source is a selector, extract text using that selector
            elements = parser.select(text_source, rule.type) if rule.type and text_source else [parser.content]
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
            keywords = [token.text for token in doc if token.pos_ in pos_tags]

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