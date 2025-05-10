import pytest
import json
import xml.etree.ElementTree as ET
from io import StringIO
import csv
from honeygrabber.formatter import OutputFormatter

@pytest.fixture
def sample_data_dict():
    return {
        "name": "John Doe",
        "age": 30,
        "email": "john.doe@example.com"
    }

@pytest.fixture
def sample_data_dict_list():
    return {
        "title": ['A Light in the Attic', 'Tipping the Velvet', 'Soumission', 'Sharp Objects', 'Sapiens: A Brief History of Humankind', 'The Requiem Red', 'The Dirty Little Secrets of Getting Your Dream Job', 'The Coming Woman: A Novel Based on the Life of the Infamous Feminist, Victoria Woodhull', 'The Boys in the Boat: Nine Americans and Their Epic Quest for Gold at the 1936 Berlin Olympics', 'The Black Maria', 'Starving Hearts (Triangular Trade Trilogy, #1)', "Shakespeare's Sonnets", 'Set Me Free', "Scott Pilgrim's Precious Little Life (Scott Pilgrim #1)", 'Rip it Up and Start Again', 'Our Band Could Be Your Life: Scenes from the American Indie Underground, 1981-1991', 'Olio', 'Mesaerion: The Best Science Fiction Stories 1800-1849', 'Libertarianism for Beginners', "It's Only the Himalayas"],
        "price": ['£51.77', '£53.74', '£50.10', '£47.82', '£54.23', '£22.65', '£33.34', '£17.93', '£22.60', '£52.15', '£13.99', '£20.66', '£17.46', '£52.29', '£35.02', '£57.25', '£23.88', '£37.59', '£51.33', '£45.17']
    }

@pytest.fixture
def sample_data_list():
    return [
        {"name": "John Doe", "age": 30, "email": "john.doe@example.com"},
        {"name": "Jane Smith", "age": 25, "email": "jane.smith@example.com"}
    ]

@pytest.fixture
def nested_data():
    return {
        "person": {
            "name": "John Doe",
            "age": 30,
            "contact": {
                "email": "john.doe@example.com",
                "phone": "555-1234"
            }
        },
        "status": "active"
    }

def test_format_json_dict(sample_data_dict):
    formatter = OutputFormatter()
    result = formatter.format(sample_data_dict, format_type='json')
    expected = json.dumps(sample_data_dict, ensure_ascii=False, indent=2)
    assert result == expected


def test_format_json_list(sample_data_list):
    formatter = OutputFormatter()
    result = formatter.format(sample_data_list, format_type='json')
    expected = json.dumps(sample_data_list, ensure_ascii=False, indent=2)
    assert result == expected

def test_format_json_empty():
    formatter = OutputFormatter()
    result = formatter.format({}, format_type='json')
    expected = json.dumps({}, ensure_ascii=False, indent=2)
    assert result == expected

def test_format_csv_dict(sample_data_dict):
    formatter = OutputFormatter()
    result = formatter.format(sample_data_dict, format_type='csv')
    output = StringIO(result)
    reader = csv.reader(output)
    rows = list(reader)
    assert len(rows) == 2
    assert rows[0] == [str(value) for value in sample_data_dict.keys()]
    assert rows[1] == [str(value) for value in sample_data_dict.values()]

def test_format_csv_list(sample_data_list):
    formatter = OutputFormatter()
    result = formatter.format(sample_data_list, format_type='csv')
    output = StringIO(result)
    reader = csv.reader(output)
    rows = list(reader)
    assert len(rows) == len(sample_data_list) + 1  # +1 for header
    for i, item in enumerate(sample_data_list):
        assert rows[i+1] == [str(value)
                             for value in item.values()]  # +1 to ignore header
    assert rows[0] == [str(value) for value in sample_data_list[0].keys()]

def test_format_csv_empty():
    formatter = OutputFormatter()
    result = formatter.format({}, format_type='csv')
    output = StringIO(result)
    reader = csv.reader(output)
    rows = list(reader)
    assert len(rows) == 0
    assert rows == []

def test_format_xml_dict(sample_data_dict):
    formatter = OutputFormatter()
    result = formatter.format(sample_data_dict, format_type='xml')
    root = ET.fromstring(result)
    for key, value in sample_data_dict.items():
        child = root.find(key)
        assert child is not None
        assert child.text == str(value)

def test_format_xml_nested(nested_data):
    formatter = OutputFormatter()
    result = formatter.format(nested_data, format_type='xml')
    root = ET.fromstring(result)
    person = root.find('person')
    assert person is not None
    name = person.find('name')
    assert name is not None
    assert name.text == 'John Doe'
    contact = person.find('contact')
    assert contact is not None
    email = contact.find('email')
    assert email is not None
    assert email.text == 'john.doe@example.com'

def test_format_unknown_format(sample_data_dict):
    formatter = OutputFormatter()
    with pytest.raises(ValueError) as exc_info:
        formatter.format(sample_data_dict, format_type='unknown')
    assert 'Unknown format type' in str(exc_info.value)

def test_format_csv_with_special_characters():
    data = {"name": "John, Doe", "message": 'He said, "Hello!"'}
    formatter = OutputFormatter()
    result = formatter.format(data, format_type='csv')
    output = StringIO(result)
    reader = csv.reader(output)
    rows = list(reader)
    assert len(rows) == 2
    assert rows[0] == ['name', 'message']
    assert rows[1] == ['John, Doe', 'He said, "Hello!"']

