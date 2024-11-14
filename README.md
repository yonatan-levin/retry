# Retry

**Retry** is an advanced web scraping library built in Python, designed to make data extraction effortless and efficient. It leverages asynchronous programming with `asyncio` and `aiohttp` for high-performance networking and integrates powerful Natural Language Processing (NLP) capabilities using `spaCy` and other NLP libraries.

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
- **Advanced NLP Integration**: Incorporate `spaCy`, `TextBlob`, `Gensim`, and `Transformers` for tasks like NER, sentiment analysis and keyword extraction.
- **Flexible Pipeline**: Customize the scraping pipeline with your own fetchers, parsers, extractors, and cleaners.
- **Data Cleaning and Normalization**: Remove unwanted content, eliminate redundancies, and normalize text using NLP techniques.
- **Extensible Architecture**: Easily add plugins and extend functionalities to suit your specific needs.
- **Support for Multiple Content Types**: Handle HTML, JSON, and other content types seamlessly.

## Installation

**Requirements**:

- Python 3.7 or higher

**Install from PyPI**:

*Note: Replace `retry` with the actual package name once published to PyPI.*

```bash
pip install retry
```

Install from Source:

```bash
git clone https://github.com/yonatan-levin/retry
cd retry
pip install -e .
```

Install Required spaCy Model:

```bash
python -m spacy download en_core_web_sm
```

In order to fetch with playwright you need to install playwright:

```bash
playwright install
```

## Quick Start

Here's a quick example to get you started:

```python
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
    'keywords': {
        'extractor_type': 'nlp',
        'nlp_task': 'keywords',
    },
}

async def main():
    url = 'https://example.com/article'
    scraper = Retry()
    data = await scraper.scrape(url, rules)
    print(scraper.output(data, format_type='json'))

if __name__ == '__main__':
    asyncio.run(main())
```

# Usage
Defining Extraction Rules

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

Scraping Data

To scrape data, create an instance of Retry and call the scrape method with the URL and extraction rules.

```python
scraper = Retry()
data = await scraper.scrape(url, rules)
```
## NLP Capabilities

Retry integrates NLP tasks using spaCy and other libraries.

- **Named Entity** Recognition (NER): Extract entities like people, organizations, and locations.
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
## Customizing the Pipeline

You can customize the scraping pipeline by modifying the Retry instance's components or pipeline steps.

Custom Fetcher:

```python
from retry.fetcher import BaseFetcher

class CustomFetcher(BaseFetcher):
    async def fetch(self, url, retries=3):
        # Implement custom fetching logic
        pass

scraper = Retry(fetcher=CustomFetcher())
```
Modifying the Pipeline:

```python
# Remove the cleaning step
scraper.pipeline.remove(scraper._clean_data)
```
# Examples
## Example: Extracting Article Data with NLP

```python
import asyncio
from retry import Retry

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
    scraper = Retry()
    data = await scraper.scrape(url, rules)
    print(scraper.output(data, format_type='json'))

if __name__ == '__main__':
    asyncio.run(main())
```
## Example: Scraping JSON Data from an API

```python
import asyncio
from retry import Retry

rules = {
    'company_name': {'selector': 'companyInfo.companyName', 'type': 'jsonpath'},
    'cik': {'selector': 'companyInfo.cik', 'type': 'jsonpath'},
    'filings': {'selector': 'filings.recent', 'type': 'jsonpath', 'multiple': True},
}

async def main():
    url = 'https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json'
    scraper = Retry()
    data = await scraper.scrape(url, rules)
    print(scraper.output(data, format_type='json'))

if __name__ == '__main__':
    asyncio.run(main())
```
# Advanced Usage
## Custom Fetchers

You can implement custom fetchers to control how content is fetched.

```python
from retry.fetcher import BaseFetcher

class CustomFetcher(BaseFetcher):
    async def fetch(self, url, retries=3):
        # Custom fetch logic
        pass

scraper = Retry(fetcher=CustomFetcher())
```
## Plugins

Extend functionality by creating plugins that process data after extraction.

```python
class SentimentPlugin:
    def process(self, data):
        from textblob import TextBlob
        if 'content' in data:
            blob = TextBlob(data['content'])
            data['sentiment'] = blob.sentiment.polarity
        return data

scraper.register_plugin(SentimentPlugin())
```
## Handling Different Content Types

Retry can handle HTML, JSON, and other content types. It automatically detects the content type from the Content-Type header.

Example for JSON Content:

``` python
rules = {
    'data_point': {'selector': 'path.to.data', 'type': 'jsonpath'},
}
``` 
Contributing

Contributions are welcome! Please follow these steps:

Fork the repository.

Create a new branch:

```bash
git checkout -b feature/your-feature
```
Commit your changes:

```bash
git commit -am 'Add new feature'
```
Push to the branch:

```bash
    git push origin feature/your-feature

    Open a Pull Request.
```
Please ensure that your code adheres to the project's coding standards and includes appropriate tests.
License

This project is licensed under the MIT License. See the LICENSE file for details.
Contact

For questions or suggestions, feel free to reach out:

 
    GitHub: https://github.com/yonatan-levin/retry

Thank you for using Retry! We hope it makes your web scraping and data extraction tasks easier and more efficient.
