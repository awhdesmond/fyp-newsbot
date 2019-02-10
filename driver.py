# -*- coding: utf-8 -*-

import copy
import random
import logging
import sched, time

from elasticsearch import Elasticsearch
from pyspark import SparkConf, SparkContext
from newsapi import NewsApiClient

from newsagents.straitstimes import StraitsTimesAgent 
from newsagents.cna import CNAAgent
from newsagents.todayonline import TodayOnlineAgent
from newsagents.scmp import SCMPAgent

PAGE_SIZE = 50
NUM_PAGES_PER_DOMAIN = 10
 
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
        elif source == "scmp.com":
            agent = SCMPAgent(url)
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

es = Elasticsearch(['http://128.199.101.98:9200'])

## Driver Code
def job():
    logging.info('Start of Spark Job.')

    domains = sc.parallelize(["straitstimes.com", "channelnewsasia.com", "todayonline.com", "scmp.com"])
    domainsParams = domains.flatMap(generateDomainParmas)
    metadata = domainsParams.flatMap(fetchDomainArticlesMetadata)
    metadata = metadata.filter(filterNontextArticles).map(parseMetadata)

    metadata.persist()

    articles = metadata.map(fulfillArticleContent).filter(lambda a: len(a["content"]) > 0)

    results = articles.collect()

    # Elastic Search Code
    for article in results:
        res = es.index(index="articles", doc_type='_doc', body=article)

    # Remove Duplicates
    searchBody = {
        "query": {
            "match_all": {}
        }
    }
    res = es.count(index="articles", doc_type="_doc", body=searchBody)
    articleCount = res["count"]
    res = es.search(index="articles", doc_type="_doc", body=searchBody, size=articleCount)
    
    articles = res["hits"]["hits"]
    articles = [article["_source"] for article in articles]
    articles = sc.parallelize(articles)
    articles = articles.map(lambda x: (x["url"], x)).reduceByKey(lambda x, y: x).map(lambda x: x[1]).filter(lambda a: len(a["content"]) > 0)
    
    results = articles.collect()

    res = es.delete_by_query(index="articles", doc_type='_doc', body=searchBody)

    for article in results:
        res = es.index(index="articles", doc_type='_doc', body=article)

    logging.info('End of Spark Job.')
    logging.info('Number of articles added: %d', len(results))

# Logging
logging.basicConfig(level=logging.INFO, filename='app.log', filemode='w', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Schedule to run every 3 hours
s = sched.scheduler(time.time, time.sleep)
def run_job(sc): 
    job()
    s.enter(10800, 1, run_job, (sc,))

s.enter(10800, 1, run_job, (s,))
s.run()