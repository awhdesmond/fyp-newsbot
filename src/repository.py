from typing import List
from elasticsearch import Elasticsearch

import conf
from common.models import Article


class ArticlesRepository:
    """
    Articles repo powered by elasticsearch

    Attributes:
        endpoint: es endpoint
    """
    def __init__(self, config: conf.ElasticSearchConfig):
        self.es = Elasticsearch([config.endpoint])
        self.index = config.index
        self.doc_type = config.doc_type

    def index_count(self):
        """
        Retrieve a count of all the articles in the db
        """
        search_body = {
            "query": {
                "match_all": {}
            }
        }
        resp = self.es.count(
            index=self.index,
            doc_type=self.doc_type,
            body=search_body
        )

        return resp["count"]

    def list_articles(self, size=None):
        """
        Retrieve all the articles in the db
        """
        search_body = {
            "query": {
                "match_all": {}
            }
        }
        resp = self.es.search(
            index=self.index,
            doc_type=self.doc_type,
            body=search_body,
            size=size
        )
        return [Article(**article["_source"]) for article in resp["hits"]["hits"]]

    def delete_all_articles(self):
        """
        Delete all the articles in the db
        """
        search_body = {
            "query": {
                "match_all": {}
            }
        }
        return self.es.delete_by_query(
            index=self.index,
            doc_type=self.doc_type,
            body=search_body,
        )

    def bulk_insert(self, articles: List[Article]):
        """
        Bulk insert articles into the database
        """
        bulk_body = []
        for article in articles:
            bulk_body.append({'index': {}})
            bulk_body.append(article.json())

        return self.es.bulk(
            index=self.index,
            doc_type=self.doc_type,
            body=bulk_body,
            request_timeout=10000
        )
