import asyncio
import os
import urllib.parse
from datetime import datetime
from pyppeteer import launch
from pyppeteer.errors import NetworkError, PageError
import websockets.exceptions
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)

# User agent to mimic Google bot
user_agent = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"

# Create a directory to save the articles
output_directory = "Saved_Articles"
if not os.path.exists(output_directory):
    os.makedirs(output_directory)

# Function to scrape and save an article with retries
async def scrape_and_save_article(browser, link, idx, search_query, max_retries=3):
    for retry in range(max_retries):
        page = None
        try:
            page = await browser.newPage()
            await page.setUserAgent(user_agent)
            await page.goto(link)
            await asyncio.sleep(2)  # Adjust sleep time as needed

            # Get the entire HTML content of the page
            page_content = await page.content()

            # Extract the article title from the page
            title_element = await page.querySelector("h1")  # Adjust selector as needed
            article_title = "UnknownTitle"
            if title_element:
                article_title = await page.evaluate('(element) => element.textContent', title_element)
            valid_title = ''.join(char for char in article_title if char.isalnum() or char.isspace())

            # Create a filename
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            file_name = os.path.join(output_directory, f"{timestamp}_{search_query}_{valid_title}_{idx + 1}.html")

            with open(file_name, "w", encoding="utf-8") as file:
                file.write(page_content)

            logging.info(f"Article {idx + 1} saved: {file_name}")
            return
        except (NetworkError, PageError, websockets.exceptions.ConnectionClosedError) as e:
            logging.warning(f"Retrying (attempt {retry + 1}) - {str(e)}")
            await asyncio.sleep(5)
        finally:
            if page:
                await page.close()

    logging.error(f"Failed to scrape and save article {idx + 1} after {max_retries} retries.")

# Function to get a limited number of article links
async def get_article_links(query, max_articles):
    search_url = f"https://news.google.com/search?q={urllib.parse.quote_plus(query)}&hl=en-US&gl=US&ceid=US:en"
    browser = await launch(headless=True)
    page = await browser.newPage()
    await page.setUserAgent(user_agent)
    await page.goto(search_url)
    await page.waitForSelector('article')

    article_elements = await page.querySelectorAll('article')
    links = [await page.evaluate('(article) => article.querySelector("a") ? article.querySelector("a").href : null', article) for article in article_elements]

    await browser.close()
    return links[:max_articles]

# Function to perform the scraping process
async def scrape_articles(search_query, max_articles):
    browser = None
    try:
        article_links = await get_article_links(search_query, max_articles)
        browser = await launch(headless=True)
        tasks = [scrape_and_save_article(browser, link, idx, search_query) for idx, link in enumerate(article_links)]
        await asyncio.gather(*tasks)
    finally:
        if browser:
            await browser.close()

# Main loop for user interaction
async def main():
    while True:
        search_query = input("Enter your search query (or 'exit' to quit): ")
        if search_query.lower() == 'exit':
            break

        max_articles_input = input("Enter the maximum number of articles to scrape (default 10): ")
        max_articles = int(max_articles_input) if max_articles_input.isdigit() else 10

        logging.info(f"Scraping up to {max_articles} articles for query: {search_query}")
        await scrape_articles(search_query, max_articles)

    logging.info("Scraping completed.")

if __name__ == "__main__":
    asyncio.run(main())
