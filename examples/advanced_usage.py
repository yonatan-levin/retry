import asyncio
from honeygrabber import HoneyGrabberSC

# Define extraction rules
rules = {
    'title': {
        'selector': 'article.product_page h1',
        'type': 'css',
    },
    'content': {
        'selector': 'div#product_description + p',
        'type': 'css',
        'multiple': True,
    },
    'entities': {
        'extractor_type': 'nlp',
        'nlp_task': 'ner',
    },
    'keywords': {
        'extractor_type': 'nlp',
        'nlp_task': 'keywords',
    },
    'sentiment': {
        'extractor_type': 'nlp',
        'nlp_task': 'sentiment',
    },
}

async def main():
    url = 'https://books.toscrape.com/catalogue/sharp-objects_997/index.html'
    scraper = HoneyGrabberSC()
    data = await scraper.scrape(url, rules)
    print(scraper.output(data, format_type='json', structure_data=False))

if __name__ == '__main__':
    asyncio.run(main())
