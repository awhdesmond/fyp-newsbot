## Installation
```
python3 -m venv env
pip3 install -r requirements.txt
```

## Running pinocchio-newsbot
```
usage: python3 src/driver.py [-h] [--config CONFIG] [--dump_path DUMP_PATH]
                             [--num-pages NUM_PAGES] [--page-size PAGE_SIZE]
                             [--start_date START_DATE]

optional arguments:
  -h, --help            show this help message and exit

General:
  --config CONFIG       path to config file (default=config/config.yml)
  --dump_path DUMP_PATH
                        path to dump all articles (existing + new)

Scrape Configs:
  --num-pages NUM_PAGES
                        number of pages to scrape (default=1)
  --page-size PAGE_SIZE
                        page size per scraping page (default=10)
  --start_date START_DATE
                        start date to scrape from (default=2020-04-07)
```


To run scraper -- `python3 src/driver.py --dump_path=articles.jsonl --page-size=20 --num-pages=5`

To run uploader -- `python3 src/uploader.py --dump_path=articles.jsonl`