import asyncio
from retry import Retry
from retry.logger import logger

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


async def scrape_book_details(scraper, book):
    detail_url = book['detail_url']
    detail_rules = {
        'description': {
            'selector': '#product_description ~ p',
            'type': 'css',
        },
        'keywords': {
            'extractor_type': 'nlp',
            'nlp_task': 'keywords',
            'text_source': 'description',
        }
    }
    try:
        detail_data = await scraper.scrape(detail_url, detail_rules)
        book.update(detail_data)
    except Exception as e:
        logger.error(f"Error scraping details for {detail_url}: {e}")

async def main():
    scraper = Retry()
    all_books = []
    total_pages = 50  # Total number of pages

    for page in range(1, total_pages + 1):
        url = f'https://books.toscrape.com/catalogue/page-{page}.html'
        try:
            page_data = await scraper.scrape(url, rules)
            books = page_data.get('books', [])
            tasks = []

            for book in books:
                tasks.append(scrape_book_details(scraper, book))

            await asyncio.gather(*tasks)
            all_books.extend(books)
            print(f"Scraped page {page}")
        except Exception as e:
            logger.error(f"Error scraping page {page}: {e}")

    # Output the results
    for book in all_books:
        print(f"Title: {book['title']}")
        print(f"Price: {book['price']}")
        print(f"Rating: {book['rating']}")
        print(f"Availability: {book['availability']}")
        print(f"Keywords: {', '.join(book.get('keywords', []))}")
        print("-" * 40)

if __name__ == '__main__':
    asyncio.run(main())
