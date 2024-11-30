import asyncio
from retry import Retry

# Updated extraction rules with 'fields'
rules = {
    'books': {
        'selector': 'article.product_pod',
        'type': 'css',
        'multiple': True,
        'fields': {
            'title': {
                'selector': 'h3 > a',
                'type': 'css',
                'attribute': 'title',
                'multiple': False
            },
            'price': {
                'selector': 'div.product_price > p.price_color',
                'type': 'css',
                'attribute': None,
                'multiple': False
            }
        }
    }
}

async def main():
    retry = Retry()
    url = 'https://books.toscrape.com/'
    data = await retry.scrape(url, rules)
    output = retry.output(data, format_type='json')
    print(output)

# Run the async main function
if __name__ == '__main__':
    asyncio.run(main())
