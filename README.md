# retry

**retry** is an advanced web scraping library built in Python, designed to make data extraction effortless and efficient. It leverages asynchronous programming with `asyncio` and `aiohttp` for high-performance networking and integrates powerful Natural Language Processing (NLP) capabilities using `spaCy` and other NLP libraries.

## 🚀 What's New

The library has been completely redesigned and improved with:

- **Enhanced Architecture**: More modular and extensible design
- **Improved Error Handling**: Comprehensive custom exceptions
- **Advanced NLP Capabilities**: Dedicated modules for entity extraction, keyword extraction, sentiment analysis, and text summarization
- **Better Documentation**: Comprehensive docstrings and improved README
- **Proxy Management**: Advanced proxy rotation and health checking
- **Rate Limiting**: Domain-specific rate limits with exponential backoff
- **Caching System**: Flexible caching with TTL support and multiple backends
- **Authentication**: Support for various authentication methods

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
  - [Defining Extraction Rules](#defining-extraction-rules)
  - [Scraping Data](#scraping-data)
  - [NLP Capabilities](#nlp-capabilities)
  - [Customizing the Pipeline](#customizing-the-pipeline)
- [Examples](#examples)
- [Advanced Topics](#advanced-topics)
  - [Custom Fetchers](#custom-fetchers)
  - [Plugins](#plugins)
  - [Handling Different Content Types](#handling-different-content-types)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

## Features

- **Asynchronous Networking**: Built on `asyncio` and `aiohttp` for efficient HTTP requests.
- **Dynamic Extraction Rules**: Use CSS selectors, XPath expressions, and regex patterns to extract data.
- **Advanced NLP Integration**: Incorporate `spaCy`, `TextBlob`, and `Transformers` for tasks like NER, sentiment analysis, and keyword extraction.
- **Flexible Pipeline**: Customize the scraping pipeline with your own fetchers, parsers, extractors, and cleaners.
- **Data Cleaning and Normalization**: Remove unwanted content, eliminate redundancies, and normalize text using NLP techniques.
- **Extensible Architecture**: Easily add plugins and extend functionalities to suit your specific needs.
- **Support for Multiple Content Types**: Handle HTML, JSON, and other content types seamlessly.
- **Proxy Rotation**: Built-in support for proxy rotation and management to avoid IP bans.
- **Rate Limiting**: Configurable rate limiting with domain-specific settings and exponential backoff.
- **Caching**: Flexible caching system with TTL support and multiple backend options.
- **Authentication**: Support for various authentication methods including Basic, Form, and Token-based authentication.
- **Error Handling**: Comprehensive error handling with custom exceptions for better debugging.

## Installation

**Requirements**:

- Python 3.7 or higher

**Install from PyPI**:

```bash
pip install retry-scraper
```

**Install from Source**:

```bash
git clone https://github.com/yonatan-levin/retry
cd retry
pip install -e .
```

**Install Required spaCy Model**:

```bash
python -m spacy download en_core_web_sm
```

**Install Playwright (Optional)**:

```bash
playwright install
```

## Quick Start

Here's a quick example to get you started:

```python
import asyncio
from retry import RetrySC

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
    'keywords': {
        'extractor_type': 'nlp',
        'nlp_task': 'keywords',
    },
}

async def main():
    url = 'https://example.com/article'
    scraper = RetrySC()
    data = await scraper.scrape(url, rules)
    print(scraper.output(data, format_type='json'))

if __name__ == '__main__':
    asyncio.run(main())
```

## Usage

### Defining Extraction Rules

Extraction rules are dictionaries that define how to extract data from the fetched content. Each rule can specify:

- **selector**: The CSS or XPath selector to locate elements.
- **type**: The selector type (css, xpath, or jsonpath).
- **attribute**: The attribute to extract from the element (e.g., href).
- **regex**: A regex pattern to apply to the extracted value.
- **multiple**: Boolean indicating whether to extract multiple elements.
- **processor**: A custom function to process the extracted value.
- **extractor_type**: Set to 'nlp' for NLP tasks.
- **nlp_task**: The NLP task to perform (e.g., ner, keywords, sentiment, summary).
- **entity_type**: For NER, specify the entity type (e.g., PERSON, ORG).

### Scraping Data

To scrape data, create an instance of `RetrySC` and call the `scrape` method with the URL and extraction rules:

```python
scraper = RetrySC()
data = await scraper.scrape(url, rules)
```

For multiple URLs:

```python
urls = ['https://example.com/page1', 'https://example.com/page2']
data = await scraper.scrape_multiple(urls, rules)
```

For paginated content:

```python
from retry.utils.pagination import PaginationHandler

pagination_handler = PaginationHandler(
    selector='.next-page',
    selector_type='css',
    attribute='href',
    limit=5
)

data = await scraper.scrape_with_pagination(url, rules, pagination_handler)
```

### NLP Capabilities

retry integrates NLP tasks using spaCy and other libraries:

- **Named Entity Recognition (NER)**: Extract entities like people, organizations, and locations.
- **Keyword Extraction**: Identify important words in the text.
- **Sentiment Analysis**: Determine the sentiment polarity of the content.
- **Text Summarization**: Generate summaries of longer texts.

Example Rule for NER:

```python
'entities': {
    'extractor_type': 'nlp',
    'nlp_task': 'ner',
    'entity_type': 'PERSON',
}
```

Using the NLP modules directly:

```python
from retry.nlp import EntityExtractor, KeywordExtractor, SentimentAnalyzer, TextSummarizer

# Extract entities
entity_extractor = EntityExtractor()
entities = entity_extractor.extract_people(text)

# Extract keywords
keyword_extractor = KeywordExtractor()
keywords = keyword_extractor.extract_keywords_with_scores(text)

# Analyze sentiment
sentiment_analyzer = SentimentAnalyzer()
sentiment = sentiment_analyzer.analyze_sentiment(text)

# Summarize text
text_summarizer = TextSummarizer()
summary = text_summarizer.summarize(text, ratio=0.2)
```

### Customizing the Pipeline

You can customize the scraping pipeline by modifying the `RetrySC` instance's components or pipeline steps:

```python
# Add a custom pipeline step
async def custom_step(context):
    # Process the context
    print(f"Processing URL: {context['url']}")
    return context

scraper.add_pipeline_step("custom_step", custom_step, position=2)

# Remove a pipeline step
scraper.remove_pipeline_step("clean_data")

# Enable/disable a pipeline step
scraper.enable_pipeline_step("apply_plugins", False)
```

## Examples

### Example: Extracting Article Data with NLP

```python
import asyncio
from retry import RetrySC

rules = {
    'title': {'selector': 'h1', 'type': 'css'},
    'author': {'selector': 'span.author-name', 'type': 'css'},
    'publish_date': {'selector': 'time.publish-date', 'type': 'css', 'attribute': 'datetime'},
    'content': {'selector': 'div.article-body', 'type': 'css'},
    'entities': {
        'extractor_type': 'nlp',
        'nlp_task': 'ner',
    },
    'summary': {
        'extractor_type': 'nlp',
        'nlp_task': 'summary',
    },
}

async def main():
    url = 'https://example.com/news/article'
    scraper = RetrySC()
    data = await scraper.scrape(url, rules)
    print(scraper.output(data, format_type='json'))

if __name__ == '__main__':
    asyncio.run(main())
```

### Example: Scraping JSON Data from an API

```python
import asyncio
from retry import RetrySC

rules = {
    'company_name': {'selector': 'companyInfo.companyName', 'type': 'jsonpath'},
    'cik': {'selector': 'companyInfo.cik', 'type': 'jsonpath'},
    'filings': {'selector': 'filings.recent', 'type': 'jsonpath', 'multiple': True},
}

async def main():
    url = 'https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json'
    scraper = RetrySC()
    data = await scraper.scrape(url, rules)
    print(scraper.output(data, format_type='json'))

if __name__ == '__main__':
    asyncio.run(main())
```

## Advanced Topics

### Custom Fetchers

You can implement custom fetchers to control how content is fetched:

```python
from retry.core.fetcher import Fetcher

class CustomFetcher(Fetcher):
    async def fetch(self, url, retries=3, timeout=10):
        # Custom fetch logic
        # ...
        return content, content_type

scraper = RetrySC(fetcher=CustomFetcher())
```

### Plugins

Extend functionality by creating plugins that process data after extraction:

```python
class SentimentPlugin:
    def process(self, data):
        from retry.nlp import SentimentAnalyzer
        
        sentiment_analyzer = SentimentAnalyzer()
        
        if 'content' in data:
            data['sentiment'] = sentiment_analyzer.analyze_sentiment(data['content'])
        
        return data

scraper = RetrySC()
scraper.register_plugin(SentimentPlugin())
```

### Handling Different Content Types

retry can handle HTML, JSON, and other content types. It automatically detects the content type from the Content-Type header:

```python
# HTML content
html_rules = {
    'title': {'selector': 'h1', 'type': 'css'},
}

# JSON content
json_rules = {
    'name': {'selector': 'user.name', 'type': 'jsonpath'},
}

# XML content
xml_rules = {
    'title': {'selector': '//title', 'type': 'xpath'},
}
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

Yonatan Levin - levinjonatan80@gmail.com

Project Link: [https://github.com/yonatan-levin/retry](https://github.com/yonatan-levin/retry)
