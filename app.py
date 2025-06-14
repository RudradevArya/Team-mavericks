import os
import json
import hashlib
import hmac
import requests
import logging
from flask import Flask, request, jsonify
from datetime import datetime
from typing import Dict, List, Optional
import openai
from github import Github
import difflib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_WEBHOOK_SECRET = os.getenv('GITHUB_WEBHOOK_SECRET')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')

# Initialize GitHub client
github_client = Github(GITHUB_TOKEN) if GITHUB_TOKEN else None

# Initialize OpenAI client
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY

class PRReviewer:
    def __init__(self):
        self.github = github_client
        self.model = OPENAI_MODEL

    def verify_signature(self, payload_body: bytes, signature_header: str) -> bool:
        """Verify GitHub webhook signature"""
        if not GITHUB_WEBHOOK_SECRET:
            logger.warning("GitHub webhook secret not configured")
            return True  # Skip verification in demo mode
        
        signature = hmac.new(
            GITHUB_WEBHOOK_SECRET.encode('utf-8'),
            payload_body,
            hashlib.sha256
        ).hexdigest()
        
        expected_signature = f"sha256={signature}"
        return hmac.compare_digest(expected_signature, signature_header)

    def get_pr_diff(self, repo_name: str, pr_number: int) -> str:
        """Get the diff for a pull request"""
        try:
            repo = self.github.get_repo(repo_name)
            pr = repo.get_pull(pr_number)
            
            # Get the diff
            diff_url = pr.diff_url
            headers = {'Authorization': f'token {GITHUB_TOKEN}'}
            response = requests.get(diff_url, headers=headers)
            
            return response.text if response.status_code == 200 else ""
        except Exception as e:
            logger.error(f"Error getting PR diff: {e}")
            return ""

    def get_pr_files(self, repo_name: str, pr_number: int) -> List[Dict]:
        """Get changed files in a pull request"""
        try:
            repo = self.github.get_repo(repo_name)
            pr = repo.get_pull(pr_number)
            
            files = []
            for file in pr.get_files():
                files.append({
                    'filename': file.filename,
                    'status': file.status,
                    'additions': file.additions,
                    'deletions': file.deletions,
                    'changes': file.changes,
                    'patch': file.patch if hasattr(file, 'patch') else None
                })
            
            return files
        except Exception as e:
            logger.error(f"Error getting PR files: {e}")
            return []

    def analyze_code_with_llm(self, diff: str, files: List[Dict], pr_info: Dict) -> str:
        """Analyze code changes using LLM"""
        if not OPENAI_API_KEY:
            return "⚠️ LLM analysis unavailable - OpenAI API key not configured"

        try:
            # Prepare context for LLM
            context = f"""
            Pull Request Analysis Request:
            
            PR Title: {pr_info.get('title', 'N/A')}
            PR Description: {pr_info.get('body', 'N/A')}
            
            Files Changed: {len(files)}
            {chr(10).join([f"- {f['filename']} ({f['status']})" for f in files[:10]])}
            
            Code Diff:
            {diff[:3000]}  # Limit diff size for API
            """

            prompt = f"""
            As an expert code reviewer, analyze this pull request and provide feedback on:
            
            1. Code Quality & Best Practices
            2. Potential Bugs or Issues
            3. Security Concerns
            4. Performance Implications
            5. Documentation & Comments
            6. Testing Coverage
            
            Please be constructive and specific in your feedback. If the code looks good, mention what's done well.
            
            {context}
            """

            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert code reviewer providing constructive feedback on pull requests."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.1
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Error analyzing code with LLM: {e}")
            return f"❌ Error during LLM analysis: {str(e)}"

    def perform_basic_checks(self, files: List[Dict]) -> List[str]:
        """Perform basic code quality checks"""
        issues = []
        
        # Check for large files
        for file in files:
            if file['changes'] > 500:
                issues.append(f"⚠️ Large changeset in {file['filename']} ({file['changes']} lines)")
        
        # Check for missing tests
        has_test_files = any('test' in f['filename'].lower() for f in files)
        has_code_files = any(f['filename'].endswith(('.py', '.js', '.ts', '.java', '.cpp')) for f in files)
        
        if has_code_files and not has_test_files:
            issues.append("⚠️ Code changes detected but no test files added/modified")
        
        # Check for potential sensitive files
        sensitive_patterns = ['.env', 'config', 'secret', 'key', 'password']
        for file in files:
            if any(pattern in file['filename'].lower() for pattern in sensitive_patterns):
                issues.append(f"🔒 Potentially sensitive file detected: {file['filename']}")
        
        return issues

    def post_review_comment(self, repo_name: str, pr_number: int, comment: str) -> bool:
        """Post review comment to GitHub PR"""
        try:
            repo = self.github.get_repo(repo_name)
            pr = repo.get_pull(pr_number)
            
            # Create review comment
            pr.create_issue_comment(comment)
            logger.info(f"Posted review comment to PR #{pr_number}")
            return True
            
        except Exception as e:
            logger.error(f"Error posting review comment: {e}")
            return False

    def review_pr(self, repo_name: str, pr_number: int, pr_data: Dict) -> Dict:
        """Main PR review function"""
        logger.info(f"Starting review for PR #{pr_number} in {repo_name}")
        
        # Get PR diff and files
        diff = self.get_pr_diff(repo_name, pr_number)
        files = self.get_pr_files(repo_name, pr_number)
        
        # Perform basic checks
        basic_issues = self.perform_basic_checks(files)
        
        # Analyze with LLM
        pr_info = {
            'title': pr_data.get('title', ''),
            'body': pr_data.get('body', ''),
            'author': pr_data.get('user', {}).get('login', ''),
        }
        
        llm_analysis = self.analyze_code_with_llm(diff, files, pr_info)
        
        # Compile review comment
        review_comment = self.compile_review_comment(basic_issues, llm_analysis, files)
        
        # Post comment
        success = self.post_review_comment(repo_name, pr_number, review_comment)
        
        return {
            'success': success,
            'files_analyzed': len(files),
            'basic_issues': len(basic_issues),
            'comment_posted': success
        }

    def compile_review_comment(self, basic_issues: List[str], llm_analysis: str, files: List[Dict]) -> str:
        """Compile the final review comment"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        
        comment = f"""
