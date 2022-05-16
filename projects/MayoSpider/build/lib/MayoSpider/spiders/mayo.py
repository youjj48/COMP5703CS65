#scrapy crawl mayo -o mayo.json

import scrapy
import re
from MayoSpider.items import MayospiderItem
from bs4 import BeautifulSoup

class MayoSpider(scrapy.Spider):
    name = 'mayo'
    allowed_domain = ['mayoclinic.org/diseases-conditions']
    start_urls = ['https://www.mayoclinic.org/diseases-conditions']
    #start_urls = ['https://www.mayoclinic.org/diseases-conditions/selective-iga-deficiency/symptoms-causes/syc-20362236']
    count = 0
    
    def writeCount(self):
        with open('./mayo_config.txt','w',encoding='utf8')as fp:
            fp.write(str(self.count))
        
    def parse(self, response):
        href_list_1 = response.xpath('//*[@id="main-content"]/div[2]/div/div/ol/li/a/@href').extract()
        for href in href_list_1:
            #print("Method parse entered page:",href)
            yield response.follow(url=href, callback=self.parseIndex)
        print("End of the crawler................................")

    def parseIndex(self, response):
        href_list_2 = response.xpath('//*[@id="index"]/ol/li/a/@href').extract()
        for href in href_list_2:
            #print("Method parse_index entered page:",href)
            if re.match('/diseases-conditions/.*/symptoms-causes/',href):
                yield response.follow(url=href, callback=self.parseSymptoms)

    def parseSymptoms(self,response):
        
        # Get Disease&Conditions
        name = response.xpath('//*[@id="mayoform"]/div[6]/header/div/h1/a/text()').get()
        
        # Get description
        soup = BeautifulSoup(response.text,'html.parser')
        main = soup.find('article',id='main-content')
        dr = re.compile(r'<[^>]+>', re.S)
        descs={}
        fst_title = main.div.h2
        out = str(fst_title)
        title = dr.sub('',out)
        dict = {}
        blp_count=0
        desc_count=0
        for node in main.div.h2.next_siblings:
            
            # general paragrahp
            if node.name=='p':
                out = dr.sub('',str(node)).strip()
                if len(out)!=0:
                    dict['p'+str(desc_count)] = out
                    desc_count+=1
            # a new sub-title
            elif node.name == 'h2':
                descs[title] = dict
                dict = {}
                out = str(node)
                title = dr.sub('',out).strip()
                blp_count=0
                desc_count=0
            # bullet point
            elif node.name == 'ul':
                blt_point = node.li
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
            descs[title] = dict
        yield{
            'name':name,
            'body':descs,
        }
        self.count+=1
        self.writeCount()
