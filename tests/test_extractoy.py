from pydantic import ValidationError
import pytest
from unittest.mock import MagicMock, patch
from retry.parser import ContentParser
from retry.extractor import ContentExtractor
import spacy


@pytest.fixture
def sample_html_content():
    return """
    <html>
        <head><title>Test Page</title></head>
        <body>
            <div id="main">
                <h1 class="title">Hello World</h1>
                <p class="content">This is a <strong>test</strong> page.</p>
                <ul>
                    <li><a href="/link1">Link 1</a></li>
                    <li><a href="/link2">Link 2</a></li>
                    <li><a href="/link3">Link 3</a></li>
                </ul>
            </div>
            <p class="author">By John Doe</p>
            <p class="date">Published on 2021-01-01</p>
        </body>
    </html>
    """


@pytest.fixture
def sample_html_content_2():
    return """
    <p>It's hard to imagine a world without A Light in the Attic. This now-classic collection of poetry and drawings from Shel Silverstein celebrates its 20th anniversary with this special edition. Silverstein's humorous and creative verse can amuse the dowdiest of readers. Lemon-faced adults and fidgety kids sit still and read these rhythmic words and laugh and smile and love th It's hard to imagine a world without A Light in the Attic. This now-classic collection of poetry and drawings from Shel Silverstein celebrates its 20th anniversary with this special edition. Silverstein's humorous and creative verse can amuse the dowdiest of readers. Lemon-faced adults and fidgety kids sit still and read these rhythmic words and laugh and smile and love that Silverstein. Need proof of his genius? RockabyeRockabye baby, in the treetopDon't you know a treetopIs no safe place to rock?And who put you up there,And your cradle, too?Baby, I think someone down here'sGot it in for you. Shel, you never sounded so good. ...more</p>
    """


@pytest.fixture
def sample_text_content():
    return "Apple is looking at buying U.K. startup for $1 billion. This is great news!"


@pytest.fixture
def sample_json_content():
    return {
        "items": [
            {"name": "Item 1", "price": 10},
            {"name": "Item 2", "price": 20},
            {"name": "Item 3", "price": 30}
        ]
    }


@pytest.fixture
def logger():
    with patch.object('retry.extractor.logger', 'error', MagicMock()) as mock_logger:
        yield mock_logger


@pytest.fixture
def parser(sample_html_content):
    parser = ContentParser(sample_html_content, content_type='text/html')
    return parser


@pytest.fixture
def parser_2(sample_html_content_2):
    parser = ContentParser(sample_html_content_2, content_type='text/html')
    return parser


@pytest.fixture
def parser_json(sample_json_content):
    parser = ContentParser(sample_json_content,
                           content_type='application/json')
    return parser


@pytest.fixture
def nlp():
    # Load the small English model
    return spacy.load('en_core_web_sm')


def test_extract_default(parser):
    rules = {
        'title': {
            'selector': 'h1.title',
            'type': 'css',
            'attribute': None,
            'regex': None,
            'multiple': False
        },
        'links': {
            'selector': 'ul li a',
            'type': 'css',
            'attribute': 'href',
            'multiple': True
        }
    }
    extractor = ContentExtractor(parser, rules)
    data = extractor.extract()
    assert data['title'] == 'Hello World'
    assert data['links'] == ['/link1', '/link2', '/link3']


def test_extract_with_regex(parser):
    rules = {
        'first_link_number': {
            'selector': 'ul li a',
            'type': 'css',
            'attribute': 'href',
            'regex': r'/link(\d)',
            'multiple': False
        }
    }
    extractor = ContentExtractor(parser, rules)
    data = extractor.extract()
    assert data['first_link_number'] == '1'


def test_extract_attribute(parser):
    rules = {
        'main_div_id': {
            'selector': 'div#main',
            'type': 'css',
            'attribute': 'id',
            'multiple': False
        }
    }
    extractor = ContentExtractor(parser, rules)
    data = extractor.extract()
    assert data['main_div_id'] == 'main'


def test_extract_multiple(parser):
    rules = {
        'link_texts': {
            'selector': '//ul/li/a',
            'type': 'xpath',
            'attribute': None,
            'multiple': True
        }
    }
    extractor = ContentExtractor(parser, rules)
    data = extractor.extract()

    assert data['link_texts'] == ['Link 1', 'Link 2', 'Link 3']


