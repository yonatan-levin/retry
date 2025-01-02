from typing import Callable, List, Optional, Dict
from enum import Enum
from pydantic import BaseModel, ConfigDict, field_validator, model_validator
from pydantic import RootModel

class ExtractorType(Enum):
    DEFAULT = 'default'
    NLP = 'nlp'
    
class PosTags(Enum):
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

class NLPTask(Enum):
    NER = 'ner'
    KEYWORDS = 'keywords'
    SENTIMENT = 'sentiment'
    SUMMARY = 'summary'
    MATCH_PATTERNS = 'match_patterns'

class TextSource(Enum):
    CONTENT = 'content'
    SELECTOR = 'selector'
    DEPENDENT = 'dependent'

class Rule(BaseModel):
    extractor_type: Optional[str] = ExtractorType.DEFAULT
    selector: Optional[str] = None
    type: Optional[str] = None  # No default value
    attribute: Optional[str] = None
    regex: Optional[str] = None
    multiple: Optional[bool] = False
    parent: Optional[bool] = False
    processor: Optional[Callable] = None  
    fields: Optional[Dict[str, 'Rule']] = None  # Recursive definition
    nlp_task: Optional[NLPTask] = None
    text_source: Optional[TextSource] = TextSource.CONTENT
    dependent_item: Optional[str] = None
    entity_type: Optional[str] = None
    pos_tags: Optional[List[PosTags]] = None

    @field_validator('extractor_type')
    def validate_extractor_type(cls, v):
        if v not in ('default', 'nlp'):
            raise ValueError("extractor_type must be 'default' or 'nlp'")
        
        return v
    
    @field_validator('type')
    def validate_type(cls, v, info):
        # We can safely use info.data since it will always exist
        extractor_type = info.data['extractor_type']  # No need for get() with default
        if extractor_type == 'default' and not v:
            raise ValueError("Field 'type' is required when 'extractor_type' is 'default'")
        return v

    @model_validator(mode='after')
    def check_required_fields(cls, values):
        if not values.extractor_type:
            values.extractor_type = 'default'
            
        if values.extractor_type == 'default':
            if not values.selector:
                raise ValueError("Field 'selector' is required when 'extractor_type' is 'default'")
            if values.nlp_task:
                raise ValueError("Field 'nlp_task' should not be set when 'extractor_type' is 'default'")
                
        elif values.extractor_type == 'nlp':
            
            if not values.nlp_task:
                raise ValueError("Field 'nlp_task' is required when 'extractor_type' is 'nlp'")
            
            if (values.selector and values.text_source.value is not 'selector')  or (values.text_source.value is 'selector' and not values.selector):
                raise ValueError("Field 'text_source' should be 'selector' with filed 'selector' set")

            if values.text_source.value is 'dependent' and not values.dependent_item:
                raise ValueError("Field 'dependent_item' is required when 'text_source' is 'dependent'")                
            
        if values.fields:
            values.parent = True
            for field_name, field_rule in values.fields.items():
                if field_rule.parent:
                    raise ValueError(f"'parent' cannot be set in child rule '{field_name}'")  
         
        return values


    @model_validator(mode='after')
    def check_multiple_child_field(cls, values):
        fields = values.fields
        if fields:
            for field_name, field_rule in fields.items():
                if field_rule.multiple:
                    raise ValueError(f"'multiple' cannot be set in child rule '{field_name}'")
        return values

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

Rule.model_rebuild()


class Rules(RootModel[Dict[str, Rule]]):
    pass


