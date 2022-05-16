#scrapy crawl medline -o medline.json

import scrapy
import re
from MayoSpider.items import MedlinespiderItem
from bs4 import BeautifulSoup

class MedlineSpider(scrapy.Spider):
    name = 'medline'
    allowed_domain=['medlineplus.gov/']
    start_urls = ['https://medlineplus.gov/all_healthtopics.html']
    #start_urls = ['https://medlineplus.gov/cpr.html']
    count = 0
    
    def writeCount(self):
        with open('./medline_config.txt','w',encoding='utf8')as fp:
            fp.write(str(self.count))
            
    def parse(self,response):
        href_list_1 = response.xpath('//*[@id="topic_all"]/article/section/div/div[2]/ul/li/a/@href').extract()
        href_list_1 = set(href_list_1)
        for href in href_list_1:
            yield response.follow(url=href, callback=self.parseItem)
    
    def parseItem(self,response):
        name = response.xpath('//*[@id="topic"]/article/div[1]/div[1]/h1/text()').get()
        if name is not None:
            name = name.replace('\n                        ','')
            name = name.replace('\n                    ','')
        also_called = response.xpath('//*[@id="topic"]/article/div[1]/div[1]/span/text()').get()
        if also_called is not None:
            also_called = also_called.split(": ")[1].split(", ")
        
        summary_content = response.xpath('//*[@id="topic-summary"]').xpath('string(.)').extract()
        if summary_content is not None:
            summary_content = summary_content[0]
            summary_content = summary_content.replace('\n','')
            summary_content = summary_content.replace('\t','')
            
        main_content = {}
        sub_topics = response.xpath('//section[re:test(@id, "cat_\d+_section")]')
        for sub_topic in sub_topics:
            sub_title = sub_topic.xpath('./div/div/div/h2').xpath('string(.)').extract()
            if len(sub_title)>0:
                sub_title = sub_title[0].replace('\n','')
                sub_title = sub_title.replace('  ','')
            
            content = sub_topic.xpath('./div/div[2]/ul/li').xpath('string(.)').extract()
            if len(content) > 0:
                for i in range(len(content)):
                    content[i] = content[i].replace('\n','')
                    content[i] = content[i].replace('  ','')
            main_content[sub_title] = content
        
        yield{
            'name':name,
            'also_called':also_called,
            'summary':summary_content,
            'body':main_content,
        }
        
        self.count+=1
        self.writeCount()