from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from Scraping.Scraping.spiders.pdfs_spider import PDFScraperSpider

# Running the Scrapy spider
if __name__ == "__main__":
    process = CrawlerProcess(get_project_settings())
    process.crawl(PDFScraperSpider)
    process.start()
