import re
import json
import locale

from scrapy.http import Request, FormRequest
from scrapy.spiders import Spider
from scrapy.crawler import CrawlerProcess
from datetime import datetime

from config import CONFIG
locale.setlocale(locale.LC_ALL, 'id_ID.UTF-8')


class PortalSpider(Spider):
    name = 'portalspider'
    allowed_domains = CONFIG['ALLOWED_DOMAIN']

    def start_requests(self):
        if self.portal['NAME'] == 'CNN':
            yield Request(self.portal['START'] % (self.date, self.cnn_attr['page'], self.date), headers={'User-Agent': CONFIG['USER_AGENT']})
        elif self.portal['NAME'] == 'Bisnis':
            date_tmp = datetime.strptime(self.date, '%Y-%m-%d')
            locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
            date_tmp = date_tmp.strftime("%d+%B+%Y")
            locale.setlocale(locale.LC_ALL, 'id_ID.UTF-8')
            yield Request(self.portal['START'] % date_tmp, headers={'User-Agent': CONFIG['USER_AGENT']})
        elif self.portal['NAME'] == 'VIVA':
            self.portal['FORM_DATA']['last_publish_date'] = self.date + " 23:59:59"
            yield FormRequest(self.portal['START'], headers={'User-Agent': CONFIG['USER_AGENT']}, formdata=self.portal['FORM_DATA'])
        elif self.portal['NAME'] in ["Media Indonesia", "Antara News", "Jakarta Post"]:
            yield Request(self.portal['START'], headers={'User-Agent': CONFIG['USER_AGENT']})
        elif self.portal['NAME'] == 'Pikiran Rakyat':
            yield Request(self.portal['START'] % 1, self.parse_pikiran_rakyat, headers={'User-Agent': CONFIG['USER_AGENT']})
        else:
            yield Request(self.portal['START'] % self.date, headers={'User-Agent': CONFIG['USER_AGENT']})

    def __init__(self, date='', portal='DETIK', **kwargs):
        super().__init__(**kwargs)
        self.portal = CONFIG[portal.upper()]
        if self.portal['NAME'] in ['Tempo', 'CNN', 'Republika', 'Liputan6', 'Okezone', 'Metrotvnews']:
            date = date.replace('-', '/')
        elif self.portal['NAME'] == 'Berita Satu':
            tmp = date.split("-")
            date = "{}-{}-{}".format(tmp[2], tmp[1], tmp[0])
        elif self.portal['NAME'] == 'Jakarta Post':
            locale.setlocale(locale.LC_ALL, 'en_GB.UTF-8')
            self.stop = False
        self.cnn_attr = {
            'page': 1,
            'articles_size': 0
        }
        self.date = date

    def parse(self, response):
        articles = response.xpath(self.portal['ARTICLES']).extract()
        count = 0
        for article in articles:
            if self.portal['NAME'] == "Tribun":
                article = '{}?page=all'.format(article)
            elif self.portal['NAME'] == "CNN":
                article = article.replace("\\", "")
            elif self.portal['NAME'] == "Liputan6" and "/foto-" in article:
                continue
            elif self.portal['NAME'] == "Bisnis" and "koran.bisnis" in article:
                continue
            elif self.portal['NAME'] in ["Media Indonesia", "Antara News"]:
                if self.filter_by_date(response, count) == 0:
                    return
                elif self.filter_by_date(response, count) == 2:
                    continue
                count = count + 1
            elif self.portal['NAME'] == "Okezone" and "lifestyle" in article:
                continue
            elif self.portal['NAME'] == "VIVA":
                if self.filter_by_date(response, 0) == 0:
                    return
            elif self.portal['NAME'] == "Jakarta Post" and self.stop:
                return            

            yield Request(article, callback=self.parse_article, headers={'User-Agent': CONFIG['USER_AGENT']})

        pages = []
        if self.portal['NAME'] == 'CNN' and self.cnn_attr['articles_size'] < len(articles):
            self.cnn_attr['articles_size'] = len(articles)
            self.cnn_attr['page'] = self.cnn_attr['page'] + 1
            pages.append(self.portal['START'] %
                         (self.date, self.cnn_attr['page'], self.date))
        elif self.portal['NAME'] == 'Republika' and len(articles) < 40:
            pages = []
        elif self.portal['NAME'] == 'VIVA':
            pages = []
            data = response.xpath(
                '//script/text()')[-1].re("window.last_publish_date = (.+?);\n")
            self.portal['FORM_DATA']['last_publish_date'] = data[0].strip('\"')
            yield FormRequest(self.portal['START'], self.parse, headers={'User-Agent': CONFIG['USER_AGENT']}, formdata=self.portal['FORM_DATA'])
        else:
            pages = response.xpath(self.portal['NEXT_PAGES']).extract()

        for next_page in pages:
            if self.portal['NAME'] == 'Suara Merdeka':
                next_page = "https://www.suaramerdeka.com/index.php/news/indeks{}".format(next_page)
            else:
                yield response.follow(next_page, self.parse, headers={'User-Agent': CONFIG['USER_AGENT']})

    def parse_title(self, response):
        title = response.xpath(self.portal['TITLE']).extract_first()
        if self.portal['NAME'] == 'Tempo':
            regex = re.compile(r'[\n\r\t]')
            title = regex.sub("", title)
        elif self.portal['NAME'] == 'CNN':
            title = self.strip(title)

        if title is not None:
            title = title.strip()

        return title

    def parse_author(self, response):
        author = response.xpath(self.portal['AUTHOR']).extract_first()
        if self.portal['NAME'] in ['Tribun', 'Antara News']:
            nrt_strip = re.compile(r'[\n\r\t]')
            author = nrt_strip.sub("", author)
            author = author.replace("Editor: ", "")
        elif self.portal['NAME'] == 'Okezone':
            author = self.strip(author)
            author = author[:-1]
        elif self.portal['NAME'] in ['Pikiran Rakyat', "Jakarta Post"]:
            author = self.strip(author)
        elif self.portal['NAME'] == 'Pikiran Rakyat':
            author = response.xpath(self.portal['DATE']).extract()
            author = author[1].split("|")[0]
            author = self.strip(author)
        elif self.portal['NAME'] == "Metrotvnews":
            author = author.split('•')
            author = author[0]
            author = self.strip(author)
        elif self.portal['NAME'] == "Suara Merdeka":
            regex = re.compile(r'\(.+\/.+\/.+\)', re.IGNORECASE)
            author = response.xpath('//p[@style="font-weight: bold;"]/text()').extract_first()
            author = regex.findall(author)[0]
            author = author.split('/')
            author = author[0][1:]
            
        if author is not None:
            author = author.strip()

        return author

    def parse_date(self, response):
        date = response.xpath(self.portal['DATE']).extract_first()

        if self.portal['NAME'] == "Kompas":
            date = date.replace("Kompas.com - ", "")
        elif self.portal['NAME'] == "CNN":
            date = date.replace("CNN Indonesia | ", "")
            date = self.strip(date)
        elif self.portal['NAME'] == "Bisnis":
            date = response.xpath(self.portal['DATE']).extract()
            date = date[1].split("|")[1]
            date = self.strip(date)
        elif self.portal['NAME'] == "Media Indonesia":
            date = date.replace("Pada: ", "")
            date = self.strip(date)
        elif self.portal['NAME'] in ["Antara News", "Pikiran Rakyat"]:
            date = self.strip(date)
        elif self.portal['NAME'] == "Metrotvnews":
            date = date.split('•')
            date = date[1]
            date = self.strip(date)

        # Date normalizer
        date = datetime.strptime(date, self.portal['DATE_FORMAT'])

        return date

    def parse_tag(self, response):
        tags = response.xpath(self.portal['TAG']).extract()
        return ', '.join(tags)

    def parse_category(self, response):
        category = response.xpath(self.portal['CATEGORY']).extract_first()

        if self.portal['NAME'] == 'Replubika':
            category = self.strip(category)
        elif self.portal['NAME'] == 'Berita Satu':
            category = response.request.url.split("/")[3]
        elif self.portal['NAME'] == 'Suara Merdeka':
            category = category.split("\\")[2]
            category = self.strip(category)      

        if category is not None:
            category = category.strip()

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
        if self.portal['NAME'] == "Media Indonesia":
            contents = contents[7:]
        for content in contents:
            if content in exclude_link:
                continue
            elif has_exclude_text and exclude_text.match(content):
                continue
            elif "googletag" in content:
                continue

            content_norm = regex.sub("", content)
            
            if has_stop_criteria and stop_criteria.match(content):
                break
            
            contents_result = '{} {}'.format(contents_result, content_norm)
            contents_result = self.strip(contents_result)

        if contents_result is not None:
            contents_result = contents_result.strip()

        return contents_result

    def parse_article(self, response):
        is_store = True

        if self.portal['NAME'] == "Jakarta Post":
            if self.filter_by_date(response, 0) == 0:
                self.stop = True
                return
            elif self.filter_by_date(response, 0) == 2:
                return

        try:
            title = self.parse_title(response)
            date = self.parse_date(response)
            author = self.parse_author(response)
            tags = self.parse_tag(response)
            category = self.parse_category(response)
            content = self.parse_content(response)
        except Exception as e:
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

    def filter_by_date(self, response, count):
        if self.portal['NAME'] == "Media Indonesia":
            art_date_tmp = response.xpath(
                self.portal['ART_DATE']).extract()[count]
            art_date_tmp = art_date_tmp.split(",")
            art_date = art_date_tmp[1][1:]
            art_date = datetime.strptime(art_date, '%d %b %Y')
        elif self.portal['NAME'] == "Antara News":
            art_date = response.xpath(
                self.portal['ART_DATE']).extract()[count]
            if "menit lalu" in art_date:
                art_date = datetime.now()
            else:
                art_date = art_date[1:-6]
                art_date = datetime.strptime(art_date, '%d %B %Y')
        elif self.portal['NAME'] == "VIVA":
            data = response.xpath(
                '//script/text()')[-1].re("window.last_publish_date = (.+?);\n")
            date = data[0].strip('\"').split(" ")
            art_date = datetime.strptime(date[0], '%Y-%m-%d')
        elif self.portal['NAME'] == "Pikiran Rakyat":
            dates = response['published_at'].split(" ")
            art_date = datetime.strptime(dates[0], '%Y-%m-%d')
        elif self.portal['NAME'] == "Jakarta Post":
            date = response.xpath(self.portal['DATE']).extract_first()
            date = date[5:]
            art_date = datetime.strptime(date, '%B %d, %Y')

        filter_date = datetime.strptime(self.date, '%Y-%m-%d')
        if art_date == filter_date:
            return 1
        elif art_date > filter_date:
            return 2
        else:
            return 0

    def parse_pikiran_rakyat(self, response):
        json_response = json.loads(response.body_as_unicode())
        articles = json_response['data']
        for article in articles:
            filter_date = self.filter_by_date(article, 0)
            if filter_date == 2:
                continue
            elif filter_date == 0:
                return

            category_slug = article['category']['slug']
            date_ = article['published_at'].split(" ")[0]
            date_ = date_.replace("-", "/")
            url = "https://www.pikiran-rakyat.com/{}/{}/{}".format(
                category_slug, date_, article['slug'])
            yield Request(url, callback=self.parse_article, headers={'User-Agent': CONFIG['USER_AGENT']})

        next_page = json_response['meta']['current_page'] + 1
        yield Request(self.portal['START'] % next_page, self.parse_pikiran_rakyat, headers={'User-Agent': CONFIG['USER_AGENT']})


# process = CrawlerProcess({
#     'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)',
#     'FEED_FORMAT': 'json',
#     'FEED_URI': 'data.json'
# })

# process.crawl(PortalSpider, date="2018-12-12", portal="pikiran-rakyat")
# process.start()  # the script will block here until the crawling is finished
