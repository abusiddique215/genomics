import logging

try:
    from elasticsearch import Elasticsearch
except ImportError:
    print("Warning: Elasticsearch not installed. Some logging features may not work.")
    Elasticsearch = None

class ElasticsearchHandler(logging.Handler):
    def __init__(self, host='localhost', port=9200):
        super().__init__()
        if Elasticsearch is not None:
            self.es = Elasticsearch([{'host': host, 'port': port}])
        else:
            self.es = None

    def emit(self, record):
        if self.es is not None:
            message = self.format(record)
            self.es.index(index="app-logs", body={'message': message, 'level': record.levelname})
        else:
            print(f"Warning: Elasticsearch not available. Log message: {self.format(record)}")

def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    handler = ElasticsearchHandler()
    logger.addHandler(handler)
    return logger