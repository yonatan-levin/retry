import asyncio
import time
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
                    'text_source': 'dependent',
                    'dependent_item': 'description',
                    'nlp_task': 'keywords',
                    'type': 'css'
                }
            }}}
    try:
        books_detail = await scraper.scrape_multiple(urls=detail_urls, rules=detail_rules, fetch_method='fetch_multiple')
        book['books_detail'] = books_detail

    except Exception as e:
        logger.error(f"Error scraping details for {detail_urls}: {e}")

def extend_book_list(source_data: dict, target_data: dict, page: str) -> dict:
    if page not in target_data:
        target_data[page] = {}
    for key,value in source_data.items():
        target_data[page][key] = value
    return target_data

async def main():
    scraper = Retry()
    all_books = {}
    total_pages = 2  # Total number of pages
    start_time = time.time()
    for page in range(1, total_pages + 1):
        url = f'https://books.toscrape.com/catalogue/page-{page}.html'
        try:
            page_data = await scraper.scrape(url, rules)
            books = page_data.get('books', [])

            await scrape_book_details(scraper, books)

            extend_book_list(books,all_books,str(page))
            print(f"Scraped page {page}")
        except Exception as e:
            logger.error(f"Error scraping page {page}: {e}")

    # Output the results
    out = scraper.output(all_books, 'json')
    print(out)
    with open("data.json", "w") as outfile:
        outfile.write(out)
        
    end_time = time.time()

    elapsed_time = end_time - start_time
    print(f"Elapsed time: {elapsed_time} seconds")

if __name__ == '__main__':
    asyncio.run(main())
