import asyncio
from retry import Retry
from retry.logger import getLogger

logger = getLogger(__name__)

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


async def scrape_book_details(scraper: Retry, book):
    detail_urls = book['detail_url']
    detail_rules = {
        "books_detail": {
            'fields': {
                'description': {
                    'selector': '#product_description ~ p',
                    'type': 'css',
                },
                'keywords': {
                    'extractor_type': 'nlp',
                    'text_source': 'selector',
                    'selector': '#product_description ~ p',
                    'nlp_task': 'keywords',
                    'type': 'css'
                }
            }}}
    try:
        books_detail = await scraper.scrape_multiple(urls=detail_urls, rules=detail_rules, fetch_method='fetch_multiple')
        book['books_detail'] = books_detail

    except Exception as e:
        logger.error(f"Error scraping details for {detail_urls}: {e}")


async def main():
    scraper = Retry()
    all_books = []
    total_pages = 50  # Total number of pages

    for page in range(1, total_pages + 1):
        url = f'https://books.toscrape.com/catalogue/page-{page}.html'
        try:
            page_data = await scraper.scrape(url, rules)
            books = page_data.get('books', [])

            await scrape_book_details(scraper, books)

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
