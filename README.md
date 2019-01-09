# News Crawler

Script untuk melakukan _crawling_ pada sejumlah portal news di Indonesia.

# List Portal News

- [Antara News](https://www.antaranews.com/)
- [Berita Satu](https://www.beritasatu.com/)
- [Bisnis Indonesia](http://www.bisnis.com/)
- [CNN Indonesia](https://www.cnnindonesia.com/)
- [Detik](https://news.detik.com/)
- [Kompas](https://www.kompas.com/)
- [Liputan 6](https://www.liputan6.com/)
- [Media Indonesia](http://mediaindonesia.com/)
- [Okezone](https://www.okezone.com/)
- [Pikiran Rakyat](https://www.pikiran-rakyat.com/)
- [Republika](https://www.republika.co.id/)
- [Sindo News](https://www.sindonews.com/)
- [Tempo](https://www.tempo.co/)
- [Tribun News](http://www.tribunnews.com/)
- [VIVA](https://www.viva.co.id/)

### Tech

- [Python3] - Python is a programming language that lets you work quickly and integrate systems more effectively
- [Scrapy] - An open source and collaborative framework for extracting the data you need from websites. In a fast, simple, yet extensible way.
- [pip] - The PyPA recommended tool for installing Python packages

### Installation

```sh
$ git clone https://github.com/rizaldntr/portal-news-crawler.git news-crawler
$ cd news-crawler
$ pip install -r requirements.txt
```

### Running Program

#### Cara 1

```sh
$ scrapy runspider crawler.py -a date=[DATE] -a portal=[PORTAL_NAME] -o [OUTPUT_FILE] -t [FORMAT_FILE]
```

Contoh:

```sh
$ scrapy runspider crawler.py -a date=2018-11-29 -a portal=pikiran-rakyat -o crawler.json -t json
```

Portal Name:

- ANTARANEWS
- BERITASATU
- BISNIS
- CNN
- DETIK
- JAKARTAPOST
- KOMPAS
- LIPUTAN6
- MEDIAINDONESIA
- OKEZONE
- PIKIRAN-RAKYAT
- REPUBLIKA
- SINDO
- TEMPO
- TRIBUN
- VIVA

Format File:

- jsonlines
- json
- csv
- xml
- pickle
- marshal

#### Cara 2

```python
import scrapy
from scrapy.crawler import CrawlerProcess

class PortalSpider(Spider):
    # Your spider definition
    ...

process = CrawlerProcess({
    'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)',
    'FEED_FORMAT': 'json',
    'FEED_URI': 'data.json'
})

process.crawl(MySpider, date=[DATE], portal=[PORTAL_NAME])
process.start() # the script will block here until the crawling is finished
```

### Todos

- None

[python3]: https://www.python.org/
[scrapy]: https://scrapy.org/
[pip]: https://github.com/pypa/pip
