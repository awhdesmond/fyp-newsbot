import argparse
import random
import copy
import json 
import requests

from typing import List, Dict
from newsapi import NewsApiClient

import conf
import elastic
from newsagents.straitstimes import StraitsTimesAgent 
from newsagents.cna import CNAAgent
from newsagents.todayonline import TodayOnlineAgent

import log
logger = log.new_stream_logger(__name__)

DEFAULT_NUM_PAGES = 1
DEFAULT_PAGE_SIZE = 10
ES_ARTICLES_INDEX_NAME = "articles"

####################
# Helper Functions #
####################
def _parse_metadata(metadata):
    return {
        "source"        : metadata["source"]["name"],
        "url"           : metadata["url"],
        "imageurl"      : metadata["urlToImage"],
        "title"         : metadata["title"],
        "author"        : metadata["author"],
        "publishedDate" : metadata["publishedAt"]
    }

def strip_url_query_params(article):
    if "?" in article["url"]:
        article["url"] = article["url"][0:article["url"].index("?")]
    return article

########################
# Today Pipeline Steps #
########################
def generate_today_urls(num_pages=DEFAULT_NUM_PAGES, page_size=DEFAULT_PAGE_SIZE):
    fmt_str = "https://www.todayonline.com/api/v3/news_feed/{}?items={}"
    return [fmt_str.format(i, page_size) for i in range(1, num_pages)]
    
def generate_today_nodes(urls: List[str]):
    totalNodes = []
    agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36"
    for url in urls:
        res = requests.get(url, headers={ 'user-agent': agent })
        nodes = res.json()["nodes"]
        totalNodes.extend(nodes)
    return totalNodes

def parse_today_nodes(nodes):
    results = []
    for node in nodes:
        parsedNode =  {
            "source": "todayonline.com",
            "url": node["node"]["node_url"],
            "imageurl": node["node"]["photo_4_3_image"],
            "title": node["node"]["title"],
            "author": node["node"]["author"][0]["name"] if len(node["node"]["author"]) > 0 else "",
            "publishedDate": node["node"]["publication_date"].replace(" ", "T") + "Z"
        }
        results.append(parsedNode)
    return results


##########################
# NewsAPI Pipeline Steps #
##########################
def fetch_existing_articles(esManager: elastic.ElasticsearchManager):
    """Fetch existing articles from elasticsearch db
    """
    logger.info("Fetching existing articles from elasticsearch")
    existing_articles_count = esManager.indexCount(ES_ARTICLES_INDEX_NAME, "_doc")
    logger.info(f"{existing_articles_count} of articles found")
    searchBody = {
         "query": {
             "match_all": {}
         }
     }
    existing_articles = esManager.searchIndex(
        ES_ARTICLES_INDEX_NAME, 
        "_doc", 
        searchBody, 
        size=existing_articles_count
    )
    existing_articles = [article["_source"] for article in existing_articles["hits"]["hits"]]
    return existing_articles


def fetch_articles_metadata_from_news_api(
    api_clients: List[NewsApiClient],
    page_size=DEFAULT_PAGE_SIZE,
    num_pages=DEFAULT_NUM_PAGES,
    domains=("straitstimes.com", "channelnewsasia.com")
):
    """fetch potentially new articles from news api
    """
    logger.info("Fetching articles metadata")
    domain_page_pairs = [
        (d, page) for page in range(1, num_pages + 1) for d in domains
    ]
    article_metadata = []
    for domain, page in domain_page_pairs:
        apiClient = random.choice(api_clients)
        metadata = apiClient.get_everything(
            language="en", 
            domains=domain, 
            page=page, 
            page_size=page_size, 
            sort_by="publishedAt"
        )["articles"]
        article_metadata.extend(metadata)

    article_metadata = [_parse_metadata(m) for m in article_metadata if "www." in m["url"]]
    logger.info(f"Feteched {len(article_metadata)} articles metadata")
    return article_metadata

def fetch_articles_from_metadata_list(article_metadata: List[Dict]):
    logger.info("Fetching articles content")
    
    articles = []
    for metadata in article_metadata:
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
        except Exception as e:
            logger.error("An error occurred: %s", e)
            article["content"] = ""
        articles.append(article)
    
    logger.info(f"Number of potentially new articles: {len(articles)}")
    return articles

def delete_existing_articles(esManager: elastic.ElasticsearchManager):
    searchBody = {
         "query": {
             "match_all": {}
         }
     }
    esManager.deleteByQuery(ES_ARTICLES_INDEX_NAME, "_doc", searchBody)

def add_articles_into_elasticsearch(
    esManager: elastic.ElasticsearchManager, 
    articles: List[Dict]
):
    esBody = []
    for article in articles:
        esBody.append({'index': {}})
        esBody.append(article)
    esManager.bulk(ES_ARTICLES_INDEX_NAME, '_doc', esBody)
    logger.info('Number of articles added: %d' % len(articles))
    
def dumpData(config: conf.Config, dump_path: str):
    esManager = elastic.ElasticsearchManager(config.elasticsearch_config.host)
    existing_articles = fetch_existing_articles(esManager)
    with open(dump_path, 'w') as jsonfile:
        json.dump(existing_articles, jsonfile)


def main(config: conf.Config):
    logger.info("Start of Newsbot Job")
    esManager = elastic.ElasticsearchManager(config.elasticsearch_config.host)
    api_clients = [NewsApiClient(api_key=k) for k in config.newsapi_config.api_keys]
    
    existing_articles = fetch_existing_articles(esManager)
    
    # News API Pipeline
    news_api_articles_metadata = fetch_articles_metadata_from_news_api(api_clients)
    news_api_articles = fetch_articles_from_metadata_list(news_api_articles_metadata)
    news_api_articles = [strip_url_query_params(a) for a in news_api_articles]
    news_api_articles = [a for a in news_api_articles if a["content"]]

    # Today API Pipeline
    today_urls = generate_today_urls()
    today_nodes = generate_today_nodes(today_urls)
    today_metadata = parse_today_nodes(today_nodes)
    today_articles = fetch_articles_from_metadata_list(today_metadata)
    today_articles = [a for a in today_articles if a["content"]]

    delete_existing_articles(esManager)
    all_articles = existing_articles + news_api_articles + today_articles
    all_articles_dict = {}
    for a in all_articles:
        all_articles_dict[a['url']] = a
    add_articles_into_elasticsearch(esManager, all_articles_dict.values())


def parse_cli_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config", 
        type=str, 
        dest="config", 
        help="path to config file"
    )
    parser.add_argument(
        "--dump", 
        type=str,
        default=None, 
        dest="dump", 
        help="path to dump existing articles before job"
    )


    args = parser.parse_args()
    return args

if __name__ == "__main__":
    args = parse_cli_args()
    config = conf.Config.from_file(args.config)
    if args.dump:
        dumpData(config, args.dump)

    main(config)
