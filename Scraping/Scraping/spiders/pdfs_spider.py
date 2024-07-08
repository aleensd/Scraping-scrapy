import scrapy
import json
import os

from ..items import ScrapingItem


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

    custom_settings = {
        'FEED_FORMAT': 'json',
        'FEED_URI': 'metadata.json',
        'DOWNLOAD_DELAY': 1,
        'CONCURRENT_REQUESTS': 50,  # Increase concurrency for scraping
        'CONCURRENT_REQUESTS_PER_DOMAIN': 50,
    }

    def start_requests(self):
        while self.skip < self.total_items:
            yield scrapy.Request(
                url=f'https://www.domstol.se/api/search/1122/?isZip=false&layoutRootId=0&query&scope=decision'
                    f'&searchPageId=15264&skip={self.skip}&sortMode=mostRecent',
                method='POST',
                headers={'Content-Type': 'application/json'},
                body=json.dumps({}),
                callback=self.parse
            )
            self.skip += self.items_per_page

    def parse(self, response, **kwargs):
        data = json.loads(response.text)
        for item in data['searchResultItems']:
            link = item['link']['link']['url']
            full_link = self.base_url + link
            yield scrapy.Request(url=full_link, callback=self.parse_pdf)

    def parse_pdf(self, response):
        metadata = ScrapingItem()
        metadata['title'] = response.xpath("//span[@data-testid='subTitle']/text()").get().strip()
        metadata['malnummer'] = self.extract_value_list_content(response, 'Målnummer')
        metadata['benamning'] = self.extract_value_list_content(response, 'Benämning')
        metadata['lagrum'] = self.extract_value_list_content(response, 'Lagrum', 'li')
        metadata['rattsfall'] = self.extract_value_list_content(response, 'Rättsfall', 'li')
        metadata['sokord'] = self.extract_value_list_content(response, 'Sökord', 'link')

        pdf_url = response.xpath('//div[@class="card__inner"]//a/@href').get()
        if pdf_url:
            metadata['url'] = response.url
            metadata['file_urls'] = [self.base_url + pdf_url]
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
                    return div.xpath("normalize-space()").get() if div else None

                elif type == 'li':
                    ul_element = parent_div.xpath("following-sibling::ul[@class='value-list value-list--unordered' "
                                                  "and @data-testid='ValueListUnordered']")
                    return ul_element.xpath(".//li[@class='value-list__item']/text()").getall() if ul_element else None

                elif type == 'link':
                    div = parent_div.xpath("following-sibling::div[@class='value-list' and @data-testid='LinkList']")
                    return div.xpath(".//a[@class='link']/@href").getall() if div else None

        return None
