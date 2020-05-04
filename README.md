## Running pinocchio-newsbot
```
usage: driver.py [-h] [--config CONFIG] [--dump DUMP]

optional arguments:
  -h, --help       show this help message and exit
  --config CONFIG  path to config file
  --dump DUMP      path to dump existing articles before job
```
```yaml
newsapi:
  api_keys:
  - ed7f51d8a8824d83950c89a512bb0971
  - c633303300c94234b6a78350b2aa8e82
elasticsearch:
  host: localhost:9200
```
To run script -- `python3 driver.py --config config.yml`
> By default the script will only scrape 1 page. You can change `DEFAULT_NUM_PAGES` to any number from 1 to 10 (tested) to scrape the amount of articles that you need.