import json
import csv
import xml.etree.ElementTree as ET
from io import StringIO

class OutputFormatter:
    def format(self, data, format_type='json'):
        if format_type == 'json':
            return json.dumps(data, ensure_ascii=False, indent=2)
        elif format_type == 'csv':
            return self._format_csv(data)
        elif format_type == 'xml':
            return self._format_xml(data)
        else:
            raise ValueError(f"Unknown format type: {format_type}")

    def _format_csv(self, data):
        output = StringIO()
        writer = csv.writer(output)
        if isinstance(data, list):
            for item in data:
                writer.writerow(item.values())
        else:
            writer.writerow(data.values())
        return output.getvalue()

    def _format_xml(self, data):
        root = ET.Element("root")
        self._dict_to_xml(root, data)
        return ET.tostring(root, encoding='unicode')

    def _dict_to_xml(self, parent, data):
        for key, value in data.items():
            child = ET.SubElement(parent, key)
            if isinstance(value, dict):
                self._dict_to_xml(child, value)
            else:
                child.text = str(value)
