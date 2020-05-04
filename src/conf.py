import yaml
from typing import List

class NewsAPIConfig:
    def __init__(self, api_keys: List[str]):
        self.api_keys = api_keys

    @staticmethod
    def from_dict(d):
        return NewsAPIConfig(
            api_keys=d["api_keys"]
        )


class ElasticSearchConfig:
    def __init__(self, endpoint: str, index: str, doc_type: str):
        self.endpoint = endpoint
        self.index = index
        self.doc_type = doc_type

    @staticmethod
    def from_dict(d):
        return ElasticSearchConfig(
            endpoint=d["endpoint"],
            index=d["index"],
            doc_type=d["doc_type"],
        )


class Config:
    def __init__(
        self,
        newsapi: NewsAPIConfig,
        elasticsearch: ElasticSearchConfig,
    ):
        self.newsapi = newsapi
        self.elasticsearch = elasticsearch

    @staticmethod
    def from_file(filepath: str):
        with open(filepath, 'r') as f:
            data = yaml.load(f, Loader=yaml.FullLoader)
            return Config.from_dict(data)

    @staticmethod
    def from_dict(d):
        return Config(
            newsapi=NewsAPIConfig.from_dict(d['newsapi']),
            elasticsearch=ElasticSearchConfig.from_dict(d['elasticsearch']),
        )
