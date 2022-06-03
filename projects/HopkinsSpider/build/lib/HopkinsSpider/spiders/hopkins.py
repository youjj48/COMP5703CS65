#scrapy crawl hopkins -o hopkins.json

import scrapy
import re
import json
import os
from HopkinsSpider.items import HopkinsspiderItem
from bs4 import BeautifulSoup

class HopkinsSpider(scrapy.Spider):
    name = 'hopkins'
    allowed_domain = ['hopkinsmedicine.org/health/conditions-and-diseases',]
    start_urls = ['https://www.hopkinsmedicine.org/health/conditions-and-diseases']
    #start_urls = ['https://www.hopkinsmedicine.org/health/conditions-and-diseases/headache']
    count = 0
    recorded_urls=[]
    incremental = False
    
    def readUrls(self):
        if self.incremental and os.path.exists('./hopkins.json'):
            with open('./hopkins.json','r',encoding='utf8')as fp: 
                    data = json.load(fp)
                    self.recorded_urls = [ele['url'] for ele in data]

    def parse(self, response):
        try:
            self.readUrls()
        except:
            pass
        href_list_1 = response.xpath('//*[@id="links-list"]/section/ul/li/a/@href').extract()
        for href in href_list_1:
            if re.match('/health/conditions-and-diseases/.*',href):
                yield response.follow(url=href, callback=self.parseIndex)

    def parseIndex(self,response):
        url = response.url
        
        if self.incremental and url in self.recorded_urls:
            return 
        
        soup = BeautifulSoup(response.text,'html.parser')
        main = soup.find('main',id='skip')
        dr = re.compile(r'<[^>]+>', re.S)
        body = {}
        
        name_content = main.article.h1
        if name_content is None:
            return
        name = dr.sub('',str(name_content))
        if name is None:
            return
            
        fst_title = main.article.h2
        out = str(fst_title)
        title = dr.sub('',out)
        
        dict = {}
        blp_count=0
        desc_count=0
        
        content = main.article.div.p
        if content is None:
            content = main.article.div
            out = dr.sub('',str(content)).strip()
            if len(out)>0:
                body[title] = out
        else:
            if content.name=='p':
                out = dr.sub('',str(content)).strip()
                if len(out)!=0:
                    dict['p'+str(desc_count)] = out
                    desc_count+=1
                    
            for node in content.next_siblings:
                
                # general paragrahp
                if node.name=='p':
                    out = dr.sub('',str(node)).strip()
                    if len(out)!=0:
                        dict['p'+str(desc_count)] = out
                        desc_count+=1
                # a new sub-title
                elif node.name == 'h2':
                    body[title] = dict
                    dict = {}
                    out = str(node)
                    title = dr.sub('',out).strip()
                    blp_count=0
                    desc_count=0
                # bullet point
                elif node.name == 'ul' or node.name == 'ol':
                    blt_point = node.li
                    if blt_point is not None:
                        out = dr.sub('',str(blt_point)).strip()
                        if len(out) != 0:
                            dict['b'+str(blp_count)] = out
                            blp_count+=1
                        for ele in blt_point.next_siblings:
                            out = dr.sub('',str(ele)).strip()
                            if len(out) != 0:
                                dict['b'+str(blp_count)] = out
                                blp_count+=1
            if len(title)>0:
                body[title] = dict
        
        yield{
            'name':name,
            'url':url,
            'body':body,
        }