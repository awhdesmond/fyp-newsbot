from typing import List

import cli
import conf
import repository
import news_api
import todayonline

import log
logger = log.init_stream_logger(__name__)


def dump_articles_to_path(articles: List, dump_path: str):
    """
    Dump all the data in the elasticsearch database to
    a local json file
    """
    logger.info(f"Dumping Articles to {dump_path}")

    with open(dump_path, "w+") as f:
        for article in articles:
            f.write(article.json())
            f.write("\n")

    logger.info("Dumping Articles Completed")


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
        start_date=args.start_date,
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

    if args.dump_path:
        dump_articles_to_path(unique_articles.values(), args.dump_path)

    repo.bulk_insert(unique_articles.values())


if __name__ == "__main__":
    args = cli.parse_cli_args()
    config = conf.Config.from_file(args.config)
    main(args, config)
