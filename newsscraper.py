import asyncio
from pyppeteer import launch
import urllib.parse

class GoogleScraper:
    def __init__(self, query, timeframe='18h'):
        base_url = 'https://news.google.com/search'
        encoded_query = urllib.parse.quote_plus(f'{query} when:{timeframe}')
        self.url = f'{base_url}?q={encoded_query}&hl=en-US&gl=US&ceid=US:en'
        self.news_articles = []

    async def scrape(self):
        browser = await launch()
        page = await browser.newPage()
        await page.goto(self.url)
        await page.waitForSelector('article')

        article_elements = await page.querySelectorAll('article')

        for article in article_elements:
            article_text = await page.evaluate('(article) => article.innerText', article)
            article_link = await page.evaluate('(article) => article.querySelector("a") ? article.querySelector("a").href : null', article)
            self.news_articles.append({'article': article_text, 'article_links': article_link})

        await browser.close()

    def display_articles(self):
        for count, article in enumerate(self.news_articles, 1):
            print(f"{count}. {article['article']}\nLink: {article['article_links']}")

async def main():
    scraper = GoogleScraper('threatactor', '18h')
    await scraper.scrape()
    scraper.display_articles()

asyncio.run(main())

