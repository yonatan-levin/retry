from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, field_validator, model_validator, validator, root_validator
from pydantic import RootModel


class Rule(BaseModel):
    extractor_type: Optional[str] = 'default'
    selector: Optional[str] = None
    type: Optional[str] = None  # No default value
    attribute: Optional[str] = None
    regex: Optional[str] = None
    multiple: Optional[bool] = False
    processor: Optional[Any] = None  # You can specify more precise types if needed
    fields: Optional[Dict[str, 'Rule']] = None  # Recursive definition
    nlp_task: Optional[str] = None
    text_source: Optional[str] = 'content'
    entity_type: Optional[str] = None

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
           
        return values

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

Rule.model_rebuild()

# If you have a Rules class, define it as follows:
class Rules(RootModel[Dict[str, Rule]]):
    pass