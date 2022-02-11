"""Functions to work with ElasticSearch."""

import logging
from elasticsearch import Elasticsearch


def connect_elasticsearch(target: dict, auth: tuple) -> Elasticsearch:
    """Connect to local elastic server"""
    _es = Elasticsearch(
        [target],
        http_auth=auth
    )
    if _es.ping():
        logging.info('Connected to Elastic')
        create_index(_es, "python")
        create_index(_es, "javascript")
        create_index(_es, "go")
    else:
        logging.error('Failed to connect!')
        _es = None
    return _es


def create_index(es, index_name: str = "versioner") -> bool:
    """Populating Elastic with strict schema to index"""
    config = {
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 1
        }
    }
    es.indices.create(index=index_name, ignore=400, **config)
    return True


def clear_index(es, index_name: str = "versioner") -> bool:
    """Delete indexes from Elastic"""
    if es is not None:
        es.indices.delete(index=index_name, ignore=400)
        return True
    return False
