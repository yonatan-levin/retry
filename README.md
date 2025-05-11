# HoneyGraber

A high-performance, asynchronous web scraping framework with built-in NLP and extensible architecture.

---

## Key Features

- **Asynchronous Networking**: Leverages `asyncio` and `aiohttp` for fast, non-blocking HTTP requests.
- **Dynamic Extraction Rules**: Define CSS, XPath, or JSONPath rules, with optional regex filtering and custom processors.
- **Advanced NLP Integration**: Native support for Named Entity Recognition, keyword extraction, sentiment analysis, and text summarization via spaCy and TextBlob.
- **Proxy Management & Rate Limiting**: Built-in proxy rotation, domain-specific rate limits, and exponential backoff.
- **Flexible Caching**: Multiple backends (in-memory, file-based) with TTL support to reduce duplicate requests.
- **Authentication Support**: Basic, token-based, form and OAuth2 authentication via a unified `AuthManager` interface.
- **Extensible Pipeline & Plugins**: Customize or extend each step (fetch, parse, extract, clean, plugins).
- **Multiple Content Types**: HTML, JSON, and XML scraping with unified API.
- **Structured Output**: JSON, CSV, and XML formatting with optional data restructuring.

---

## Installation

```bash
pip install honeygraber
```

> **Note:** Requires Python 3.7+ and a spaCy model for NLP tasks:

```bash
python -m spacy download en_core_web_sm
```

(Optional) For Playwright-based rendering:

```bash
pip install playwright
playwright install
```

---

## Quick Start

### Basic Usage

```python
import asyncio
from honeygrabber import HoneyGrabberSC

rules = {
    'title':   {'selector': 'h1',                   'type': 'css'},
    'author':  {'selector': 'span.author-name',     'type': 'css'},
    'keywords':{'extractor_type': 'nlp',            'nlp_task': 'keywords'},
}

async def main():
    url = 'https://example.com/article'
    scraper = HoneyGrabberSC()
    data = await scraper.scrape(url, rules)
    print(scraper.output(data, format_type='json'))

if __name__ == '__main__':
    asyncio.run(main())
```

### Advanced Usage

```python
import asyncio
from honeygrabber import HoneyGrabberSC

# Define extraction rules for an online book page
rules = {
    'title':   {'selector': 'article.product_page h1',   'type': 'css'},
    'description':{
        'selector': 'div#product_description + p',        'type': 'css', 'multiple': True},
    'entities':{'extractor_type': 'nlp',                'nlp_task': 'ner'},
    'sentiment':{'extractor_type': 'nlp',               'nlp_task': 'sentiment'},
}

async def main():
    url = 'https://books.toscrape.com/catalogue/sharp-objects_997/index.html'
    scraper = HoneyGrabberSC()
    data = await scraper.scrape(url, rules)
    # Disable automatic restructuring when the data contains mixed types
    print(scraper.output(data, format_type='json', structure_data=False))

if __name__ == '__main__':
    asyncio.run(main())
```

---

## Examples

See the `examples/` directory for more usage patterns:

- **basic_usage.py** — Simple HTML scraping.
- **advanced_usage.py** — Mixed content with NLP tasks.
- **scrape_books.py** — Bulk scraping and CSV export.
- **authentication_examples.py** — Demonstrates Basic, Token, Form, and OAuth2 flows.
- **custom_fetcher.py** — Custom fetcher implementation.

---

## Advanced Topics

- ### Custom Fetchers
  Inherit from `Fetcher` to implement custom request logic.

- ### Pagination
  Use `PaginationHandler` to iterate through multi-page listings.

- ### Plugins
  Register post-processing steps via `scraper.register_plugin()`.

- ### Authentication
  Unified interface via `AuthManager` to handle credentials and token refresh.

---

## Contributing

We welcome contributions! Please fork the repo, create a feature branch, and open a pull request with clear descriptions.

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/awesome`
3. Commit your changes: `git commit -m "Add awesome feature"`
4. Push to your branch: `git push origin feature/awesome`
5. Open a Pull Request

Please adhere to existing coding standards and include unit tests for new functionality.

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

## Contact

Yonatan Levin  •  levinjonatan80@gmail.com  •  [GitHub/@yonatan-levin](https://github.com/yonatan-levin)
