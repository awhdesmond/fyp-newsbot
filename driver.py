# -*- coding: utf-8 -*-

import logging
import sched, time

from newsbot import Newsbot
from elasticsearchManager import ElasticsearchManager
from pyspark import SparkConf, SparkContext

# Logging
logging.basicConfig(level=logging.INFO, filename='app.log', filemode='w', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Scheduler
scheduler = sched.scheduler(time.time, time.sleep)

conf = SparkConf().setMaster("local").setAppName("NewsAgent")
sc = SparkContext(conf=conf)

newsbot = Newsbot(sc)
esManager = ElasticsearchManager()

def newsbotJob():
    logging.info('Start of Spark Job.')

    articles = newsbot.fetchArticles()

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
    indexArticles = sc.parallelize(indexArticles)

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
    scheduler.enter(10800, 1, runNewsbotJob, (s,))
    scheduler.run()







