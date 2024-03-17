import requests
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from io import BytesIO
import logging

# Setup logging
logging.basicConfig(filename='github_search_results.log', level=logging.INFO, format='%(asctime)s - %(message)s')

def fetch_from_github_api(query, search_type='users'):
    """
    Fetches data from GitHub API based on the search query and type, with error handling.
    """
    base_url = 'https://api.github.com/search/'
    url = f"{base_url}{search_type}?q={query}"
    headers = {'Accept': 'application/vnd.github.v3+json'}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        logging.error(f"HTTPError during API call: {e}")
    except requests.exceptions.RequestException as e:
        logging.error(f"RequestException during API call: {e}")
    return {'items': []}  # Return an empty list on error

def create_pdf(results, filename="search_results.pdf", search_type='users'):
    """
    Creates a PDF file with the search results, including clickable links and profile avatars.
    Error handling for issues in PDF generation and image fetching.
    """
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    y_position = height - 100

    for item in results.get('items', []):
        try:
            name = item.get('login', item.get('name', 'N/A'))
            url = item['html_url']
            avatar_url = item.get('avatar_url', item.get('owner', {}).get('avatar_url', ''))

            response = requests.get(avatar_url)
            img = ImageReader(BytesIO(response.content))
            c.drawImage(img, 40, y_position - 20, width=60, height=60)

            c.drawString(110, y_position, name)
            c.linkURL(url, (100, y_position - 20, 500, y_position + 20), thickness=1)

            y_position -= 100

            if y_position < 100:
                c.showPage()
                y_position = height - 100
        except Exception as e:
            logging.error(f"Error generating PDF content: {e}")

    c.save()

def log_results(results, search_type='users'):
    """
    Logs the search results.
    """
    for item in results.get('items', []):
        try:
            name = item.get('login', item.get('name', 'N/A'))
            url = item['html_url']
            logging.info(f"{search_type.capitalize()} Name: {name}, URL: {url}")
        except Exception as e:
            logging.error(f"Error logging result: {e}")

def get_user_search_criteria():
    """
    Gathers detailed search criteria for GitHub user searches from the user.
    """
    print("Enter search criteria for GitHub users:")
    type = input("Type (user/org): ").strip()
    name = input("Name: ").strip()
    num_repos = input("Number of repositories (e.g., >10, <50, 10..50): ").strip()
    location = input("Location: ").strip()
    repo_language = input("Repository language: ").strip()
    created_at = input("Account creation date (YYYY-MM-DD, e.g., >2020-01-01): ").strip()
    followers = input("Number of followers (e.g., >100): ").strip()
    is_sponsorable = input("Sponsorable (yes/no): ").strip().lower()

    # Building the query with error handling for inputs
    query_parts = []
    if type in ['user', 'org']:
        query_parts.append(f"type:{type}")
    if name:
        query_parts.append(f"user:{name}")
    if num_repos:
        query_parts.append(f"repos:{num_repos}")
    if location:
        query_parts.append(f"location:\"{location}\"")
    if repo_language:
        query_parts.append(f"language:{repo_language}")
    if created_at:
        query_parts.append(f"created:{created_at}")
    if followers:
        query_parts.append(f"followers:{followers}")
    if is_sponsorable in ['yes', 'no']:
        query_parts.append(f"is:sponsorable:{is_sponsorable == 'yes'}")

    return " ".join(query_parts)

def main_menu():
    while True:
        print("\nGitHub Search CLI")
        print("1. Search GitHub Users")
        print("2. Search GitHub Repositories")
        print("3. Exit")
        choice = input("Enter your choice (1-3): ").strip()

        if choice == '1':
            query = get_user_search_criteria()
            results = fetch_from_github_api(query, 'users')
            log_results(results, 'users')
            pdf_filename = "github_users_search_results.pdf"
            create_pdf(results, pdf_filename, 'users')
            print(f"Results have been logged and saved to {pdf_filename}.")
        elif choice == '2':
            query = input("Enter your search query for GitHub repositories: ").strip()
            results = fetch_from_github_api(query, 'repositories')
            log_results(results, 'repositories')
            pdf_filename = "github_repositories_search_results.pdf"
            create_pdf(results, pdf_filename, 'repositories')
            print(f"Results have been logged and saved to {pdf_filename}.")
        elif choice == '3':
            break
        else:
            print("Invalid choice, please try again.")

if __name__ == "__main__":
    main_menu()

