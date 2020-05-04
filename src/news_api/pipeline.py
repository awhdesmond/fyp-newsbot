from typing import List
from newsapi import NewsApiClient

import conf
from common.models import Article
from news_api import cna, straitstimes

import log
logger = log.new_stream_logger(__name__)


class NewsApiPipeline:

    def __init__(self, config: conf.NewsAPIConfig):
        self.api_clients = [NewsApiClient(api_key=k) for k in config.api_keys]

    def strip_url_query_params(self, url):
        if "?" in url:
            url = url[0:url.index("?")]
        return url

    def generate_articles(
        self,
        domains: List[str],
        page_size=1,
        num_pages=10,
    ):
        """
        Fetch potentially new articles from news api
        """
        logger.info("Fetching newsapi articles metadata")

        domain_page_pairs = [
            (d, page) for page in range(1, num_pages + 1) for d in domains
        ]
        raw_metadata = []
        for idx, (domain, page) in enumerate(domain_page_pairs):
            client = self.api_clients[idx % len(self.api_clients)]
            resp = client.get_everything(
                language="en",
                domains=domain,
                page=page,
                page_size=page_size,
                sort_by="publishedAt"
            )
            metadata = resp["articles"]
            raw_metadata.extend(metadata)

        articles = []
        for metadata in raw_metadata:
            raw_metadata["url"] = self.strip_url_query_params(raw_metadata["url"])
            article = Article(**raw_metadata)
            articles.append(article)

        logger.info(f"Feteched {len(articles)} articles")
        return articles

    def generate_content(metadata: List[Article]):
        """
        Fetch the actual article content from the url present
        in the metadata
        """
        logger.info("Fetching articles content")

        for article in metadata:
            url = article.url
            source = article.source.lower()

            if source == "straitstimes.com":
                agent = straitstimes.StraitsTimesAgent(url)
            elif source == "channelnewsasia.com":
                agent = cna.CNAAgent(url)

            try:
                article.content = agent.get_content()
            except Exception as e:
                logger.warn(f"failed to retrieve content for {url}. found: {str(e)}")
                article.content = ""

    def generate(
        self,
        domains: List[str],
        num_pages: int = 1,
        page_size: int = 10
    ):
        articles = self.generate_articles(domains, num_pages, page_size)
        self.generate_content(articles)
        return articles
