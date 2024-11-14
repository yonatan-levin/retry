import hashlib
import re
import regex
import spacy
from spacy.util import compile_infix_regex
from spacy.tokens import Span
from .constants import UNWANTED_PATTERNS, CUSTOM_INFIXES
from .logger import logger

logger.name = 'cleaner'


class Cleaner:
    def __init__(self, additional_patterns=None, replace_defaults=False, **kwargs):

        self.nlp = spacy.load('en_core_web_sm')
        self.unwanted_patterns = UNWANTED_PATTERNS
        infix_re = compile_infix_regex(CUSTOM_INFIXES)
        self.nlp.tokenizer.infix_finditer = infix_re.finditer
        self.seen_hashes = set()

        if not Span.has_extension('is_unwanted'):
            Span.set_extension('is_unwanted', default=False)

        if 'custom_nlp_components' in kwargs:
            for component, before in kwargs['custom_nlp_components']:
                self.nlp.add_pipe(component, before=before)

        if additional_patterns:
            self.add_unwanted_pattern(
                additional_patterns, replace_defaults=replace_defaults)

    def clean(self, data, case_sensitive=False):
        cleaned_data = {}
        for key, value in data.items():
            if value is None:
                    continue
            if isinstance(value, list):
                unique_items = []
                for item in value:
                    
                    if item is None:
                        continue
                    
                    if case_sensitive:
                        item_hash = hashlib.md5(item.lower().encode('utf-8')).hexdigest()
                    else:
                        item_hash = hashlib.md5(item.encode('utf-8')).hexdigest()
                        
                    if item_hash not in self.seen_hashes:
                        self.seen_hashes.add(item_hash)
                        
                        cleaned_text = self._normalize_text(item)
                        if cleaned_text != '':
                            unique_items.append(cleaned_text)
                            
                cleaned_data[key] = unique_items
            elif isinstance(value, str):
                cleaned_data[key] = self._normalize_text(value)
            else:
                cleaned_data[key] = value
        return cleaned_data

    def add_unwanted_pattern(self, pattern_str, flags=0, ignorecase=re.IGNORECASE, replace_defaults=False):
        """
        Compiles the given pattern string and adds it to the unwanted patterns list.

        Parameters:
        - pattern_str (str): The regex pattern as a string.
        - flags (int): Optional regex flags (e.g., re.IGNORECASE).
        """
        try:
            if replace_defaults:
                self.unwanted_patterns = re.compile(
                    pattern_str, flags, ignorecase)
                return

            compiled_pattern = re.compile(pattern_str, flags)
            self.unwanted_patterns.append(compiled_pattern)
        except Exception as e:
            logger.exception(e)

    def _normalize_text(self, text):
        # Remove extra whitespace and newlines
        text = ' '.join(text.split())
        doc = self.nlp(text)
        text = self._remove_unwanted(doc)

        tokens = []
        for sentence in doc.sents:
            if not sentence._.is_unwanted:
                for token in sentence:
                    if token.is_punct:
                        if tokens:
                            tokens[-1] += token.text_with_ws
                        else:
                            tokens.append(token.text_with_ws)
                    else:
                        tokens.append(token.text_with_ws)

        normalized_text = ''.join(tokens)
        return normalized_text

    def _remove_unwanted(self, doc):
        """
        Removes unwanted patterns from the text using spaCy for sentence tokenization.

        Parameters:
        - doc (spacy.tokens.Doc): The input text in tokenized format.

        Returns:
        - Doc: The spaCy Doc object with sentences marked as unwanted.        
        """
        # Mark sentences as unwanted
        for sentence in doc.sents:
            sentence_text = sentence.text.strip()
            if any(pattern.search(sentence_text) for pattern in self.unwanted_patterns):
                sentence._.is_unwanted = True
            else:
                sentence._.is_unwanted = False

        return doc
