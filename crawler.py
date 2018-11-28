import re

from scrapy.http import Request
from scrapy.spiders import Spider
from scrapy.crawler import CrawlerProcess
from config import CONFIG


class PortalSpider(Spider):
    name = 'portalspider'
    allowed_domains = CONFIG['ALLOWED_DOMAIN']

    def start_requests(self):
        if self.portal['NAME'] == 'CNN':
            yield Request(self.portal['START'] % (self.date, self.cnn_attr['page'], self.date), headers={'User-Agent': CONFIG['USER_AGENT']})
        else:
            yield Request(self.portal['START'] % self.date, headers={'User-Agent': CONFIG['USER_AGENT']})

    def __init__(self, date='', portal='DETIK', **kwargs):
        super().__init__(**kwargs)
        self.portal = CONFIG[portal.upper()]
        if self.portal['NAME'] in ['Tempo', 'CNN', 'Republika']:
            date = date.replace('-', '/')
        self.date = date
        self.cnn_attr = {
            'page': 1,
            'articles_size': 0
        }

    def parse(self, response):
        articles = response.xpath(self.portal['ARTICLES']).extract()
        for article in articles:
            if self.portal['NAME'] == "Tribun":
                article = '{}?page=all'.format(article)
            elif self.portal['NAME'] == "CNN":
                article = article.replace("\\", "")
            yield Request(article, callback=self.parse_article, headers={'User-Agent': CONFIG['USER_AGENT']})

        pages = []
        if self.portal['NAME'] == 'CNN' and self.cnn_attr['articles_size'] < len(articles):
            self.cnn_attr['articles_size'] = len(articles)
            self.cnn_attr['page'] = self.cnn_attr['page'] + 1
            pages.append(self.portal['START'] %
                         (self.date, self.cnn_attr['page'], self.date))
        elif self.portal['NAME'] == 'Republika' and len(articles) < 40:
            pages = []
        else:
            pages = response.xpath(self.portal['NEXT_PAGES']).extract()

        for next_page in pages:
            yield response.follow(next_page, self.parse, headers={'User-Agent': CONFIG['USER_AGENT']})

    def parse_title(self, response):
        title = response.xpath(self.portal['TITLE']).extract_first()
        if self.portal['NAME'] == 'Tempo':
            regex = re.compile(r'[\n\r\t]')
            title = regex.sub("", title)
        elif self.portal['NAME'] == 'CNN':
            title = self.strip(title)

        return title

    def parse_author(self, response):
        author = response.xpath(self.portal['AUTHOR']).extract_first()
        if self.portal['NAME'] == 'Tribun':
            nrt_strip = re.compile(r'[\n\r\t]')
            author = nrt_strip.sub("", author)
            author = author.replace("Editor: ", "")

        return author

    def parse_date(self, response):
        date = response.xpath(self.portal['DATE']).extract_first()

        if self.portal['NAME'] == "Kompas":
            date = date.replace("Kompas.com - ", "")
        elif self.portal['NAME'] == "CNN":
            date = date.replace("CNN Indonesia | ", "")
            date = self.strip(date)

        return date

    def parse_tag(self, response):
        tags = response.xpath(self.portal['TAG']).extract()
        return ', '.join(tags)

    def parse_category(self, response):
        category = response.xpath(self.portal['CATEGORY']).extract_first()

        if self.portal['NAME'] == 'Replubika':
            category = self.strip(category)

        return category

    def parse_content(self, response):
        regex = re.compile(r'[\n\r\t]')
        try:
            exclude_link = response.xpath(
                self.portal['EXCLUDE_LINK']).extract()
        except Exception:
            exclude_link = []

        has_exclude_text = False
        if 'EXCLUDE_TEXT' in self.portal:
            has_exclude_text = True
            exclude_text = re.compile(
                self.portal['EXCLUDE_TEXT'], re.IGNORECASE)

        has_stop_criteria = False
        if 'STOP_CRITERION' in self.portal:
            has_stop_criteria = True
            stop_criteria = re.compile(
                self.portal['STOP_CRITERION'], re.IGNORECASE)

        contents_result = ''
        contents = response.xpath(self.portal['CONTENTS']).extract()
        for content in contents:
            if content in exclude_link:
                continue
            elif has_exclude_text and exclude_text.match(content):
                continue
            elif "googletag" in content:
                continue

            content_norm = regex.sub("", content)
            contents_result = '{} {}'.format(contents_result, content_norm)
            contents_result = self.strip(contents_result)

            if has_stop_criteria and stop_criteria.match(content):
                break

        return contents_result

    def parse_article(self, response):
        is_store = True
        try:
            title = self.parse_title(response)
            date = self.parse_date(response)
            author = self.parse_author(response)
            tags = self.parse_tag(response)
            category = self.parse_category(response)
            content = self.parse_content(response)
        except Exception:
            is_store = False

        if is_store:
            return {
                'title': title,
                'author': author,
                'date': date,
                'category': category,
                'content': content,
                'tags': tags,
                'link': response.request.url,
                'media': self.portal['NAME'],
            }

    def strip(self, string):
        result = string.rstrip()
        result = result.lstrip()

        return result