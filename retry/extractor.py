import re
from .logger import logger

class ContentExtractor:
    def __init__(self, parser, rules):
        self.parser = parser
        self.rules = rules

    def extract(self):
        data = {}
        for key, rule in self.rules.items():
            selector = rule.get('selector')
            selector_type = rule.get('type', 'css')
            attribute = rule.get('attribute')
            regex = rule.get('regex')
            multiple = rule.get('multiple', False)
            processor = rule.get('processor')

            elements = self.parser.select(selector, selector_type)
            values = []

            for element in elements:
                if attribute:
                    value = element.get(attribute, '').strip()
                else:
                    value = element.text_content().strip()

                if regex:
                    match = re.search(regex, value)
                    value = match.group(1) if match else None

                if processor and callable(processor):
                    value = processor(value)

                if value:
                    values.append(value)

                if not multiple:
                    break

            data[key] = values if multiple else (values[0] if values else None)
            logger.debug(f"Extracted {key}: {data[key]}")
        return data