def test_extract_nlp_ner(sample_text_content):
    # Mock the parser to return sample_text_content
    parser = MagicMock()
    parser.parsed_content.get_text.return_value = sample_text_content
    rules = {
        'entities': {
            'extractor_type': 'nlp',
            'text_source': 'content',
            'nlp_task': 'ner',
            'entity_type': None  # Get all entities
        }
    }
    extractor = ContentExtractor(parser, rules)
    data = extractor.extract()
    # Expected entities: 'Apple', 'U.K.', '$1 billion'
    assert 'entities' in data
    assert data['entities'] == ['Apple', 'U.K.', '$1 billion']


def test_extract_nlp_keywords(sample_text_content):
    parser = MagicMock()
    parser.parsed_content.get_text.return_value = sample_text_content
    rules = {
        'keywords': {
            'extractor_type': 'nlp',
            'nlp_task': 'keywords'
        }
    }
    extractor = ContentExtractor(parser, rules)
    data = extractor.extract()
    assert 'keywords' in data
    # TextBlob's keyword extraction is not deterministic, check for common expected keywords
    # but don't be too strict about exact matches
    assert len(data['keywords']) > 0
    assert 'Apple' in data['keywords']  # This should always be extracted as a proper noun


def test_extract_nlp_sentiment(sample_text_content):
    parser = MagicMock()
    parser.parsed_content.get_text.return_value = sample_text_content
    rules = {
        'sentiment': {
            'extractor_type': 'nlp',
            'nlp_task': 'sentiment'
        }
    }
    extractor = ContentExtractor(parser, rules)
    data = extractor.extract()
    assert 'sentiment' in data
    sentiment_data = data['sentiment']
    assert sentiment_data['sentiment'] == 'Positive'
    assert -1.0 <= sentiment_data['polarity'] <= 1.0
    assert 0.0 <= sentiment_data['subjectivity'] <= 1.0


def test_extract_with_processor(parser):
    def uppercase_processor(value):
        return value.upper()

    rules = {
        'title_upper': {
            'selector': 'h1.title',
            'type': 'css',
            'processor': uppercase_processor
        }
    }
    extractor = ContentExtractor(parser, rules)
    data = extractor.extract()
    assert data['title_upper'] == 'HELLO WORLD'


def test_extract_json_content():
    sample_json_content = {
        "items": [
            {"name": "Item 1", "price": 10},
            {"name": "Item 2", "price": 20},
            {"name": "Item 3", "price": 30}
        ]
    }
    parser = MagicMock()
    parser.select_json.return_value = sample_json_content['items']
    rules = {
        'item_names': {
            'selector': 'items',
            'type': 'json',
            'attribute': 'name',
            'multiple': True
        }
    }
    extractor = ContentExtractor(parser, rules)
    data = extractor.extract()
    assert data['item_names'] == ['Item 1', 'Item 2', 'Item 3']


def test_extract_with_match_patterns(sample_text_content):
    parser = MagicMock()
    parser.parsed_content.get_text.return_value = sample_text_content
    match_patterns = {
        'MONEY': [[{'IS_CURRENCY': True}, {'LIKE_NUM': True}, {'LOWER': 'billion'}]]
    }
    rules = {
        'money_mentions': {
            'extractor_type': 'nlp',
            'nlp_task': 'match_patterns'
        }
    }
    extractor = ContentExtractor(parser, rules, match_patterns=match_patterns)
    data = extractor.extract()
    assert 'money_mentions' in data
    assert data['money_mentions'] == {'MONEY': ['$1 billion']}


def test_extract_invalid_selector_type(parser):
    rules = {
        'invalid_selector': {
            'selector': 'h1.title',
            'type': 'invalid',
            'attribute': None,
            'multiple': False
        }
    }
    extractor = ContentExtractor(parser, rules)
    with patch('retry.extractor.logger') as mock_logger:
        value = extractor.extract()

        # Assert that the value is None due to the exception
        assert value['invalid_selector'] is None

        # Assert that logger.error was called with the expected message
        mock_logger.error.assert_called()
        args, kwargs = mock_logger.error.call_args
        assert 'Error extracting data' in args[0]
        assert 'invalid' in args[0]


