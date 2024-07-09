from datetime import datetime
from collections import deque
from scrapy import signals

import scrapy
import json

from helpers.app_logger import get_logger
from ..items import ScrapingItem

logger = get_logger(__name__)


class PDFScraperSpider(scrapy.Spider):
    name = 'pdf_scraper'
    base_url = 'https://www.domstol.se'
    start_urls = [
        'https://www.domstol.se/api/search/1122/?isZip=false&layoutRootId=0&query&scope=decision&searchPageId=15264'
        '&skip=0&sortMode=mostRecent'
    ]
    skip = 0
    total_items = 2126
    items_per_page = 20
    pdfs_to_download = 10
    downloaded_pdfs = 0
    pdf_urls_queue = deque()

    custom_settings = {
        'FEED_FORMAT': 'json',
        'FEED_URI': 'metadata.json',
        'DOWNLOAD_DELAY': 1,
        'CONCURRENT_REQUESTS': 50,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 50,
        'ITEM_PIPELINES': {
            'Scraping.pipelines.PDFDownloadPipeline': 1,
        },
        'FILES_STORE': './pdfs'
    }

    def start_requests(self):
        logger.info("Starting requests")
        while self.skip < self.total_items:
            try:
                yield scrapy.Request(
                    url=f'https://www.domstol.se/api/search/1122/?isZip=false&layoutRootId=0&query&scope=decision'
                        f'&searchPageId=15264&skip={self.skip}&sortMode=mostRecent',
                    method='POST',
                    headers={'Content-Type': 'application/json'},
                    body=json.dumps({}),
                    callback=self.parse
                )
                self.skip += self.items_per_page
            except Exception as e:
                logger.error(f"Error during start_requests: {e}")

    def parse(self, response, **kwargs):
        logger.info(f"Parsing page: {response.url}")
        try:
            data = json.loads(response.text)
            for item in data['searchResultItems']:
                link = item['link']['link']['url']
                full_link = self.base_url + link
                yield scrapy.Request(url=full_link, callback=self.parse_pdf, meta={'date': item['footer']['date']})
        except Exception as e:
            logger.error(f"Error during parse: {e}")

    def parse_pdf(self, response):
        logger.info(f"Parsing PDF metadata: {response.url}")
        metadata = ScrapingItem()
        metadata['title'] = response.xpath("//span[@data-testid='subTitle']/text()").get().strip().replace('"', '')
        metadata['malnummer'] = self.extract_value_list_content(response, 'Målnummer')
        metadata['benamning'] = self.extract_value_list_content(response, 'Benämning')
        metadata['lagrum'] = self.extract_value_list_content(response, 'Lagrum', 'li')
        metadata['rattsfall'] = self.extract_value_list_content(response, 'Rättsfall', 'li')
        metadata['sokord'] = self.extract_value_list_content(response, 'Sökord', 'link')

        pdf_url = response.xpath('//div[@class="card__inner"]//a/@href').get()
        if pdf_url and '2024' in pdf_url:
            metadata['url'] = pdf_url
            pdf_date = response.meta.get('date')  # Fetching date from meta
            self.pdf_urls_queue.append((self.base_url + pdf_url, pdf_date))
            logger.debug(f"Added PDF {pdf_url} with date {pdf_date} to queue.")

        if len(self.pdf_urls_queue) == 77:
            sorted_pdfs = sorted(self.pdf_urls_queue, key=lambda x: datetime.strptime(x[1], '%Y-%m-%d'), reverse=True)[
                          :10]
            metadata['file_urls'] = [url for url, _ in sorted_pdfs]

        yield metadata

    @staticmethod
    def extract_value_list_content(response, title, type="text") -> str | list[str] | None:
        # Find the anchor div with id=title
        anchor_div = response.xpath(f"//div[@class='anchor' and @id='{title}']")

        if anchor_div:
            parent_div = anchor_div.xpath("ancestor::div[contains(@class, 'preheading--small')]")

            if parent_div:
                if type == 'text':
                    div = parent_div.xpath("following-sibling::div[@class='value-list' and @data-testid='ValueList']")
                    return ' '.join(div.xpath(".//text()").getall()).strip().replace('"', '') if div else None

                elif type == 'li':
                    ul_element = parent_div.xpath("following-sibling::ul[@class='value-list value-list--unordered' "
                                                  "and @data-testid='ValueListUnordered']")
                    extracted_items = [li.strip() for li in
                                       ul_element.xpath(".//li[@class='value-list__item']/text()").getall()] \
                        if ul_element else None
                    return [item for item in extracted_items if item] if extracted_items else None

                elif type == 'link':
                    div = parent_div.xpath("following-sibling::div[@class='value-list' and @data-testid='LinkList']")
                    return [link.strip() for link in div.xpath(".//a[@class='link']/@href").getall()] if div else None

        return None
