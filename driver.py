import copy
import random

from pyspark import SparkConf, SparkContext
from newsapi import NewsApiClient
from newsagents.straitstimes import StraitsTimesAgent 
from newsagents.cna import CNAAgent
from newsagents.todayonline import TodayOnlineAgent


PAGE_SIZE = 5
NUM_PAGES_PER_DOMAIN = 5
 
API_KEYS = ["ed7f51d8a8824d83950c89a512bb0971", "c633303300c94234b6a78350b2aa8e82"]
API_CLIENTS = list(map(lambda key: NewsApiClient(api_key=key), API_KEYS))

def generateDomainParmas(domain):
    return [(domain, page) for page in range(1, NUM_PAGES_PER_DOMAIN)]

def fetchDomainArticlesMetadata(param):
    apiClient = random.choice(API_CLIENTS)
    metadata = apiClient.get_everything(language='en', 
                                        domains=param[0], 
                                        page=param[1], 
                                        page_size=PAGE_SIZE, 
                                        sort_by="publishedAt")["articles"]
    return metadata


def filterNontextArticles(metadata):
    return "www." in metadata["url"]

def parseMetadata(metadata):
    return {
        "source"        : metadata["source"]["name"],
        "url"           : metadata["url"],
        "imageurl"      : metadata["urlToImage"],
        "title"         : metadata["title"],
        "author"        : metadata["author"],
        "publishedDate" : metadata["publishedAt"]
    }

def fulfillArticleContent(metadata):
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
        else:
            article["content"] = ""
            return article

        article["content"] = agent.get_content()
        return article

    except Exception as e:
        print("An error occurred: ", e)
        article["content"] = ""
        return article




conf = SparkConf().setMaster("local").setAppName("NewsAgent")
sc = SparkContext(conf=conf)

domains = sc.parallelize(["straitstimes.com", "channelnewsasia.com", "todayonline.com"])
domainsParams = domains.flatMap(generateDomainParmas)
metadata = domainsParams.flatMap(fetchDomainArticlesMetadata)
metadata = metadata.filter(filterNontextArticles).map(parseMetadata)

metadata.persist()

articles = metadata.map(fulfillArticleContent)
result = articles.collect()

print(result[1:10])