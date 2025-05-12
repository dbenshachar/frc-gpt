import requests
import os
import re
import traceback

GITHUB_API_URL = "https://api.github.com"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
assert GITHUB_TOKEN is not None, "GITHUB_TOKEN must be set"
API_QUERY = "filename:WPILib-License.md language:Java"

SOURCE_CODE_DIR = "src/main/java"
OUTPUT_FILE = "data/data.txt"
SEPARATOR_TOKEN = "\n\n" + "="*50 + " FILE SEPARATOR " + "="*50 + "\n\n"

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json",
}

PER_PAGE = 1
PAGES = 1