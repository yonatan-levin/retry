import json
import re
import pandas as pd
import xml.etree.ElementTree as ET
from io import StringIO
from typing import Any, Dict, List, Union

class OutputFormatter:
    def format(self, data, format_type='json') -> str:
        if format_type == 'json':
            return json.dumps(data, ensure_ascii=False, indent=2)
        elif format_type == 'csv':
            return self._format_csv(data)
        elif format_type == 'xml':
            return self._format_xml(data)
        else:
            raise ValueError(f"Unknown format type: {format_type}")

    def _format_csv(self, data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> str: 
        if not isinstance(data, (dict, list)):
            raise AttributeError("Data must be a dictionary or a list of dictionaries for CSV formatting.")
       
        if isinstance(data, dict):
            data = [data]  # Convert single dict to list of dicts

        if not all(isinstance(item, dict) for item in data):
            raise AttributeError("All items in the data list must be dictionaries for CSV formatting.")

        # Flatten nested dictionaries
        df = pd.json_normalize(data, sep='_')
        
        if df.empty or df.shape[1] == 0:  # Check if DataFrame is empty or has no columns
            return ''  # Return empty string if no data to write

        output = StringIO()
        df.to_csv(output, index=False)
        
        return output.getvalue()

    def _format_xml(self, data: Dict[str, Any]) -> str:
        if not isinstance(data, dict):
            raise AttributeError("Data must be a dictionary for XML formatting.")
        
        root = ET.Element("root")
        self._dict_to_xml(root, data)
        return ET.tostring(root, encoding='unicode')

    def _dict_to_xml(self, parent: ET.Element, data: Any, parent_key: str = 'root') -> None:
        if isinstance(data, dict):
            attribs = {}
            text = None
            for key, value in data.items():
                if key.startswith('@'):
                    # Attribute
                    attrib_name = self._sanitize_name(key[1:])
                    attribs[attrib_name] = str(value)
                elif key == '#text':
                    # Text content
                    text = str(value)
                elif isinstance(value, list):
                    # Handle lists within dictionaries
                    child_tag = self._sanitize_name(key)
                    for item in value:
                        child = ET.SubElement(parent, child_tag)
                        self._dict_to_xml(child, item, parent_key=key)
                else:
                    # Child element
                    child_tag = self._sanitize_name(key)
                    child = ET.SubElement(parent, child_tag)
                    self._dict_to_xml(child, value, parent_key=key)
            if attribs:
                parent.attrib.update(attribs)
            if text:
                parent.text = text
        elif isinstance(data, list):
            # Handle lists of values or dictionaries
            child_tag = self._sanitize_name(parent_key)
            for item in data:
                child = ET.SubElement(parent, child_tag)
                self._dict_to_xml(child, item, parent_key=parent_key)
        elif data is None:
            # Empty element
            pass
        else:
            # Scalar value
            parent.text = str(data)

    def _sanitize_name(self, name: str) -> str:
        # Remove invalid characters
        name = re.sub(r'[^a-zA-Z0-9_\-\.]', '', name)
        # Ensure the name starts with a letter or underscore
        if not re.match(r'^[a-zA-Z_]', name):
            name = f'_{name}'
        return name