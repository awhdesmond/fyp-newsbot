import yaml
from typing import List

class NewsAPIConfig:
    def __init__(self, api_keys: List[str]):
        self.api_keys = api_keys

    @staticmethod
    def from_dict(d):
        return NewsAPIConfig(
            api_keys=d['api_keys']
        )


class ElasticSearchConfig:
    def __init__(self, host):
        self.host = host

    @staticmethod
    def from_dict(d):
        return ElasticSearchConfig(
            host=d['host']
        )


class Config:
    def __init__(
        self, 
        newsapi_config: NewsAPIConfig, 
        elasticsearch_config: ElasticSearchConfig,
    ):
        self.newsapi_config = newsapi_config
        self.elasticsearch_config = elasticsearch_config

    @staticmethod
    def from_file(filepath: str):
        with open(filepath, 'r') as f:
            data = yaml.load(f, Loader=yaml.FullLoader)
            return Config.from_dict(data)

    @staticmethod
    def from_dict(d):
        return Config(
            newsapi_config=NewsAPIConfig.from_dict(d['newsapi']),
            elasticsearch_config=ElasticSearchConfig.from_dict(d['elasticsearch']),
        )
    