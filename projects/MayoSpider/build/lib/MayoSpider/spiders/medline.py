#scrapy crawl medline -o medline.json

import scrapy
import re
from MayoSpider.items import MedlinespiderItem
from bs4 import BeautifulSoup

class MedlineSpider(scrapy.Spider):
    name = 'medline'
    custom_settings = {
        'ITEM_PIPELINES': {
            'MayoSpider.pipelines.MedlinespiderPipeline': 301
        }
    }
    allowed_domain=['medlineplus.gov/']
    start_urls = ['https://medlineplus.gov/healthtopics.html']
    #start_urls = ['https://medlineplus.gov/cpr.html']
    incremental = False
            
    def readUrls(self):
        if self.incremental and os.path.exists('./medline.json'):
            with open('./medline.json','r',encoding='utf8')as fp: 
                    data = json.load(fp)
                    self.recorded_urls = [ele['url'] for ele in data]
                    
    def parse(self,response):
        try:
            self.readUrls()
        except:
            pass
            
        href_list_1 = response.xpath('//*[@id="page_health_topic"]/article/div[2]/div[2]/div/section[1]/div/div[2]/ul/li/a/@href').extract()
        href_list_1 = set(href_list_1)
        print(href_list_1)
        for href in href_list_1:
            yield response.follow(url=href, callback=self.parseTopic)
    
    def parseTopic(self,response):
        href_list_2 = response.xpath('//*[@id="tpgp"]/article/section/ul/li/a/@href').extract()
        href_list_2 = set(href_list_2)
        for href in href_list_2:
            yield response.follow(url=href, callback=self.parseItem)
            
    def parseItem(self,response):
        url = response.url
        
        if self.incremental and url in self.recorded_urls:
            return 
            
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
            'url':url,
            'also_called':also_called,
            'summary':summary_content,
            'body':main_content,
        }
        