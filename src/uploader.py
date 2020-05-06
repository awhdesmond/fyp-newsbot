import json

import cli
import common
import conf
import repository

def upload_data_to_repo(config: conf.Config, dump_path: str):
    articles = []
    with open(dump_path, 'r') as f:
        for line in f:
            article = common.models.Article(**json.loads(line))
            articles.append(article)

    repo = repository.ArticlesRepository(config.elasticsearch)
    repo.bulk_insert(articles)


if __name__ == "__main__":
    args = cli.parse_cli_args()
    config = conf.Config.from_file(args.config)
    upload_data_to_repo(config, args.dump_path)
