#scrapy crawl mayo -o mayo.json

import scrapy
import re
from MayoSpider.items import MayospiderItem
from bs4 import BeautifulSoup

class MayoSpider(scrapy.Spider):
    name = 'mayo'
    custom_settings = {
        'ITEM_PIPELINES': {
            'MayoSpider.pipelines.MayospiderPipeline': 300
        }
    }
    allowed_domain = ['mayoclinic.org/diseases-conditions',]
    start_urls = ['https://www.mayoclinic.org/diseases-conditions']
    #start_urls = ['https://www.mayoclinic.org/diseases-conditions/dandruff/symptoms-causes/syc-20353850']
    #count = 0
    incremental = False
            
    def readUrls(self):
        if self.incremental and os.path.exists('./mayo.json'):
            with open('./mayo.json','r',encoding='utf8')as fp: 
                    data = json.load(fp)
                    self.recorded_urls = [ele['url'] for ele in data]
                    
    def getContent(self,response,body):
        soup = BeautifulSoup(response.text,'html.parser')
        main = soup.find('article',id='main-content')
        dr = re.compile(r'<[^>]+>', re.S)
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
                body[title] = dict
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
            body[title] = dict
        return body
        
    def parse(self, response):
        try:
            self.readUrls()
        except:
            pass
        href_list_1 = response.xpath('//*[@id="main-content"]/div[2]/div/div/ol/li/a/@href').extract()
        for href in href_list_1:
            #print("Method parse entered page:",href)
            yield response.follow(url=href, callback=self.parseIndex)
        #print("End of the crawler................................")

    def parseIndex(self, response):
        href_list_2 = response.xpath('//*[@id="index"]/ol/li/a/@href').extract()
        for href in href_list_2:
            #print("Method parse_index entered page:",href)
            if re.match('/diseases-conditions/.*/symptoms-causes/',href):
                yield response.follow(url=href, callback=self.parseSymptoms)

    def parseSymptoms(self,response):
        url = response.url
        
        if self.incremental and url in self.recorded_urls:
            return 
            
        # Get Disease&Conditions
        name = response.xpath('//*[@id="mayoform"]/div[6]/header/div/h1/a/text()').get()
        href = response.xpath('//*[@id="et_genericNavigation_diagnosis-treatment"]/@href').extract()
        
        # Get description
        body = self.getContent(response,{})
        extra = {}
        extra['name'] = name
        extra['body'] = body
        extra['url'] = url
        #self.count+=1
        if len(href)>0:
            yield response.follow(url = href[0], callback= self.parseDiagnosis,meta=extra)
        else:
            yield {
            'name':name,
            'url':url,
            'body':body,
        }
        
    def parseDiagnosis(self,response):
        extra = response.meta
        name = extra['name']
        body = extra['body']
        url = extra['url']
        #print(body)
        
        # Get description
        body = self.getContent(response,body)
            
        yield{
            'name':name,
            'url':url,
            'body':body,
        }
        