def test_extract_missing_selector(parser):
    rules = {
        'missing_selector': {
            'selector': 'h2.subtitle',
            'type': 'css',
            'attribute': None,
            'multiple': False
        }
    }
    extractor = ContentExtractor(parser, rules)
    data = extractor.extract()
    assert data['missing_selector'] is None


def test_extract_nlp_unknown_task(parser, sample_text_content):
    # Mock the parser to return sample_text_content
    parser = MagicMock()
    parser.parsed_content.get_text.return_value = sample_text_content
    rules = {
        'unknown_task': {
            'extractor_type': 'nlp',
            'nlp_task': 'unknown'
        }
    }
    with pytest.raises(ValidationError):
        extractor = ContentExtractor(parser, rules)
        extractor.extract()


def test_extract_nlp_entity_type(sample_text_content):
    parser = MagicMock()
    parser.parsed_content.get_text.return_value = sample_text_content
    rules = {
        'organizations': {
            'extractor_type': 'nlp',
            'nlp_task': 'ner',
            'entity_type': 'ORG'
        }
    }
    extractor = ContentExtractor(parser, rules)
    data = extractor.extract()
    assert data['organizations'] == ['Apple']


def test_extract_nlp_from_selector(parser):
    rules = {
        'title_sentiment': {
            'extractor_type': 'nlp',
            'nlp_task': 'sentiment',
            'text_source': 'selector',
            'selector': 'h1.title',
            'type': 'css'
        }
    }
    extractor = ContentExtractor(parser, rules)
    data = extractor.extract()
    sentiment_data = data['title_sentiment']
    assert sentiment_data['sentiment'] == 'Neutral'


def test_extract_with_regex_no_match(parser):
    rules = {
        'nonexistent_number': {
            'selector': 'h1.title',
            'type': 'css',
            'regex': r'\d+',
            'multiple': False
        }
    }
    extractor = ContentExtractor(parser, rules)
    data = extractor.extract()
    assert data['nonexistent_number'] is None


def test_extract_default_with_no_elements(parser):
    rules = {
        'no_elements': {
            'selector': 'div.nonexistent',
            'type': 'css',
            'multiple': True
        }
    }
    extractor = ContentExtractor(parser, rules)
    data = extractor.extract()
    assert data['no_elements'] == []


def test_extract_attribute_missing(parser):
    rules = {
        'missing_attribute': {
            'selector': 'h1.title',
            'type': 'css',
            'attribute': 'nonexistent',
            'multiple': False
        }
    }
    extractor = ContentExtractor(parser, rules)
    data = extractor.extract()
    assert data['missing_attribute'] == ''


def test_extract_json_with_regex():
    sample_json_content = {
        "emails": [
            {"email": "user1@example.com"},
            {"email": "user2@example.net"},
            {"email": "user3@example.org"}
        ]
    }
    parser = MagicMock()
    parser.select_json.return_value = sample_json_content['emails']
    rules = {
        'emails': {
            'selector': 'emails',
            'type': 'json',
            'attribute': 'email',
            'regex': r'@(.*)\.',
            'multiple': True
        }
    }
    extractor = ContentExtractor(parser, rules)
    data = extractor.extract()
    assert data['emails'] == ['example', 'example', 'example']


def test_extract_with_custom_matcher(sample_text_content):
    parser = MagicMock()
    parser.parsed_content.get_text.return_value = sample_text_content
    # Define custom match patterns
    match_patterns = {
        'BUYING': [[{'LOWER': 'buying'}]]
    }
    rules = {
        'buying_mentions': {
            'extractor_type': 'nlp',
            'nlp_task': 'match_patterns'
        }
    }
    extractor = ContentExtractor(parser, rules, match_patterns=match_patterns)
    data = extractor.extract()
    assert data['buying_mentions'] == {'BUYING': ['buying']}


def test_extract_with_processor_exception(parser):
    # Define a faulty processor that raises an exception
    def faulty_processor(value):
        raise ValueError("Processor error")

    rules = {
        'faulty_extraction': {
            'selector': 'h1.title',
            'type': 'css',
            'processor': faulty_processor
        }
    }

    extractor = ContentExtractor(parser, rules)

    with patch('retry.extractor.logger') as mock_logger:

        data = extractor.extract()
        # Assert that the value is None due to the exception
        assert data['faulty_extraction'] is None

        # Assert that logger.error was called with the expected message
        mock_logger.error.assert_called()
        args, kwargs = mock_logger.error.call_args
        assert 'Error extracting data' in args[0]
        assert 'Processor error' in args[0]