def test_format_json_with_unicode():
    data = {"greeting": "こんにちは", "farewell": "さようなら"}
    formatter = OutputFormatter()
    result = formatter.format(data, format_type='json')
    expected = json.dumps(data, ensure_ascii=False, indent=2)
    assert result == expected

def test_format_xml_with_unicode():
    data = {"greeting": "こんにちは", "farewell": "さようなら"}
    formatter = OutputFormatter()
    result = formatter.format(data, format_type='xml')
    root = ET.fromstring(result)
    greeting = root.find('greeting')
    assert greeting is not None
    assert greeting.text == 'こんにちは'

def test_format_csv_list_with_missing_keys():
    data = [
        {"name": "John Doe", "age": 30},
        {"name": "Jane Smith", "email": "jane.smith@example.com"}
    ]
    formatter = OutputFormatter()
    result = formatter.format(data, format_type='csv')
    # Since dictionaries are unordered, and keys may not be consistent,
    # we need to adjust the test or the formatter to handle headers.

    # Placeholder for test adjustments or enhancements to the formatter.

def test_format_empty_data():
    formatter = OutputFormatter()
    # Test with empty dictionary
    result_json = formatter.format({}, format_type='json')
    assert result_json == json.dumps({}, ensure_ascii=False, indent=2)
    # Test with empty list
    result_json = formatter.format([], format_type='json')
    assert result_json == json.dumps([], ensure_ascii=False, indent=2)
    # Test with empty data for CSV
    result_csv = formatter.format([], format_type='csv')
    assert result_csv == ''
    # Test with empty data for XML
    result_xml = formatter.format({}, format_type='xml')
    expected_xml = '<root />'
    assert result_xml.strip() == expected_xml

def test_format_xml_with_list():
    formatter = OutputFormatter()
    data = ["item1", "item2", "item3"]
    with pytest.raises(AttributeError):
        formatter.format(data, format_type='xml')
    # The formatter expects a dictionary for XML formatting

def test_format_csv_with_non_dict_items():
    formatter = OutputFormatter()
    data = ["item1", "item2", "item3"]
    with pytest.raises(AttributeError):
        formatter.format(data, format_type='csv')
    # The _format_csv method expects dictionaries with values()

def test_format_with_invalid_data():
    formatter = OutputFormatter()
    data = "This is a string, not a dictionary or list."
    with pytest.raises(AttributeError):
        formatter.format(data, format_type='csv')
    # Similar for XML
    with pytest.raises(AttributeError):
        formatter.format(data, format_type='xml')

def test_format_json_with_non_serializable_data():
    formatter = OutputFormatter()
    data = {"set_data": {1, 2, 3}}
    with pytest.raises(TypeError):
        formatter.format(data, format_type='json')

def test_format_csv_with_nested_dict():
    formatter = OutputFormatter()
    data = {'name': 'John Doe', 'details': {
        'age': 30, 'email': 'john.doe@example.com'}}
    result = formatter.format(data, format_type='csv')

    expected_output = "name,details_age,details_email\r\nJohn Doe,30,john.doe@example.com\r\n"
    assert result == expected_output

def test_format_xml_with_special_characters():
    formatter = OutputFormatter()
    data = {"message": "This & that < those > these"}
    result = formatter.format(data, format_type='xml')
    root = ET.fromstring(result)
    message = root.find('message')
    assert message is not None
    assert message.text == "This & that < those > these"

def test_format_xml_with_attributes():
    # Since the formatter doesn't support attributes, this test is to confirm behavior
    formatter = OutputFormatter()
    data = {"user": {"@id": "123", "name": "John"}}
    result = formatter.format(data, format_type='xml')
    root = ET.fromstring(result)
    user = root.find('user')
    assert user is not None
    id_element = user.attrib.get('id')
    assert id_element is not None
    assert id_element == '123'

def test_format_csv_with_empty_list():
    formatter = OutputFormatter()
    result = formatter.format([], format_type='csv')
    assert result == ''

def test_format_json_with_empty_list():
    formatter = OutputFormatter()
    result = formatter.format([], format_type='json')
    expected = json.dumps([], ensure_ascii=False, indent=2)
    assert result == expected

def test_format_xml_with_empty_dict():
    formatter = OutputFormatter()
    result = formatter.format({}, format_type='xml')
    expected = '<root />'
    assert result.strip() == expected

# New tests for _restructure_data method
def test_single_record_dict():
    formatter = OutputFormatter()

    data = {
        "name": "John Doe",
        "age": 30,
        "email": "john.doe@example.com"
    }
    expected = {"name": "John Doe", "age": 30, "email": "john.doe@example.com"}
    
    assert formatter._restructure_data(data) == expected

def test_dict_of_lists():
    formatter = OutputFormatter()

    data = {
        "title": ["Title1", "Title2"],
        "price": ["£10", "£20"]
    }
    expected = [
        {"title": "Title1", "price": "£10"},
        {"title": "Title2", "price": "£20"}
    ]
    assert formatter._restructure_data(data) == expected

def test_nested_with_top_key():
    formatter = OutputFormatter()

    data = {
        "books": {
            "title": ["Title1", "Title2"],
            "price": ["£10", "£20"]
        }
    }
    expected = [
        {"title": "Title1", "price": "£10"},
        {"title": "Title2", "price": "£20"}
    ]
    assert formatter._restructure_data(data) == expected

def test_mixed_data_error():
    formatter = OutputFormatter()

    data = {
        "title": ["Title1", "Title2"],
        "author": "John Doe"  # scalar, while 'title' is a list
    }
    with pytest.raises(TypeError):
        formatter._restructure_data(data)
