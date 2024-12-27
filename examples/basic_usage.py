"""
This script scrapes book information from 'https://books.toscrape.com/' using specified extraction rules.

Extraction Rules:
- The 'rules' dictionary defines how to extract data from the webpage using CSS selectors.

- 'books':
  - 'selector': 'article.product_pod'
    - Selects each book element on the page.
  - 'type': 'css'
    - Specifies that the selector is a CSS selector.
  - 'multiple': True
    - Indicates that multiple elements should be selected.
  - 'fields':
    - 'title':
      - 'selector': 'h3 > a'
        - Selects the anchor tag within the header of each book element.
      - 'attribute': 'title'
        - Extracts the 'title' attribute from the anchor tag.
      - 'multiple': False
        - Only one title per book.
    - 'price':
      - 'selector': 'div.product_price > p.price_color'
        - Selects the price paragraph within the product price division.
      - 'attribute': None
        - Extracts the content based on an attribute if given.
      - 'multiple': False
        - first item only

Expected Output:
- The script outputs JSON data containing a list of books with their titles and prices.
- Example:

{
  "books": [
    {
      "title": "A Light in the Attic",
      "price": "£51.77"
    }
  ]
}
"""
import asyncio
from retry import Retry

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
#docstring the expected output

async def main():
    retry = Retry()
    url = 'https://books.toscrape.com/'
    data = await retry.scrape(url, rules)
    output = retry.output(data, format_type='json')
    print(output)

if __name__ == '__main__':
    asyncio.run(main())
