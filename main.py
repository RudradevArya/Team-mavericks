import requests

# Constants (set your actual GitHub repo info and headers)
OWNER = "your-username"
REPO = "your-repo"
HEADERS = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer YOUR_GITHUB_TOKEN"
}

def fetch_from_github(endpoint, params=None):
    """Generic GitHub GET request"""
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/{endpoint}"
    response = requests.get(url, headers=HEADERS, params=params)
    response.raise_for_status()
    return response.json()

def get_repo_details():
    return fetch_from_github("")

def get_pull_requests(state="open"):
    return fetch_from_github("pulls", {"state": state})

def get_pr_details(pr_number):
    return fetch_from_github(f"pulls/{pr_number}")

def get_issues():
    return fetch_from_github("issues")

def get_commits():
    return fetch_from_github("commits")

def print_repo_info(repo):
    print("\n--- Repository Info ---")
    print(f"Name: {repo.get('name')}")
    print(f"Description: {repo.get('description')}")
    print(f"Default Branch: {repo.get('default_branch')}")
    print(f"Visibility: {repo.get('visibility')}")

def print_pull_requests(prs):
    print("\n--- Open Pull Requests ---")
    for pr in prs[:5]:
        print(f"PR #{pr['number']}: {pr['title']} by {pr['user']['login']}")

def print_commits(commits):
    print("\n--- Recent Commits ---")
    for commit in commits[:5]:
        sha = commit['sha'][:7]
        message = commit['commit']['message']
        print(f"{sha}: {message}")

def print_issues(issues):
    print("\n--- Open Issues (includes PRs) ---")
    for issue in issues[:5]:
        kind = "PR" if "pull_request" in issue else "Issue"
        print(f"Issue #{issue['number']}: {issue['title']} ({kind})")

def print_pr_details(pr):
    print(f"\n--- Details of PR #{pr['number']} ---")
    print(f"Title: {pr['title']}")
    print(f"State: {pr['state']}")
    print(f"Mergeable: {pr.get('mergeable')}")
    print(f"Created at: {pr['created_at']}")
    print(f"Changed files: {pr['changed_files']}")

# ---- MAIN ----
if __name__ == "__main__":
    repo = get_repo_details()
    print_repo_info(repo)

    prs = get_pull_requests()
    print_pull_requests(prs)

    commits = get_commits()
    print_commits(commits)

    issues = get_issues()
    print_issues(issues)

    if prs:
        pr_details = get_pr_details(prs[0]["number"])
        print_pr_details(pr_details)
