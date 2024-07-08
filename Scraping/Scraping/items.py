# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class ScrapingItem(scrapy.Item):
    file_urls = scrapy.Field()  # List of URLs to download
    # Other metadata fields
    title = scrapy.Field()
    url = scrapy.Field()
    malnummer = scrapy.Field()
    benamning = scrapy.Field()
    lagrum = scrapy.Field()
    rattsfall = scrapy.Field()
    sokord = scrapy.Field()
