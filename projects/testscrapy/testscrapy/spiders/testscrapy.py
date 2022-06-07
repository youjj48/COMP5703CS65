import scrapy
import re
from w3lib.html import remove_tags
from scrapy.loader import ItemLoader

class HealthdirectSpider(scrapy.Spider):
    name = 'healdir'
    allowed_domain = ['healthdirect.gov.au/health-topics/conditions']
    start_urls = ['https://www.healthdirect.gov.au/health-topics/conditions']

    def parse(self, response):
        for href in response.xpath('/html/body/section[1]/section/div/main/div/section/ul/li/a/@href').extract():
            yield scrapy.Request(url='https://www.healthdirect.gov.au'+href, callback=self.parse_item)

    def parse_item(self, response):
        # Get xpath
        xpath1 = '//*[@id="mainContentArticleText"]/div/p'
        xpath2 = '//*[@id="mainContentArticleText"]/div/*[self::h2 or self::h3]'
        xpath3 = '//*[@id="mainContentArticleText"]/div/ul//li'
        topics = response.xpath(xpath1 + '|' + xpath2 + '|' + xpath3)
        title = response.xpath('//*[@id="mainContentArticleText"]/div/h2[1]/text()').get()
        descr = {}
        text = {}
        tag_li = {}
        para = []
        n = 0
        list_tags=[]

        for topic in topics:
            tags = topic.xpath('name()').get()
            list_tags.append(tags)
        if 'h2' in list_tags:
            for topic in topics:
                # paragrahp
                if topic.xpath('name()').get() == 'p':
                    word = topic.extract()
                    string = "".join(word)
                    dr = re.compile(r'<[^>]+>', re.S)
                    word = dr.sub('', string)
                    para.append(word)

                elif topic.xpath('name()').get() == 'li':
                    n += 1
                    string = "".join(topic.extract())
                    dr = re.compile(r'<[^>]+>', re.S)
                    dd = dr.sub('', string)
                    tag_li[str(n)] = dd


                # sub_head
                elif topic.xpath('name()').get() == 'h2' or 'h3':
                    text["paragraph"] = para
                    text["bp_title"] = tag_li
                    descr[title] = text
                    string = "".join(topic.extract())
                    dr = re.compile(r'<[^>]+>', re.S)
                    title = dr.sub('', string)

                    tag_li = {}
                    text = {}
                    para = []
                    n = 0
            text["paragraph"] = para
            text["bp_title"] = tag_li
            descr[title] = text
        elif 'h2' not in list_tags:
            for topic in topics:
                # paragrahp
                if topic.xpath('name()').get() == 'p':
                    string = "".join(word)
                    dr = re.compile(r'<[^>]+>', re.S)
                    word = dr.sub('', string)
                    para.append(word)

                elif topic.xpath('name()').get() == 'li':
                    bp_title = word
                    string = "".join(topic.extract())
                    dr = re.compile(r'<[^>]+>', re.S)
                    dd = dr.sub('', string)
                    tag_li[str(n)] = dd
                    n += 1
            descr["paragraph"] = para
            descr["bp_title"] = tag_li

        yield {
            'name': topic.xpath('//*[@id="mainContentArticleText"]/header/h1/text()').get(),
            'body': descr,
        }