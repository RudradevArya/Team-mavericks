import requests

def get_repo_details():
    url = f"https://api.github.com/repos/{OWNER}/{REPO}"
    response = requests.get(url, headers=HEADERS)
    return response.json()

# ---- Fetch All Pull Requests ----


def get_pull_requests(state="open"):
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/pulls"
    params = {"state": state}
    response = requests.get(url, headers=HEADERS, params=params)
    return response.json()

# ---- Fetch Single PR Details ----


def get_pr_details(pr_number):
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/pulls/{pr_number}"
    response = requests.get(url, headers=HEADERS)
    return response.json()

# ---- Fetch All Issues (including PRs) ----


def get_issues():
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/issues"
    response = requests.get(url, headers=HEADERS)
    return response.json()

# ---- Fetch All Commits ----


def get_commits():
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/commits"
    response = requests.get(url, headers=HEADERS)
    return response.json()


# ---- MAIN ----
if __name__ == "__main__":
    print("\n--- Repository Info ---")
    repo = get_repo_details()
    print(f"Name: {repo.get('name')}")
    print(f"Description: {repo.get('description')}")
    print(f"Default Branch: {repo.get('default_branch')}")
    print(f"Visibility: {repo.get('visibility')}")

    print("\n--- Open Pull Requests ---")
    prs = get_pull_requests()
    for pr in prs[:5]:  # limit to 5
        print(f"PR #{pr['number']}: {pr['title']} by {pr['user']['login']}")

    print("\n--- Recent Commits ---")
    commits = get_commits()
    for commit in commits[:5]:  # show last 5 commits
        print(f"{commit['sha'][:7]}: {commit['commit']['message']}")

    print("\n--- Open Issues (includes PRs) ---")
    issues = get_issues()
    for issue in issues[:5]:  # limit to 5
        print(
            f"Issue #{issue['number']}: {issue['title']} ({'PR' if 'pull_request' in issue else 'Issue'})")

    if prs:
        pr_number = prs[0]["number"]
        print(f"\n--- Details of PR #{pr_number} ---")
        pr_details = get_pr_details(pr_number)
        print(f"Title: {pr_details['title']}")
        print(f"State: {pr_details['state']}")
        print(f"Mergeable: {pr_details.get('mergeable')}")
        print(f"Created at: {pr_details['created_at']}")
        print(f"Changed files: {pr_details['changed_files']}")
print("hello")
print("hello2")
print("hello3")