def test_extract_nlp_sentiment_empty_text():
    parser = MagicMock()
    parser.parsed_content.get_text.return_value = ""
    rules = {
        'sentiment': {
            'extractor_type': 'nlp',
            'nlp_task': 'sentiment'
        }
    }
    extractor = ContentExtractor(parser, rules)
    data = extractor.extract()
    assert data['sentiment'] == {
        "sentiment": "Neutral",
        "polarity": 0.0,
        "subjectivity": 0.0
    }


def test_extract_nlp_match_patterns_no_matches(sample_text_content):
    parser = MagicMock()
    parser.parsed_content.get_text.return_value = sample_text_content
    match_patterns = {
        'NONEXISTENT': [[{'LOWER': 'nonexistent'}]]
    }
    rules = {
        'no_matches': {
            'extractor_type': 'nlp',
            'nlp_task': 'match_patterns'
        }
    }
    extractor = ContentExtractor(parser, rules, match_patterns=match_patterns)
    data = extractor.extract()
    assert data['no_matches'] == {}


def test_extract_default_from_json(parser):
    with patch.object(parser, 'select_json', return_value=[{'name': 'Item 1'}, {'name': 'Item 2'}]):
        parser.select_json.return_value = [
            {'name': 'Item 1'}, {'name': 'Item 2'}]
        rules = {
            'item_names': {
                'selector': 'items',
                'type': 'json',
                'attribute': 'name',
                'multiple': True
            }
        }
        extractor = ContentExtractor(parser, rules)
        data = extractor.extract()
        assert data['item_names'] == ['Item 1', 'Item 2']


def test_nested_rule_object(parser):
    rules = {
        'nested_rule': {
            'selector': 'div#main',
            'type': 'css',
            'fields': {
                'title': {
                    'selector': 'h1.title',
                    'type': 'css',
                },
                'content': {
                    'selector': 'p.content',
                    'type': 'css',
                }
            }
        }
    }
    extractor = ContentExtractor(parser, rules)
    data = extractor.extract()
    assert data['nested_rule'] == {
        'title': 'Hello World',
        'content': 'This is a test page.'
    }


def test_nested_rule_list(parser):
    rules = {
        'nested_rule': {
            'selector': 'div#main',
            'type': 'css',
            'multiple': True,
            'fields': {
                'links': {
                    'selector': 'ul li a',
                    'type': 'css',
                    'attribute': 'href',
                }
            }
        }
    }
    extractor = ContentExtractor(parser, rules)
    data = extractor.extract()
    assert data['nested_rule'] == {
        'links': ['/link1', '/link2', '/link3']
    }


def test_rules_without_fields(parser):
    rules = {
        'main_content': {
            'selector': 'div#main',
            'type': 'css'
            # 'fields' property is intentionally omitted
        }
    }
    extractor = ContentExtractor(parser, rules)
    data = extractor.extract()
    assert 'main_content' in data
    assert 'Hello World' in data['main_content']


def test_extract_first_description_second_nlp(parser_2, sample_html_content_2):
    # Mock the parser so it does not return any text
    parser = MagicMock()
    parser.parsed_content.get_text.return_value = ""

    # Define a rule that specifies a custom text_source
    rules = {
        "books_detail": {
            'fields': {
                'description': {
                    'selector': 'p',
                    'type': 'css',
                },
                'keywords': {
                    'extractor_type': 'nlp',
                    'text_source': 'dependent',
                    'dependent_item': 'description',
                    'nlp_task': 'keywords',
                    'type': 'css',
                    'pos_tags': ['NOUN', 'PROPN','ADJ']
                }
            }}}

    # Initialize the extractor
    extractor = ContentExtractor(parser_2, rules)

    # Extract data
    data = extractor.extract()

    # Assert that the description and keywords are extracted correctly
    assert data['books_detail']['description'] == sample_html_content_2.strip().replace('\n', '').replace('<p>','').replace('</p>','')
    assert 'keywords' in data['books_detail']
    assert 'genius' in data['books_detail']['keywords']
    assert 'Light' in data['books_detail']['keywords']
    assert 'good' in data['books_detail']['keywords']
