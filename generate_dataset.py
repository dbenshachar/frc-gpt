import base64
import requests
import os
from dotenv import load_dotenv

load_dotenv()

GITHUB_API_URL = "https://api.github.com"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
assert GITHUB_TOKEN is not None, "GITHUB_TOKEN must be set"
API_QUERY = "language:java path:src/main/ is:public"

SOURCE_CODE_DIR = "data"
SEPARATOR_TOKEN = "\n\n" + "="*50 + " FILE SEPARATOR " + "="*50 + "\n\n"

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json",
}

PER_PAGE = 100
PAGES = 10

def create_directory(directory_name):
    """
    Creates a directory if it does not already exist.

    Args:
        directory_name (str): The name of the directory to create.
    """
    if not os.path.exists(directory_name):
        os.makedirs(directory_name)
        print(f"Created directory: {directory_name}")
    else:
        print(f"Directory already exists: {directory_name}")

def fetch_repositories(query, per_page, pages):
    """
    Fetches repositories from GitHub based on the given query.

    Args:
        query (str): The search query to use.
        per_page (int): Number of repositories to fetch per page.
        pages (int): Number of pages to fetch.

    Returns:
        list: A list of (owner, repository name) tuples.
    """
    repositories = []
    for page in range(1, pages + 1):
        print(f"Fetching page {page} of repository results...")
        url = f"{GITHUB_API_URL}/search/repositories?q={query}&per_page={per_page}&page={page}"
        try:
            response = requests.get(url, headers=HEADERS)
            print(f"Request Status Code: {response.status_code}")
            response.raise_for_status()
            data = response.json()
            for item in data.get("items", []):
                repositories.append((item["owner"]["login"], item["name"]))
            print(f"Fetched {len(data.get('items', []))} repositories from page {page}.")
        except requests.exceptions.RequestException as e:
            print(f"Error fetching repositories on page {page}: {e}")
            break
    return repositories

def fetch_java_files(owner, repo_name, source_code_dir):
    """
    Fetches the content of all .java files in the src/main directory of a given repository.

    Args:
        owner (str): The GitHub username or organization name of the repository owner.
        repo_name (str): The name of the repository.
        source_code_dir (str): The directory to save the source code to.
    """
    print(f"Fetching Java files from repository: {owner}/{repo_name}")
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo_name}/git/trees/main?recursive=1"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        java_files_content = ""
        for file in data.get('tree', []):
            if file['path'].startswith("src/main/") and file['path'].endswith(".java"):
                file_url = f"{GITHUB_API_URL}/repos/{owner}/{repo_name}/contents/{file['path']}"
                file_response = requests.get(file_url, headers=HEADERS)
                file_response.raise_for_status()
                file_data = file_response.json()
                if 'content' in file_data:
                    file_content = base64.b64decode(file_data['content']).decode('utf-8')
                    java_files_content += file_content + SEPARATOR_TOKEN
                    print(f"Fetched and added content from: {file['path']}")

        output_file_path = os.path.join(source_code_dir, f"{owner}_{repo_name}.txt")
        with open(output_file_path, "w", encoding="utf-8") as output_file:
            output_file.write(java_files_content)
        print(f"All Java files content saved to: {output_file_path}")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching Java files from repository {owner}/{repo_name}: {e}")
    except KeyError as e:
        print(f"KeyError while processing repository {owner}/{repo_name}: {e}.")
    except Exception as e:
        print(f"Unexpected error with repository {owner}/{repo_name}: {e}")

def main():
    """
    Main function to orchestrate fetching repositories and their Java files.
    """
    create_directory(SOURCE_CODE_DIR)
    print("Fetching repositories...")
    repositories = fetch_repositories(API_QUERY, PER_PAGE, PAGES)
    print(f"Total repositories fetched: {len(repositories)}")

    if not repositories:
        print("No repositories found. Exiting.")
        return

    for owner, repo_name in repositories:
        fetch_java_files(owner, repo_name, SOURCE_CODE_DIR)

if __name__ == "__main__":
    main()
    print("All repositories processed.")
    print(f"Data saved: {SOURCE_CODE_DIR}")