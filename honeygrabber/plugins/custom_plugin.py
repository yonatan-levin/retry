from . import BasePlugin

class CustomPlugin(BasePlugin):
    def process(self, data):
        """
        A custom plugin that filters out any data entries with empty values.

        :param data: The extracted data.
        :return: The filtered data.
        """
        return {k: v for k, v in data.items() if v}
