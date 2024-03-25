import asyncio
import os
import urllib.parse
from datetime import datetime
from pyppeteer import launch
from pyppeteer.errors import NetworkError, PageError
import websockets.exceptions
import logging
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import random

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize the UserAgent object for user-agent rotation
fake_user_agent = UserAgent()

# Directory for saving articles
output_directory = "Saved_Articles"
if not os.path.exists(output_directory):
    os.makedirs(output_directory)

# Load processed URLs from a file at the start
def load_processed_urls():
    try:
        with open('processed_urls.txt', 'r') as file:
            return set(line.strip() for line in file)
    except FileNotFoundError:
        return set()

# Save processed URLs to the file
def save_processed_urls(urls):
    with open('processed_urls.txt', 'w') as file:
        for url in urls:
            file.write(url + '\n')

processed_urls = load_processed_urls()

async def goto_with_retry(page, url, max_retries=5):
    retry_delay = 1  # Initial delay
    for attempt in range(max_retries):
        try:
            await page.goto(url, {'waitUntil': 'networkidle2'})
            return
        except Exception as e:
            logging.warning(f"Retry {attempt + 1} for {url}: {e}")
            await asyncio.sleep(retry_delay)
            retry_delay *= 2  # Exponential backoff
    raise Exception(f"Failed to load {url} after {max_retries} retries")

async def scrape_and_save_article(browser, link, idx, search_query):
    if link in processed_urls:
        logging.info(f"Skipping already processed article: {link}")
        return
    else:
        processed_urls.add(link)

    page = await browser.newPage()
    await page.setUserAgent(fake_user_agent.random)
    await page.setViewport({
        'width': random.randint(1024, 1920),
        'height': random.randint(768, 1080),
        'deviceScaleFactor': random.randint(1, 3)
    })

    # Additional headers can be customized here
    await page.setExtraHTTPHeaders({
        'Accept-Language': 'en-US',
        'Referer': 'https://www.google.com/'
    })

    try:
        await asyncio.sleep(random.uniform(2, 5))  # Random delay
        await goto_with_retry(page, link)

        content = await page.content()
        soup = BeautifulSoup(content, 'lxml')
        title_element = soup.find('h1')
        title = title_element.get_text(strip=True) if title_element else "UnknownTitle"
        valid_title = ''.join(c for c in title if c.isalnum() or c.isspace())

        filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{idx+1}_{valid_title}.html"
        filepath = os.path.join(output_directory, filename.replace(" ", "_"))
        with open(filepath, "w", encoding="utf-8") as file:
            file.write(f'<a href="{link}" target="_blank">Source URL</a>\n\n{content}')

        logging.info(f"Article {idx + 1} saved: {filepath}")
    except (NetworkError, PageError, websockets.exceptions.ConnectionClosedError) as e:
        logging.error(f"Error scraping article {idx + 1}: {e}")
    finally:
        if page and not page.isClosed():
            await page.close()

async def get_article_links(browser, query, max_articles=10):
    page = await browser.newPage()
    await page.setUserAgent(fake_user_agent.random)
    await page.goto(f"https://news.google.com/search?q={urllib.parse.quote_plus(query)}", {'waitUntil': 'networkidle2'})
    await page.waitForSelector('article')

    elements = await page.querySelectorAll('article')
    links = await asyncio.gather(*(page.evaluate('(element) => element.querySelector("a").href', el) for el in elements))

    await page.close()
    return links[:max_articles]

async def scrape_articles(query, max_articles=10):
    browser = await launch()
    try:
        links = await get_article_links(browser, query, max_articles)
        tasks = [scrape_and_save_article(browser, link, idx, query) for idx, link in enumerate(links)]
        await asyncio.gather(*tasks)
    finally:
        await browser.close()

async def main():
    while True:
        query = input("Enter search query ('exit' to quit): ").strip()
        if query.lower() == 'exit':
            break

        max_articles = input("Max articles to scrape (default 10): ").strip()
        max_articles = int(max_articles) if max_articles.isdigit() else 10

        await scrape_articles(query, max_articles)
        print("\nQuery completed. You can start a new search or exit.")
        
    save_processed_urls(processed_urls)  # Save the updated list of processed URLs when exiting

if __name__ == "__main__":
    asyncio.run(main())

