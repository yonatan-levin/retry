import asyncio
from retry import Retry

# Define extraction rules
rules = {
    'title': {
        'selector': 'h1.article-title',
        'type': 'css',
    },
    'content': {
        'selector': 'div.article-content',
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
    scraper = Retry()
    data = await scraper.scrape(url, rules)
    print(scraper.output(data, format_type='json'))

if __name__ == '__main__':
    asyncio.run(main())
