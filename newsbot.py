# -*- coding: utf-8 -*-

import logging
import random
import copy

from newsapi import NewsApiClient

from newsagents.straitstimes import StraitsTimesAgent 
from newsagents.cna import CNAAgent
from newsagents.todayonline import TodayOnlineAgent
from newsagents.scmp import SCMPAgent

PAGE_SIZE = 50
NUM_PAGES_PER_DOMAIN = 10
DOMAINS = ["straitstimes.com", "channelnewsasia.com", "todayonline.com", "scmp.com"]
 
API_KEYS = ["ed7f51d8a8824d83950c89a512bb0971", "c633303300c94234b6a78350b2aa8e82"]
API_CLIENTS = list(map(lambda key: NewsApiClient(api_key=key), API_KEYS))


class Newsbot(object):

    def __init__(self, sparkContext):
        self.sparkContext = sparkContext

    def _generateDomainParmas(self, domain):
        return [(domain, page) for page in range(1, NUM_PAGES_PER_DOMAIN)]
    
    def _fetchDomainArticlesMetadata(self, param):
        apiClient = random.choice(API_CLIENTS)
        metadata = apiClient.get_everything(language='en', 
                                            domains=param[0], 
                                            page=param[1], 
                                            page_size=PAGE_SIZE, 
                                            sort_by="publishedAt")["articles"]
        return metadata

    def _filterNontextArticles(self, metadata):
        return "www." in metadata["url"]

    def _parseMetadata(self, metadata):
        return {
            "source"        : metadata["source"]["name"],
            "url"           : metadata["url"],
            "imageurl"      : metadata["urlToImage"],
            "title"         : metadata["title"],
            "author"        : metadata["author"],
            "publishedDate" : metadata["publishedAt"]
        }


    def _fulfillArticleContent(self, metadata):
        url = metadata["url"]
        source = metadata["source"].lower()
        article = copy.deepcopy(metadata)

        try:
            agent = None
            if source == "straitstimes.com":
                agent = StraitsTimesAgent(url)
            elif source == "channelnewsasia.com":
                agent = CNAAgent(url)
            elif source == "todayonline.com":
                agent = TodayOnlineAgent(url)
            elif source == "scmp.com":
                agent = SCMPAgent(url)
            else:
                article["content"] = ""
                return article

            article["content"] = agent.get_content()
            return article

        except Exception as e:
            logging.error("An error occurred: %s", e)
            article["content"] = ""
            return article


    def fetchArticles(self):
        domains = self.sparkContext.parallelize(DOMAINS)
        domainsParams = domains.flatMap(self._generateDomainParmas)
        metadata = domainsParams.flatMap(self._fetchDomainArticlesMetadata) \ 
                                .filter(self._filterNontextArticles) \ 
                                .map(self._parseMetadata)
        metadata.persist()

        articles = metadata.map(self._fulfillArticleContent) \
                            .filter(lambda a: len(a["content"]) > 0)

        results = articles.collect()
        return results
















