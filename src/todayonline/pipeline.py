import requests
from typing import List

from common import agents
from common.models import Article

import log
logger = log.init_stream_logger(__name__)


class TodayPipeline:
    """
    Pipeline for scraping Today Online news articles
    """

    URLS_FORMAT_STRING = "https://www.todayonline.com/api/v3/news_feed/{}?items={}"

    def generate_urls(self, num_pages: int = 1, page_size: int = 10):
        """
        Generate a list of urls for today online articles
        """
        logger.info("Generating todayonline urls")

        return [
            TodayPipeline.URLS_FORMAT_STRING.format(i, page_size)
            for i in range(1, num_pages + 1)
        ]

    def generate_articles(self, urls: List[str]):
        """
        Extract the articles information from the response
        returned by accessing the provided urls
        """
        logger.info("Fetching todayonline metadata")
        total_articles = []
        for url in urls:
            res = requests.get(
                url, headers={'user-agent': agents.HTTP_USER_AGENT}
            )
            articles = res.json()["nodes"]
            total_articles.extend(articles)

        results = []
        for raw in total_articles:
            article = Article(
                source="todayonline.com",
                url=raw["node"]["node_url"],
                imageurl=raw["node"]["photo_4_3_image"],
                title=raw["node"]["title"],
                author=raw["node"]["author"][0]["name"] if len(raw["node"]["author"]) > 0 else "",
                publishedDate=raw["node"]["publication_date"].replace(" ", "T") + "Z",
                content=raw["node"]["body"]
            )
            results.append(article)
        return results

    def generate(self, num_pages: int = 1, page_size: int = 10):
        urls = self.generate_urls(num_pages, page_size)
        articles = self.generate_articles(urls)
        return articles
