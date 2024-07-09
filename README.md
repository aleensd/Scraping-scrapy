# Scraping

## About this project

A scraper for one of Sweden's premier legal to scrape PDF URLs and metadata from this website https://www.domstol.se/hogsta-domstolen/avgoranden/.

## Prerequisites

- Python 3.11
- Scrapy
- Required Python packages (requirements.txt)

## Installation
- Run **make venv** to install python packages
- Run **python run_dev.py** to run the script or  **make run**

## Usage

- The scraper Initiates API requests to fetch initial pages of data.
- Parses JSON response from API, extracts PDF links, and initiates requests to scrape PDF metadata
- Latest 10 PDFs are downloaded to the specified directory.
