

import json
from typing import List, Dict

import cli
import conf
import repository
import news_api
import todayonline

from newsagents.straitstimes import StraitsTimesAgent
from newsagents.cna import CNAAgent
from newsagents.todayonline import TodayOnlineAgent

import log
logger = log.new_stream_logger(__name__)


def dump_exisiting_data(config: conf.Config, dump_path: str):
    """
    Dump all the data in the elasticsearch database to
    a local json file
    """
    logger.info("Dumping Existing Articles...")

    repo = repository.ArticlesRepository(config.elasticsearch)
    existing_articles = repo.list_articles()

    logger.info(f"Found {len(existing_articles)} articles in the database")

    with open(dump_path, 'w') as jsonfile:
        json.dump(existing_articles, jsonfile)

    logger.info("Dumping Existing Articles Completed")


def main(args, config: conf.Config):
    """
    Executes the news scraping job from different news sources
    """
    logger.info("Start of Newsbot Job")

    # Initialise es connection and api keys
    repo = repository.ArticlesRepository(config.elasticsearch)

    all_articles = []

    # News API Pipeline
    news_api_pipeline = news_api.pipeline.NewsApiPipeline(config.newsapi)
    all_articles.extend(news_api_pipeline.generate(
        domains=[
            "channelnewsasia.com",
            "straitstimes.com",
        ],
        num_pages=args.num_pages,
        page_size=args.page_size,
    ))

    # Today API Pipeline
    today_pipeline = todayonline.pipeline.TodayPipeline()
    all_articles.extend(today_pipeline.generate(args.num_pages, args.page_size))

    # Fetch existing articles and delete them
    all_articles.extend(repo.list_articles())
    repo.delete_all_articles()

    unique_articles = {}
    for a in all_articles:
        unique_articles[a.url] = a

    repo.bulk_insert(unique_articles.values())


if __name__ == "__main__":
    args = cli.parse_cli_args()
    config = conf.Config.from_file(args.config)

    if args.dump:
        dump_exisiting_data(config, args.dump)

    main(config)
