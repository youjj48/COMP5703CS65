# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class MayospiderItem(scrapy.Item):
	name = scrapy.Field()
	title = scrapy.Field()
	info = scrapy.Field()

class MedlinespiderItem(scrapy.Item):
	name = scrapy.Field()
	title = scrapy.Field()
	info = scrapy.Field()