import argparse

def parse_cli_args():
    parser = argparse.ArgumentParser("Pinocchio Newsbot Crawler")

    general = parser.add_argument_group("General")
    general.add_argument(
        "--config",
        type=str,
        dest="config/config.yml",
        help="path to config file"
    )
    general.add_argument(
        "--dump",
        type=str,
        default=None,
        dest="dump",
        help="path to dump existing articles before job"
    )

    scrape = parser.add_argument_group("Scrape Configs")
    scrape.add_argument(
        "--num-pages",
        type=int
        default=1,
        dest="num_pages",
        help="number of pages to scrape"
    )
    scrape.add_argument(
        "--page-size",
        type=int
        default=10,
        dest="page_size",
        help="page size per scraping page"
    )

    args = parser.parse_args()
    return args