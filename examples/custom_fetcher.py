import asyncio
from retry import RetrySC
from retry.fetcher import BaseFetcher

rules = {
    "title": {
        "selector": "h1",
        "type": "css"
    },
    "content": {
        "selector": "//article//p",
        "type": "xpath",
        "multiple": True
    },
    "links": {
        "selector": "a",
        "type": "css",
        "attribute": "href",
        "multiple": True
    }
}


class CustomFetcher(BaseFetcher):
    async def fetch(self, url, retries=3):
        print(url, retries)
        pass


async def main():
    # Initialize the scraper with the custom fetcher
    scraper = RetrySC(fetcher=CustomFetcher())

    # Scrape using the custom fetch method
    data = await scraper.scrape('https://google.com', rules)

    # Output the results
    print(scraper.output(data))

asyncio.run(main())