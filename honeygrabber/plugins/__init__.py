class BasePlugin:
    def process(self, data):
        """
        Process the extracted data.

        :param data: The data extracted by the scraper.
        :return: Modified data after processing.
        """
        raise NotImplementedError("Plugins must implement the 'process' method.")
