from . import BasePlugin

class SamplePlugin(BasePlugin):
    def process(self, data):
        """
        A sample plugin that capitalizes all string values in the data.

        :param data: The extracted data.
        :return: The modified data.
        """
        processed_data = {}
        for key, value in data.items():
            if isinstance(value, str):
                processed_data[key] = value.upper()
            elif isinstance(value, list):
                processed_data[key] = [v.upper() if isinstance(v, str) else v for v in value]
            else:
                processed_data[key] = value
        return processed_data
