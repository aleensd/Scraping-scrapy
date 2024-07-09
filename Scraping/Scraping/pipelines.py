# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from scrapy.pipelines.files import FilesPipeline
from urllib.parse import urlparse

import scrapy


class ScrapingPipeline:
    def process_item(self, item, spider):
        return item


class PDFDownloadPipeline(FilesPipeline):

    def get_media_requests(self, item, info):
        if 'file_urls' in item:
            for file_url in item['file_urls']:
                request = scrapy.Request(file_url, meta={'filename': file_url.split('/')[-1]})
                # request.headers['Referer'] = item['url']  # Assuming item['url'] holds the referer URL
                yield request

    def file_path(self, request, response=None, info=None, *, item=None):
        return request.meta['filename']
