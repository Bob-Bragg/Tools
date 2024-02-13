import requests
from bs4 import BeautifulSoup
import csv
import logging
import time
import readline

# Configure logging
logging.basicConfig(filename='scraping_log.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Global Variables
page = 1
cves = []

# Auto-completion and caching functions

def load_cves_from_cache():
    try:
        with open('cve_cache.txt', 'r') as cache_file:
            return [line.strip() for line in cache_file.readlines()]
    except FileNotFoundError:
        return []

def complete(text, state):
    cve_cache = load_cves_from_cache()
    options = [cmd for cmd in cve_cache if cmd.startswith(text)]
    if state < len(options):
        return options[state]
    else:
        return None

def save_cves_to_cache():
    with open('cve_cache.txt', 'w') as cache_file:
        for cve in cves:
            cache_file.write(cve[0] + '\n')

# Setup readline for auto-completion
readline.set_completer(complete)
readline.parse_and_bind("tab: complete")

# Function Definitions

def get_user_input():
    try:
        search_year = int(input("Enter the year to search for CVEs (e.g., 2023), or 0 to search specific CVEs: "))
        if search_year == 0:
            specific_cves = input("Enter CVE IDs separated by commas (e.g., CVE-2021-34527, CVE-2022-21882): ")
            specific_cves = [cve.strip() for cve in specific_cves.split(',')]
            return 0, specific_cves
        return search_year, []
    except ValueError:
        print("Invalid input.")
        exit()

def scrape_cisa_for_cves(year, specific_cves):
    global page
    try:
        while True:
            url = f"https://www.cisa.gov/known-exploited-vulnerabilities-catalog?page={page}"
            response = requests.get(url)
            page += 1

            if response.status_code != 200:
                logging.error(f"Failed to retrieve page {page}. Status code: {response.status_code}")
                break

            soup = BeautifulSoup(response.content, "html.parser")
            cve_entries = soup.find_all("div", class_="c-view__row")

            if not cve_entries:
                logging.info("No more CVEs found. Exiting.")
                break

            for entry in cve_entries:
                number_element = entry.find("h3", class_="c-teaser__title")
                name_element = entry.find("div", class_='c-teaser__vuln-name')
                summary_element = entry.find("div", class_="c-teaser__summary")

                if number_element and name_element and summary_element:
                    number = number_element.text.strip()
                    title = name_element.text.strip()
                    summary = summary_element.text.strip()

                    cve_year = int(number.split('-')[1])
                    if year == 0 and number not in specific_cves:
                        continue
                    append_cve_data(number, title, summary)
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")

def append_cve_data(number, title, summary):
    googleNewsUrl = generate_google_news_url(number)
    githubSearchUrl = generate_github_search_url(number)
    cves.append([number, title, summary, googleNewsUrl, githubSearchUrl])
    print(f"Scraped CVE: {number}")  # Troubleshooting print

def generate_google_news_url(cve):
    return f"https://news.google.com/search?q={cve}+exploit+PoC&hl=en-US&gl=US&ceid=US:en"

def generate_github_search_url(cve):
    return f"https://google.com/search?q=site:github.com+{cve}+exploit+PoC"

def write_data_to_csv():
    with open('cisa_kevs.csv', mode='w', newline='', encoding='utf-8') as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(['CVE Number', 'Title', 'Summary', 'Google News Link', 'GitHub Search Link'])
        for cve in cves:
            csv_writer.writerow(cve)
    print("Data written to CSV successfully.")

# Main Function

def main():
    search_year, specific_cves = get_user_input()
    scrape_cisa_for_cves(search_year, specific_cves)
    save_cves_to_cache()  # Save scraped CVEs to cache
    write_data_to_csv()

if __name__ == "__main__":
    main()

