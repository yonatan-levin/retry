from dataclasses import dataclass

@dataclass
class CleanerConfig:
    additional_patterns: str = None
    replace_defaults: bool = False
    custom_nlp_components: dict = None
    flags = 0