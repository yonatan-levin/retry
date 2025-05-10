HoneyGraber
==========

**HoneyGraber** is an advanced web scraping library built in Python, designed to make data extraction effortless and efficient. Like the tenacious honey badger, it fearlessly extracts data from any source with determination and precision. It leverages asynchronous programming with ``asyncio`` and ``aiohttp`` for high-performance networking and integrates powerful Natural Language Processing (NLP) capabilities using ``spaCy`` and other NLP libraries.

What's New
---------

The library has been completely redesigned and improved with:

* **Enhanced Architecture**: More modular and extensible design
* **Improved Error Handling**: Comprehensive custom exceptions
* **Advanced NLP Capabilities**: Dedicated modules for entity extraction, keyword extraction, sentiment analysis, and text summarization
* **Proxy Management**: Advanced proxy rotation and health checking
* **Rate Limiting**: Domain-specific rate limits with exponential backoff
* **Caching System**: Flexible caching with TTL support and multiple backends
* **Authentication**: Support for various authentication methods

Features
--------

* **Dynamic Extraction Rules**: Use CSS selectors, XPath expressions, and regex patterns to extract data.
* **Advanced NLP Integration**: Incorporate ``spaCy``, ``TextBlob``, and ``Transformers`` for tasks like NER, sentiment analysis, and keyword extraction.
* **Flexible Pipeline**: Customize the scraping pipeline with your own fetchers, parsers, extractors, and cleaners.
* **Data Cleaning and Normalization**: Remove unwanted content, eliminate redundancies, and normalize text using NLP techniques.
* **Extensible Architecture**: Easily add plugins and extend functionalities to suit your specific needs.
* **Support for Multiple Content Types**: Handle HTML, JSON, and other content types seamlessly.
* **Proxy Rotation**: Built-in support for proxy rotation and management to avoid IP bans.
* **Rate Limiting**: Configurable rate limiting with domain-specific settings and exponential backoff.
* **Caching**: Flexible caching system with TTL support and multiple backend options.
* **Authentication**: Support for various authentication methods including Basic, Form, and Token-based authentication.
* **Error Handling**: Comprehensive error handling with custom exceptions for better debugging.

Installation
-----------

**Requirements**:

* Python 3.7 or higher

**Install from PyPI**:

.. code-block:: bash

    pip install honeygraber

**Install from Source**:

.. code-block:: bash

    git clone https://github.com/yonatan-levin/honeygraber
    cd honeygraber
    pip install -e .

**Install Required spaCy Model**:

.. code-block:: bash

    python -m spacy download en_core_web_sm

**Install Playwright (Optional)**:

.. code-block:: bash

    playwright install

Quick Start
----------

Here's a quick example to get you started:

.. code-block:: python

    import asyncio
    from honeygraber import RetrySC

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

Usage
-----

Defining Extraction Rules
~~~~~~~~~~~~~~~~~~~~~~~~~

Extraction rules are dictionaries that define how to extract data from the fetched content. Each rule can specify:

* **selector**: The CSS or XPath selector to locate elements.
* **type**: The selector type (css, xpath, or jsonpath).
* **attribute**: The attribute to extract from the element (e.g., href).
* **regex**: A regex pattern to apply to the extracted value.
* **multiple**: Boolean indicating whether to extract multiple elements.
* **processor**: A custom function to process the extracted value.
* **extractor_type**: Set to 'nlp' for NLP tasks.
* **nlp_task**: The NLP task to perform (e.g., ner, keywords, sentiment, summary).
* **entity_type**: For NER, specify the entity type (e.g., PERSON, ORG).

Scraping Data
~~~~~~~~~~~~

To scrape data, create an instance of ``RetrySC`` and call the ``scrape`` method with the URL and extraction rules:

.. code-block:: python

    scraper = RetrySC()
    data = await scraper.scrape(url, rules)

For multiple URLs:

.. code-block:: python

    urls = ['https://example.com/page1', 'https://example.com/page2']
    data = await scraper.scrape_multiple(urls, rules)

For more information and examples, visit the `project repository <https://github.com/yonatan-levin/honeygraber>`_. 