import base64
import requests
import os
from dotenv import load_dotenv

load_dotenv()

GITHUB_API_URL = "https://api.github.com"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
assert GITHUB_TOKEN is not None, "GITHUB_TOKEN must be set"
API_QUERY = "path:.wpilib path:src/main/ is:public"
API_QUERY = "path:.wpilib is:public"

SOURCE_CODE_DIR = "data"
SEPARATOR_TOKEN = "\n\n" + "="*50 + " FILE SEPARATOR " + "="*50 + "\n\n"

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json",
}

PER_PAGE = 1
PAGES = 100

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

def load_seen_repos(directory):
    """
    Loads seen repository names from filenames in the data directory.

    Args:
        directory (str): Path to the directory containing downloaded repo files.

    Returns:
        set: Set of "owner/repo" strings that have already been processed.
    """
    seen = set()
    for filename in os.listdir(directory):
        if filename.endswith(".txt") and "_" in filename:
            base = filename[:-5]  # remove .java
            parts = base.split("_", 1)
            if len(parts) == 2:
                owner, repo = parts
                seen.add(f"{owner}/{repo}")
    return seen

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
            print(f"Data fetched for page {page}: {data}")
            for item in data.get("items", []):
                repositories.append((item["owner"]["login"], item["name"]))
            print(f"Fetched {len(data.get('items', []))} repositories from page {page}.")
        except Exception as e:
            print(f"Error fetching repositories on page {page}: {e}")
    return repositories

def get_most_recent_branch(owner, repo_name):
    """
    Get the most recently pushed branch for the given repository.

    Args:
        owner (str): The owner of the repository.
        repo_name (str): The name of the repository.

    Returns:
        str: The name of the most recently pushed branch.
    """
    url = f"https://api.github.com/repos/{owner}/{repo_name}/branches"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        branches = response.json()

        # Sort branches by the date of the latest commit (last commit date)
        sorted_branches = sorted(branches, key=lambda b: b['commit']['commit']['author']['date'], reverse=True)

        # Get the most recent branch (the first in the sorted list)
        most_recent_branch = sorted_branches[0]['name']
        print(f"Most recent branch in {owner}/{repo_name}: {most_recent_branch}")
        return most_recent_branch
    except Exception as e:
        print(f"Error fetching branches from repository {owner}/{repo_name}: {e}")
        return "main"  # Fallback to 'main' if there is an error or no branches

def fetch_java_files(owner, repo_name, source_code_dir, seen_repos):
    """
    Fetches the content of all .java files in the src/main directory of a given repository.
    Uses the most recently pushed branch instead of 'main'.

    Args:
        owner (str): The owner of the repository.
        repo_name (str): The name of the repository.
        source_code_dir (str): The directory to save the source code to.
        seen_repos (set): A set of repositories already processed to avoid duplication.
    """
    full_name = f"{owner}/{repo_name}"
    if full_name in seen_repos:
        print(f"Skipping already processed repo: {full_name}")
        return

    # Fetch the most recent branch dynamically
    most_recent_branch = get_most_recent_branch(owner, repo_name)
    print(f"Fetching Java files from repository: {full_name} (Branch: {most_recent_branch})")

    # Fetch the repository tree
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo_name}/git/trees/{most_recent_branch}?recursive=1"
    print(f"Fetching repository tree from: {url}")
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()

        # Check if src/main exists in the repo structure
        src_main_exists = any(file['path'].startswith("src/main/") for file in data.get('tree', []))

        if not src_main_exists:
            print(f"src/main/ directory not found in repository {full_name}. Skipping repository.")
            return

        java_files_content = ""
        found_java_file = False  # Flag to track if any Java files are found

        for file in data.get('tree', []):
            if file['path'].startswith("src/main/") and file['path'].endswith(".java"):
                file_url = f"{GITHUB_API_URL}/repos/{owner}/{repo_name}/contents/{file['path']}"
                file_response = requests.get(file_url, headers=HEADERS)
                file_response.raise_for_status()
                file_data = file_response.json()
                if 'content' in file_data:
                    file_content = base64.b64decode(file_data['content']).decode('utf-8')
                    java_files_content += file_content + SEPARATOR_TOKEN
                    found_java_file = True  # Mark as found at least one .java file
                    print(f"Fetched and added content from: {file['path']}")

        if found_java_file:
            output_file_path = os.path.join(source_code_dir, f"{owner}_{repo_name}.txt")
            with open(output_file_path, "w", encoding="utf-8") as output_file:
                output_file.write(java_files_content)
            print(f"All Java files content saved to: {output_file_path}")
            seen_repos.add(full_name)
        else:
            print(f"No Java files found in {full_name}. Skipping this repository.")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching Java files from repository {full_name}: {e}")
    except KeyError as e:
        print(f"KeyError while processing repository {full_name}: {e}.")
    except Exception as e:
        print(f"Unexpected error with repository {full_name}: {e}")

def main():
    """
    Main function to orchestrate fetching repositories and their Java files.
    """
    create_directory(SOURCE_CODE_DIR)
    seen_repos = load_seen_repos(SOURCE_CODE_DIR)
    print(f"Loaded {len(seen_repos)} previously seen repos.")

    print("Fetching repositories...")
    repositories = fetch_repositories(API_QUERY, PER_PAGE, PAGES)
    print(f"Total repositories fetched: {len(repositories)}")

    for owner, repo_name in repositories:
        fetch_java_files(owner, repo_name, SOURCE_CODE_DIR, seen_repos)

if __name__ == "__main__":
    main()
    print("All repositories processed.")
    print(f"Data saved: {SOURCE_CODE_DIR}")
