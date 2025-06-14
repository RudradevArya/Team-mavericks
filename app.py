import os
import json
import hashlib
import hmac
import requests
import logging
from flask import Flask, request, jsonify
from datetime import datetime
from typing import Dict, List
import openai
from github import Github

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Load configuration
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_WEBHOOK_SECRET = os.getenv('GITHUB_WEBHOOK_SECRET')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')

# Initialize GitHub and OpenAI clients
github_client = Github(GITHUB_TOKEN) if GITHUB_TOKEN else None
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY

class PRReviewer:
    def __init__(self):
        self.github = github_client
        self.model = OPENAI_MODEL

    def verify_signature(self, payload: bytes, signature: str) -> bool:
        if not GITHUB_WEBHOOK_SECRET:
            return True
        expected = 'sha256=' + hmac.new(
            GITHUB_WEBHOOK_SECRET.encode(), payload, hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature)

    def get_pull_request(self, repo_name: str, pr_number: int):
        try:
            repo = self.github.get_repo(repo_name)
            return repo.get_pull(pr_number)
        except Exception as e:
            logger.error(f"Error fetching PR: {e}")
            return None

    def get_pr_diff(self, pr) -> str:
        try:
            response = requests.get(
                pr.diff_url,
                headers={'Authorization': f'token {GITHUB_TOKEN}'}
            )
            return response.text if response.status_code == 200 else ""
        except Exception as e:
            logger.error(f"Error fetching PR diff: {e}")
            return ""

    def get_pr_files(self, pr) -> List[Dict]:
        files = []
        try:
            for file in pr.get_files():
                files.append({
                    'filename': file.filename,
                    'status': file.status,
                    'additions': file.additions,
                    'deletions': file.deletions,
                    'changes': file.changes,
                    'patch': getattr(file, 'patch', None)
                })
        except Exception as e:
            logger.error(f"Error getting PR files: {e}")
        return files

    def analyze_code(self, diff: str, files: List[Dict], pr_info: Dict) -> str:
        if not OPENAI_API_KEY:
            return "⚠️ LLM analysis unavailable - API key missing"

        try:
            context = f"""
            Pull Request Title: {pr_info.get('title', '')}
            Description: {pr_info.get('body', '')}
            Files Changed: {len(files)}
            {'\n'.join(f"- {f['filename']} ({f['status']})" for f in files[:10])}
            Code Diff:
            {diff[:3000]}
            """
            prompt = f"""
            Act as an expert code reviewer.
            Review for: Code Quality, Bugs, Security, Performance, Documentation, Tests.
            Provide clear, constructive feedback.
            {context}
            """

            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a code review assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.1
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI error: {e}")
            return f"❌ LLM analysis failed: {e}"

    def perform_checks(self, files: List[Dict]) -> List[str]:
        issues = []
        if any(f['changes'] > 500 for f in files):
            issues.append("⚠️ Large changeset detected.")
        if any(f['filename'].endswith(('.py', '.js', '.ts', '.java', '.cpp')) for f in files) and not any('test' in f['filename'].lower() for f in files):
            issues.append("⚠️ Code changes with no test files.")
        if any(s in f['filename'].lower() for f in files for s in ['.env', 'config', 'secret', 'key', 'password']):
            issues.append("🔒 Sensitive file pattern detected.")
        return issues

    def post_comment(self, pr, comment: str) -> bool:
        try:
            pr.create_issue_comment(comment)
            return True
        except Exception as e:
            logger.error(f"Error posting comment: {e}")
            return False

    def review_pr(self, repo_name: str, pr_number: int, pr_data: Dict) -> Dict:
        pr = self.get_pull_request(repo_name, pr_number)
        if not pr:
            return {'success': False, 'error': 'Failed to retrieve PR'}

        diff = self.get_pr_diff(pr)
        files = self.get_pr_files(pr)
        basic_issues = self.perform_checks(files)

        pr_info = {
            'title': pr_data.get('title', ''),
            'body': pr_data.get('body', ''),
            'author': pr_data.get('user', {}).get('login', '')
        }

        llm_output = self.analyze_code(diff, files, pr_info)
        comment = self.build_comment(files, basic_issues, llm_output)
        success = self.post_comment(pr, comment)

        return {'success': success, 'issues_found': len(basic_issues), 'files_checked': len(files)}

    def build_comment(self, files: List[Dict], issues: List[str], analysis: str) -> str:
        time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        summary = f"""
## 🤖 Automated Review Summary
**Time:** {time}

### 🔍 Basic Checks
{chr(10).join(f"- {i}" for i in issues) if issues else '✅ All checks passed!'}

### 🧠 LLM Feedback
{analysis}

### 📁 Files
{chr(10).join(f"- `{f['filename']}` ({f['status']})" for f in files[:10])}
{'...and more' if len(files) > 10 else ''}

---
*Automated review powered by AI.*
"""
        return summary

reviewer = PRReviewer()

@app.route('/health')
def health():
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.utcnow().isoformat(),
        'github': bool(GITHUB_TOKEN),
        'openai': bool(OPENAI_API_KEY)
    })

@app.route('/webhook', methods=['POST'])
def webhook():
    sig = request.headers.get('X-Hub-Signature-256', '')
    if not reviewer.verify_signature(request.data, sig):
        return jsonify({'error': 'Invalid signature'}), 401

    event = request.get_json()
    if event.get('action') not in ['opened', 'synchronize']:
        return jsonify({'message': 'Ignored event'})

    repo = event.get('repository', {}).get('full_name', '')
    pr_num = event.get('pull_request', {}).get('number')
    if not (repo and pr_num):
        return jsonify({'error': 'Missing PR info'}), 400

    result = reviewer.review_pr(repo, pr_num, event.get('pull_request', {}))
    return jsonify({'message': 'Review complete', 'result': result})

@app.route('/review', methods=['POST'])
def manual():
    data = request.get_json()
    if 'repo' not in data or 'pr_number' not in data:
        return jsonify({'error': 'Missing parameters'}), 400

    result = reviewer.review_pr(data['repo'], data['pr_number'], data.get('pr_data', {}))
    return jsonify({'message': 'Manual review complete', 'result': result})

if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)), debug=False)