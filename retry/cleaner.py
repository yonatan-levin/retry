import unicodedata

class DataCleaner:
    def clean(self, data):
        cleaned_data = {}
        for key, value in data.items():
            if isinstance(value, list):
                cleaned_data[key] = [self._clean_value(v) for v in value]
            else:
                cleaned_data[key] = self._clean_value(value)
        return cleaned_data

    def _clean_value(self, value):
        if isinstance(value, str):
            value = unicodedata.normalize('NFKC', value)
            value = value.strip()
        return value
