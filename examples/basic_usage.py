import asyncio
from retry import Retry

rules = {
    'books': {
        'selector': 'article.product_pod',
        'type': 'css',
        'multiple': True,
        'rules': {
            'title': {
                'selector': 'h3 > a',
                'type': 'css',
                'attribute': 'title',
            },
            'price': {
                'selector': 'p.price_color',
                'type': 'css',
            },
            'rating': {
                'selector': 'p.star-rating',
                'type': 'css',
                'attribute': 'class',
                'regex': r'star-rating (\w+)',
            },
            'availability': {
                'selector': 'p.instock.availability',
                'type': 'css',
                'processor': lambda x: x.strip(),
            },
            'detail_url': {
                'selector': 'h3 > a',
                'type': 'css',
                'attribute': 'href',
                'processor': lambda x: 'https://books.toscrape.com/catalogue/' + x.replace('../../../', ''),
            },
        }
    }
}

async def main():
    # Initialize the scraper
    scraper = Retry()
    # Scrape using fetch_with_playwright
    data = await scraper.scrape('https://books.toscrape.com', rules, fetch_method='fetch_with_playwright')
    # Output the results
    print(scraper.output(data, format_type='json'))

asyncio.run(main())