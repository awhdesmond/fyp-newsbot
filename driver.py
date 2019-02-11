import logging
import random
import copy
import sched, time

from newsapi import NewsApiClient

from newsagents.straitstimes import StraitsTimesAgent 
from newsagents.cna import CNAAgent
from newsagents.todayonline import TodayOnlineAgent
from newsagents.scmp import SCMPAgent

from elasticsearchManager import ElasticsearchManager
from pyspark import SparkConf, SparkContext

# Logging
logging.basicConfig(level=logging.INFO, filename='app.log', filemode='w', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Scheduler
scheduler = sched.scheduler(time.time, time.sleep)

conf = SparkConf().setMaster("local").setAppName("NewsAgent")
sparkContext = SparkContext(conf=conf)

# Elasticsearch
esManager = ElasticsearchManager()

PAGE_SIZE = 50
NUM_PAGES_PER_DOMAIN = 10
DOMAINS = ["straitstimes.com", "channelnewsasia.com", "todayonline.com", "scmp.com"]
 
API_KEYS = ["ed7f51d8a8824d83950c89a512bb0971", "c633303300c94234b6a78350b2aa8e82"]
API_CLIENTS = list(map(lambda key: NewsApiClient(api_key=key), API_KEYS))


def _generateDomainParmas(domain):
        return [(domain, page) for page in range(1, NUM_PAGES_PER_DOMAIN)]
    
def _fetchDomainArticlesMetadata(param):
    apiClient = random.choice(API_CLIENTS)
    metadata = apiClient.get_everything(language='en', 
                                        domains=param[0], 
                                        page=param[1], 
                                        page_size=PAGE_SIZE, 
                                        sort_by="publishedAt")["articles"]
    return metadata

def _filterNontextArticles(metadata):
    return "www." in metadata["url"]

def _parseMetadata(metadata):
    return {
        "source"        : metadata["source"]["name"],
        "url"           : metadata["url"],
        "imageurl"      : metadata["urlToImage"],
        "title"         : metadata["title"],
        "author"        : metadata["author"],
        "publishedDate" : metadata["publishedAt"]
    }


def _fulfillArticleContent(metadata):
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


def fetchArticles():
    domains = sparkContext.parallelize(DOMAINS)
    domainsParams = domains.flatMap(_generateDomainParmas) 
    metadata = domainsParams.flatMap(_fetchDomainArticlesMetadata) \
                            .filter(_filterNontextArticles) \
                            .map(_parseMetadata)
    metadata.persist()

    articles = metadata.map(_fulfillArticleContent) \
                        .filter(lambda a: len(a["content"]) > 0)

    results = articles.collect()
    return results



def newsbotJob():
    logging.info('Start of Spark Job.')

    articles = fetchArticles()

    # Elastic Search Code
    for article in articles:
        esManager.indexDocument("articles", '_doc', article)

    # Remove Duplicates
    articleCount = esManager.indexCount("articles", '_doc')
    searchBody = {
        "query": {
            "match_all": {}
        }
    }
    response = esManager.searchIndex("articles", '_doc', searchBody, size=articleCount)
    indexArticles = [article["_source"] for article in response["hits"]["hits"]]
    indexArticles = sparkContext.parallelize(indexArticles)

    indexArticles = indexArticles.map(lambda x: (x["url"], x)) \
                                 .reduceByKey(lambda x, y: x) \
                                 .map(lambda x: x[1]) \
                                 .filter(lambda a: len(a["content"]) > 0)
    
    results = indexArticles.collect()
    esManager.deleteByQuery("articles", "_doc", searchBody)

    for article in results:
        esManager.indexDocument("articles", '_doc', article)

    logging.info('Number of articles added: %d', len(results))
    logging.info('End of Spark Job.')
    

def runNewsbotJob(sc): 
    newsbotJob()
    scheduler.enter(10800, 1, runNewsbotJob, (sc,)) 

def main():
    newsbotJob()
    # scheduler.enter(10800, 1, runNewsbotJob, (scheduler,))
    # scheduler.run()

main()