## 🤖 Automated PR Review

**Review completed at:** {timestamp}

### 📊 Summary
- **Files analyzed:** {len(files)}
- **Basic checks:** {'✅ Passed' if not basic_issues else f'⚠️ {len(basic_issues)} issues found'}

### 🔍 Basic Checks
"""
        
        if basic_issues:
            comment += "\n".join(f"- {issue}" for issue in basic_issues)
        else:
            comment += "✅ All basic checks passed!"
        
        comment += f"""

### 🧠 AI Code Analysis
{llm_analysis}

### 📝 Files Changed
"""
        
        for file in files[:10]:  # Limit to first 10 files
            comment += f"- `{file['filename']}` ({file['status']}) - +{file['additions']}/-{file['deletions']}\n"
        
        if len(files) > 10:
            comment += f"... and {len(files) - 10} more files\n"
        
        comment += """

---
*This review was generated automatically. Please use your best judgment and consider all feedback carefully.*
"""
        
        return comment


# Initialize PR reviewer
pr_reviewer = PRReviewer()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'github_configured': bool(GITHUB_TOKEN),
        'openai_configured': bool(OPENAI_API_KEY)
    })

@app.route('/webhook', methods=['POST'])
def github_webhook():
    """Handle GitHub webhook events"""
    
    # Verify signature
    signature = request.headers.get('X-Hub-Signature-256', '')
    if not pr_reviewer.verify_signature(request.data, signature):
        logger.warning("Invalid webhook signature")
        return jsonify({'error': 'Invalid signature'}), 401
    
    # Parse payload
    try:
        payload = request.get_json()
    except Exception as e:
        logger.error(f"Error parsing webhook payload: {e}")
        return jsonify({'error': 'Invalid JSON payload'}), 400
    
    # Handle pull request events
    if payload.get('action') in ['opened', 'synchronize']:
        pr_data = payload.get('pull_request', {})
        repo_name = payload.get('repository', {}).get('full_name', '')
        pr_number = pr_data.get('number')
        
        if repo_name and pr_number:
            logger.info(f"Processing PR #{pr_number} in {repo_name}")
            
            # Perform review
            try:
                result = pr_reviewer.review_pr(repo_name, pr_number, pr_data)
                return jsonify({
                    'message': 'PR review completed',
                    'result': result
                })
            except Exception as e:
                logger.error(f"Error reviewing PR: {e}")
                return jsonify({'error': 'Review failed'}), 500
        else:
            return jsonify({'error': 'Missing repository or PR number'}), 400
    
    # For other events, just acknowledge
    return jsonify({'message': 'Event received but not processed'})

@app.route('/review', methods=['POST'])
def manual_review():
    """Manual review endpoint for testing"""
    data = request.get_json()
    
    if not data or 'repo' not in data or 'pr_number' not in data:
        return jsonify({'error': 'Missing repo or pr_number'}), 400
    
    try:
        result = pr_reviewer.review_pr(
            data['repo'], 
            data['pr_number'], 
            data.get('pr_data', {})
        )
        return jsonify({
            'message': 'Manual review completed',
            'result': result
        })
    except Exception as e:
        logger.error(f"Error in manual review: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()  # Load environment variables from .env file
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False) 