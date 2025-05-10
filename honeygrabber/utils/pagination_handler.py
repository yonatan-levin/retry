from urllib.parse import urljoin

class PaginationHandler:
    def __init__(self, next_page_selector, selector_type='css', limit=None):
        """
        Initialize the PaginationHandler.

        :param next_page_selector: The selector to find the next page link.
        :param selector_type: The type of selector ('css' or 'xpath').
        :param limit: The maximum number of pages to scrape.
        """
        self.next_page_selector = next_page_selector
        self.selector_type = selector_type
        self.limit = limit

    def get_next_page_url(self, parser, current_url):
        """
        Retrieves the URL of the next page.

        :param parser: An instance of HTMLParser.
        :param current_url: The current page URL.
        :return: The URL of the next page or None if not found.
        """
        elements = parser.select(self.next_page_selector, self.selector_type)
        if elements:
            href = elements[0].get('href')
            if href:
                return urljoin(current_url, href)
        return None

    async def paginate(self, initial_url, fetch_page, parse_page):
        """
        Handles the pagination loop.

        :param initial_url: The starting URL.
        :param fetch_page: A coroutine to fetch page content.
        :param parse_page: A function to parse page content.
        :return: A list of parsed data from all pages.
        """
        results = []
        url = initial_url
        page_count = 0

        while url:
            content = await fetch_page(url)
            parser = parse_page(content)
            data = parser.extract()
            results.extend(data)

            url = self.get_next_page_url(parser, url)
            page_count += 1

            if self.limit and page_count >= self.limit:
                break

        return results
