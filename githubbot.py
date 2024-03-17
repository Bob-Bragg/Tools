import requests
from bs4 import BeautifulSoup
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from io import BytesIO
import logging

# Setup logging
logging.basicConfig(filename='github_search_results.log', filemode='w', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_github_api_key():
    use_key = input("Do you want to use a GitHub API key for higher rate limits? (yes/no): ").strip().lower()
    if use_key == 'yes':
        api_key = input("Enter your GitHub API key: ").strip()
        return api_key
    return None

def get_search_query():
    print("\nEnter search criteria for GitHub users:")
    type = input("Type (user/org): ").strip()
    name = input("Name: ").strip()
    num_repos = input("Number of repositories (e.g., >10, <50, 10..50): ").strip()
    location = input("Location: ").strip()
    repo_language = input("Repository language: ").strip()
    created_at = input("Account creation date (YYYY-MM-DD, e.g., >2020-01-01): ").strip()
    followers = input("Number of followers (e.g., >100): ").strip()
    is_sponsorable = input("Sponsorable (yes/no): ").strip()

    query = "+".join(filter(None, [
        f"type:{type}" if type else "",
        name,
        f"repos:{num_repos}" if num_repos else "",
        f"location:{location}" if location else "",
        f"language:{repo_language}" if repo_language else "",
        f"created:{created_at}" if created_at else "",
        f"followers:{followers}" if followers else "",
        "is:sponsorable:true" if is_sponsorable.lower() == 'yes' else ""
    ]))

    return query

def fetch_from_github_api(query, search_type='users', api_key=None):
    headers = {'Accept': 'application/vnd.github.v3+json'}
    if api_key:
        headers['Authorization'] = f'token {api_key}'

    url = f"https://api.github.com/search/{search_type}?q={query}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        logging.error(f"API request failed with status code {response.status_code}: {response.json().get('message')}")
        return None

def scrape_github_profile(url):
    # Note: Scraping GitHub profiles is against GitHub's Terms of Service.
    # This function is provided for educational purposes only.
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        bio = soup.select_one('div.user-profile-bio').text.strip() if soup.select_one('div.user-profile-bio') else "No bio available"
        return bio
    except Exception as e:
        logging.error(f"Error scraping GitHub profile: {e}")
        return "Scraping error"

def create_pdf(results, filename="search_results.pdf"):
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    y_position = height - 100

    for item in results.get('items', []):
        username = item.get('login')
        user_url = item.get('html_url')
        bio = scrape_github_profile(user_url)  # Scraping for educational purposes

        try:
            avatar_url = item.get('avatar_url', '')
            response = requests.get(avatar_url)
            img = ImageReader(BytesIO(response.content))
            c.drawImage(img, 40, y_position - 45, width=50, height=50)

            text = f"Username: {username}\nBio: {bio}\nURL: {user_url}"
            c.drawString(100, y_position, text)
            c.linkURL(user_url, (40, y_position - 45, 40 + 50, y_position + 5), thickness=1)
            y_position -= 100

            if y_position < 100:
                c.showPage()
                y_position = height - 100
        except Exception as e:
            logging.error(f"Failed to add user {username} to PDF: {e}")

    c.save()
    logging.info(f"PDF created: {filename}")

def main_menu():
    api_key = get_github_api_key()

    while True:
        choice = input("\n1. Search GitHub Users\n2. Exit\nEnter your choice (1-2): ").strip()
        if choice == '1':
            query = get_search_query()
            results = fetch_from_github_api(query, api_key=api_key)
            if results:
                create_pdf(results, "GitHub_Search_Results.pdf")
                print("Search results have been saved to GitHub_Search_Results.pdf")
            else:
                print("Failed to fetch results or no results to display.")
        elif choice == '2':
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main_menu()

