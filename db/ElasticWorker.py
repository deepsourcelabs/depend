"""Functions to work with ElasticSearch"""

import logging
from elasticsearch import Elasticsearch
import Secrets


def connect_elasticsearch(target: dict) -> Elasticsearch:
    """Connect to local elastic server"""
    _es = None
    _es = Elasticsearch(
        [target],
        http_auth=("elastic", Secrets.PASSWORD)
    )
    if _es.ping():
        logging.info('Connected to Elastic')
        create_index(_es, "python")
        create_index(_es, "javascript")
        create_index(_es, "go")
    else:
        logging.error('Failed to connect!')
    return _es


def create_index(es: Elasticsearch, index_name: str = "versioner") -> bool:
    """Populating Elastic with strict schema to index"""
    config = {
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 1
        }
    }
    es.indices.create(index=index_name, ignore=400, **config)
    return True


def clear_index(es: Elasticsearch, index_name: str = "versioner") -> bool:
    """Delete indexes from Elastic"""
    es.indices.delete(index=index_name, ignore=400)
    return True
