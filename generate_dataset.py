import base64
import datetime
import requests
import os
from dotenv import load_dotenv

load_dotenv()

GITHUB_API_URL = "https://api.github.com"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
assert GITHUB_TOKEN is not None, "GITHUB_TOKEN must be set"
API_QUERY = "reefscape in:name OR crescendo in:name OR chargedup in:name OR charged-up in:name OR rapidreact in:name OR rapid-react in:name"

SOURCE_CODE_DIR = "data"
SEPARATOR_TOKEN = "\n\n" + "="*50 + " FILE SEPARATOR " + "="*50 + "\n\n"

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json",
}

PER_PAGE = 50
PAGES = 1

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
            base = filename[:-4]  # remove .java
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

def get_default_branch(owner, repo_name):
    """
    Attempts to fetch the default branch of a GitHub repository first.
    If the default branch is not found or an error occurs, it then
    fetches all branches, sorts them by the latest commit date, and
    returns the name of the most recently committed branch.
    Returns 'main' as a final fallback if neither the default nor
    any other branch can be determined.
    """
    try:
        # --- First attempt: Get the default branch from repo details ---
        repo_url = f"https://api.github.com/repos/{owner}/{repo_name}"
        repo_response = requests.get(repo_url)
        repo_response.raise_for_status() # Raise an exception for bad status codes
        repo_data = repo_response.json()

        default_branch = repo_data.get("default_branch")
        if default_branch:
            print(f"Found default branch '{default_branch}' for {owner}/{repo_name}.")
            return default_branch
        else:
            print(f"Default branch not found in repo details for {owner}/{repo_name}. Falling back to finding most recent branch by commit.")

        # --- Fallback: Find the most recent branch by commit date ---
        branches_url = f"https://api.github.com/repos/{owner}/{repo_name}/branches"
        branches_response = requests.get(branches_url)
        branches_response.raise_for_status() # Raise an exception for bad status codes
        branches_data = branches_response.json()

        if not branches_data:
            print(f"No branches found for {owner}/{repo_name}. Using 'main' as ultimate fallback.")
            return "main"

        # Sort branches by the commit date in descending order
        # We fetch the full commit details to get the accurate date
        def get_commit_date(branch):
            commit_url = branch['commit']['url']
            try:
                commit_response = requests.get(commit_url)
                commit_response.raise_for_status()
                commit_data = commit_response.json()
                # Use committer date, fallback to author date
                date_str = commit_data['commit']['committer'].get('date') or commit_data['commit']['author'].get('date')
                if date_str:
                    # Parse ISO 8601 format
                    return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            except requests.exceptions.RequestException as e:
                print(f"Warning: Could not fetch commit details for {branch['name']}: {e}")
            except ValueError:
                 print(f"Warning: Could not parse date format for commit {branch['commit']['sha']}.")
            return datetime.min # Return earliest possible date if no date or error

        # Sort the branches list based on the commit date
        branches_data.sort(key=get_commit_date, reverse=True)

        # The first branch after sorting is the most recent one
        most_recent_branch = branches_data[0]['name']
        print(f"Most recent branch by commit for {owner}/{repo_name} is '{most_recent_branch}'.")
        return most_recent_branch

    except requests.exceptions.RequestException as e:
        # This block catches errors from any of the requests.get() calls
        print(f"Error fetching data for {owner}/{repo_name}: {e}")
        # Attempt to get default branch as fallback in case of API error
        try:
            repo_url_fallback = f"https://api.github.com/repos/{owner}/{repo_name}"
            repo_response_fallback = requests.get(repo_url_fallback)
            repo_response_fallback.raise_for_status()
            repo_data_fallback = repo_response_fallback.json()
            default_branch_fallback = repo_data_fallback.get("default_branch")
            if default_branch_fallback:
                print(f"Using default branch '{default_branch_fallback}' as fallback due to API error.")
                return default_branch_fallback
        except requests.exceptions.RequestException:
            # If even the fallback default branch fetch fails
            pass # Ignore this error, proceed to ultimate fallback

        print(f"Using 'main' as ultimate fallback due to API error and unable to get default branch.")
        return "main"
    except Exception as e:
        # Catch any other unexpected errors during processing
        print(f"An unexpected error occurred for {owner}/{repo_name}: {e}")
        # Attempt to get default branch as fallback in case of unexpected error
        try:
            repo_url_fallback = f"https://api.github.com/repos/{owner}/{repo_name}"
            repo_response_fallback = requests.get(repo_url_fallback)
            repo_response_fallback.raise_for_status()
            repo_data_fallback = repo_response_fallback.json()
            default_branch_fallback = repo_data_fallback.get("default_branch")
            if default_branch_fallback:
                print(f"Using default branch '{default_branch_fallback}' as fallback due to unexpected error.")
                return default_branch_fallback
        except requests.exceptions.RequestException:
             # If even the fallback default branch fetch fails
            pass # Ignore this error, proceed to ultimate fallback

        print(f"Using 'main' as ultimate fallback due to unexpected error and unable to get default branch.")
        return "main"

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
    branch = get_default_branch(owner, repo_name)
    print(f"Fetching Java files from repository: {full_name} (Branch: {branch})")

    # Fetch the repository tree
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo_name}/git/trees/{branch}?recursive=1"
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
