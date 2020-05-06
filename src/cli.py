import argparse

def parse_cli_args():
    parser = argparse.ArgumentParser("python3 src/driver.py")

    general = parser.add_argument_group("General")
    general.add_argument(
        "--config",
        type=str,
        default="config/config.yml",
        dest="config",
        help="path to config file (default=config/config.yml)"
    )
    general.add_argument(
        "--dump_path",
        type=str,
        default=None,
        dest="dump_path",
        help="path to dump all articles (existing + new)"
    )

    scrape = parser.add_argument_group("Scrape Configs")
    scrape.add_argument(
        "--num-pages",
        type=int,
        default=1,
        dest="num_pages",
        help="number of pages to scrape (default=1)"
    )
    scrape.add_argument(
        "--page-size",
        type=int,
        default=10,
        dest="page_size",
        help="page size per scraping page (default=10)"
    )

    scrape.add_argument(
        "--start_date",
        type=str,
        default="2020-04-07",
        dest="start_date",
        help="start date to scrape from (default=2020-04-07)"
    )

    args = parser.parse_args()
    return args
