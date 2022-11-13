import os

from github import Github

github_client = Github(os.environ["GITHUB_API_TOKEN"])
