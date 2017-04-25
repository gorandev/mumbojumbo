import re
from scrapy.exporters import JsonLinesItemExporter
from scrapy.utils.python import to_bytes


class JsonMongoLinesItemExporter(JsonLinesItemExporter):
    def export_item(self, item):
        itemdict = dict(self._get_serialized_fields(item))
        data = self.encoder.encode(itemdict) + '\n'
        data = re.sub(
            r'"date": ("\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")',
            r'"date": ISODate(\1)',
            data
        )
        self.file.write(to_bytes(data, self.encoding))
