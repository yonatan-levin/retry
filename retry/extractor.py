import re
from .logger import logger
import spacy
from textblob import TextBlob
from spacy.matcher import Matcher

logger.name = 'extractor'

class ContentExtractor:
    def __init__(self, parser, rules, match_patterns: list[dict] = None):
        self.parser = parser
        self.rules = rules
        self.nlp = spacy.load('en_core_web_sm')

        self.matcher = Matcher(self.nlp.vocab)
        if match_patterns:
            for key, pattern in match_patterns.items():
                self.matcher.add(key, pattern)

    def extract(self):
  
        data = {}
        for key, rule in self.rules.items():
            try:     
                extractor_type = rule.get('extractor_type', 'default')
                if extractor_type == 'nlp':
                        data[key] = self._extract_nlp(rule)
                else:
                        data[key] = self._extract_default(rule)
                logger.debug(f"Extracted {key}: {data[key]}")
            except Exception as e:
                logger.error(f"Error extracting data: {e}")
                data[key] = None
        return data
    
    def _extract_default(self, rule):
        data = {}

        selector = rule.get('selector')
        selector_type = rule.get('type', 'css')
        attribute = rule.get('attribute')
        regex = rule.get('regex')
        multiple = rule.get('multiple', False)
        processor = rule.get('processor')

        elements = self.parser.select(selector, selector_type)
        values = []

        for element in elements:
            if isinstance(element, dict):
                # Handle JSON elements
                value = element.get(attribute) if attribute else element
            elif hasattr(element, 'get'):  # For BeautifulSoup elements
                if attribute:
                    value = element.get(attribute, '').strip()
                else:
                    value = element.text.strip()
            else:
                value = str(element).strip()

            if regex:
                match = re.search(regex, value)
                value = match.group(1) if match else None

            if processor and callable(processor):
                value = processor(value)

            if value:
                values.append(value)

            if not multiple:
                break

        data = values if multiple else (values[0] if values else None)
        logger.debug(f"Extracted {rule}: {data}")
        return data

    def _extract_nlp(self, rule):
        nlp_task = rule.get('nlp_task')
        # Where to get the text from
        text_source = rule.get('text_source', 'content')

        # Get the text to process
        if text_source == 'content':
            text = self.parser.get_text()
        else:
            # Extract text using a selector
            selector = rule.get('selector')
            selector_type = rule.get('type', 'css')
            elements = self.parser.select(selector, selector_type)
            texts = [element.get_text(strip=True) for element in elements]
            text = ' '.join(texts)

        doc = self.nlp(text)

        if nlp_task == 'ner':
            entity_type = rule.get('entity_type')
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
                    
        # elif nlp_task == 'summary':
        #     # For now, we'll return None
        #     return None

        # elif nlp_task == 'classification':
        #     # Implement text classification using spaCy's text categorizer
        #     # Requires training a custom model
        #     # For now, we'll return None
        #     return None

        elif nlp_task == 'match_patterns':
            extracted_data = self._match_patterns(doc)
            return extracted_data
        else:
            return None

    def _analyze_sentiment(self,text):
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
