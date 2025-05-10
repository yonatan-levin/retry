from typing import Callable, List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, root_validator, RootModel


class ExtractorType(str, Enum):
    DEFAULT = 'default'
    NLP = 'nlp'


class PosTags(str, Enum):
    NOUN = 'NOUN'
    VERB = 'VERB'
    ADJ = 'ADJ'
    ADV = 'ADV'
    PROPN = 'PROPN'
    NUM = 'NUM'
    PRON = 'PRON'
    DET = 'DET'
    ADP = 'ADP'
    AUX = 'AUX'
    INTJ = 'INTJ'
    CONJ = 'CONJ'
    PART = 'PART'
    PUNCT = 'PUNCT'
    SYM = 'SYM'
    X = 'X'


class NLPTask(str, Enum):
    NER = 'ner'
    KEYWORDS = 'keywords'
    SENTIMENT = 'sentiment'
    SUMMARY = 'summary'
    MATCH_PATTERNS = 'match_patterns'


class TextSource(str, Enum):
    CONTENT = 'content'
    SELECTOR = 'selector'
    DEPENDENT = 'dependent'


class Rule(BaseModel):
    extractor_type: ExtractorType = ExtractorType.DEFAULT
    selector: Optional[str] = None
    type: Optional[str] = None
    attribute: Optional[str] = None
    regex: Optional[str] = None
    multiple: bool = False
    parent: bool = False
    processor: Optional[Callable[[Any], Any]] = None
    fields: Optional[Dict[str, 'Rule']] = None
    nlp_task: Optional[NLPTask] = None
    text_source: TextSource = TextSource.CONTENT
    dependent_item: Optional[str] = None
    entity_type: Optional[str] = None
    pos_tags: Optional[List[PosTags]] = None

    @root_validator(skip_on_failure=True)
    def validate_rule(cls, values):

        fields = values.get('fields')
        if fields:
            values['parent'] = True
            for name, sub in fields.items():
                if sub.parent:
                    raise ValueError(f"'parent' cannot be True in child rule '{name}'")
                if sub.multiple:
                    raise ValueError(f"'multiple' cannot be True in child rule '{name}'")
            return values

        et = values.get('extractor_type')
        sel = values.get('selector')
        nlp = values.get('nlp_task')
        txt_src = values.get('text_source')
        dep   = values.get('dependent_item')

        if et == ExtractorType.DEFAULT:
            if not sel:
                raise ValueError("selector is required for default extractor_type")
            if nlp:
                raise ValueError("nlp_task should not be set for default extractor_type")
            if not values.get('type'):
                raise ValueError("type is required for default extractor_type")

        elif et == ExtractorType.NLP:
            if not nlp:
                raise ValueError("nlp_task is required for nlp extractor_type")
            if txt_src == TextSource.SELECTOR and not sel:
                raise ValueError("selector must be set when text_source is 'selector'")
            if txt_src == TextSource.DEPENDENT and not dep:
                raise ValueError("dependent_item is required when text_source is 'dependent'")

        return values
    class Config:
        arbitrary_types_allowed = True


Rule.update_forward_refs()


class Rules(RootModel[Dict[str, Rule]]):
    """Root model for a mapping of rule names to Rule instances."""

    def get_rule(self, name: str) -> Optional[Rule]:
        """Return the rule by name, or None if not found."""
        return self.root.get(name)

    def all_rules(self) -> Dict[str, Rule]:
        """Return the entire rules mapping."""
        return self.root
