import json
import re
import pandas as pd
import xml.etree.ElementTree as ET
from io import StringIO
from typing import Any, Dict, List, Union


class OutputFormatter:
    def format(self, data, format_type='json', structure_data: bool = True) -> str:

        if format_type == 'json':          
            if structure_data and isinstance(data, dict):
                data = self._restructure_data(data)
                
            return json.dumps(data, ensure_ascii=False, indent=2)
        elif format_type == 'csv':
            return self._format_csv(data)
        elif format_type == 'xml':
            return self._format_xml(data)
        else:
            raise ValueError(f"Unknown format type: {format_type}")

    def _format_csv(self, data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> str:
        if not isinstance(data, (dict, list)):
            raise AttributeError(
                "Data must be a dictionary or a list of dictionaries for CSV formatting.")

        if isinstance(data, dict):
            data = [data]  # Convert single dict to list of dicts

        if not all(isinstance(item, dict) for item in data):
            raise AttributeError(
                "All items in the data list must be dictionaries for CSV formatting.")

        # Flatten nested dictionaries
        df = pd.json_normalize(data, sep='_')

        # Check if DataFrame is empty or has no columns
        if df.empty or df.shape[1] == 0:
            return ''  # Return empty string if no data to write

        output = StringIO()
        df.to_csv(output, index=False)

        return output.getvalue()

    def _format_xml(self, data: Dict[str, Any]) -> str:
        if not isinstance(data, dict):
            raise AttributeError(
                "Data must be a dictionary for XML formatting.")

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

    def _restructure_data(self, data_dict: Dict) -> List[Dict]:
        """
        Dynamically inspects the dictionary and restructures it into a list of dictionaries.
        
        Scenarios:
        1) Single-level dict of scalars -> return [ { ... all scalars ... } ].
        2) Single-level dict of lists   -> return [ { key1: val1[i], key2: val2[i], ... }, ... ].
        3) Nested dict with exactly one top-level key -> process the inner dict 
        according to #1 or #2.
        4) If there's a mixture of lists and scalars in the same dict, or multiple top-level 
        keys that are all dicts, raise an error or handle it as needed.
        
        Returns:
            list of dict:
                - If scenario #1 or #2, straightforwardly restructured.
                - If scenario #3, the inner dict is restructured according to #1 or #2.
        
        Raises:
            TypeError: If data cannot be handled by the logic (e.g., mixing scalars & lists).
            ValueError: If a dictionary of lists has lists of unequal length.
        """

        # Quick checks
        if not isinstance(data_dict, dict):
            raise TypeError(f"Expected data_dict to be a dictionary, got {type(data_dict)}.")

        # 1) If there's exactly one top-level key and its value is a dict, we might want 
        #    to process that dict instead (like the "books" scenario).
        if len(data_dict) == 1:
            (only_key, only_value) = list(data_dict.items())[0]
            if isinstance(only_value, dict):
                # Recursively call the same function on this single sub-dict
                return self._restructure_data(only_value)
            # else fall through to check if it's scalar or list, etc.

        # 2) If we get here, either we have multiple keys at the top or a single key
        #    whose value is not a dict.

        #   - Check if this is a dictionary of lists or a dictionary of scalars.
        #   - Or a mixture -> raise error unless you have special logic.

        values = list(data_dict.values())
        # Helper to detect if something is list-like
        def is_list_like(x):
            return isinstance(x, list)

        # (a) Dictionary of lists?
        if all(is_list_like(v) for v in values):
            
            # Ensure all lists have same length
            keys = list(data_dict.keys())
            
            if len(keys) == 0:
                return {}
            
            length = len(data_dict[keys[0]])
            for k in keys[1:]:
                if len(data_dict[k]) != length:
                    raise ValueError("All lists must have the same length.")
            # Build list of dictionaries
            result = []
            for i in range(length):
                row = {}
                for k in keys:
                    row[k] = data_dict[k][i]
                result.append(row)
            return result

        # (b) Dictionary of scalars?
        if all(not is_list_like(v) for v in values):
            # Return a single-element list
            return data_dict

        # (c) If we reach here, we have a mixture (some values are lists, some are scalars)
        # or multiple nested dicts at the top level. This example code won't handle that
        # automatically, so we'll raise an error. 
        # (You could also handle partial merges, recursion, etc. if you wish.)
        raise TypeError(
            "Mixed or more complex data structure detected. "
            "Some values are lists while others are scalars or multiple dict keys found."
        )