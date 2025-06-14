import json
import os
import sys
from flask import Flask, request, jsonify
from datetime import datetime

# OpenFaaS function handler
app = Flask(__name__)

# Import our main application logic
from app import PRReviewer, github_client

# Initialize PR reviewer
pr_reviewer = PRReviewer()

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def handle(path=''):
    """
    OpenFaaS function handler that routes all requests
    """
    
    # Health check
    if request.method == 'GET' and (path == '' or path == 'health'):
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'platform': 'openfaas',
            'function': 'pr-reviewer',
            'github_configured': bool(os.getenv('github_token')),  # OpenFaaS secret
            'openai_configured': bool(os.getenv('openai_api_key'))   # OpenFaaS secret
        })
    
    # Handle GitHub webhook
    if request.method == 'POST' and path in ['', 'webhook']:
        try:
            # Get the payload
            payload = request.get_json()
            if not payload:
                return jsonify({'error': 'No JSON payload'}), 400
            
            # Verify signature
            signature = request.headers.get('X-Hub-Signature-256', '')
            if not pr_reviewer.verify_signature(request.data, signature):
                return jsonify({'error': 'Invalid signature'}), 401
            
            # Process PR events
            if payload.get('action') in ['opened', 'synchronize', 'reopened']:
                pr_data = payload.get('pull_request', {})
                repo_name = payload.get('repository', {}).get('full_name', '')
                pr_number = pr_data.get('number')
                
                if repo_name and pr_number:
                    # Perform the review
                    result = pr_reviewer.review_pr(repo_name, pr_number, pr_data)
                    
                    return jsonify({
                        'message': 'PR review completed successfully',
                        'repository': repo_name,
                        'pr_number': pr_number,
                        'result': result,
                        'timestamp': datetime.now().isoformat()
                    })
                else:
                    return jsonify({'error': 'Missing repository or PR number'}), 400
            else:
                # Acknowledge other events
                return jsonify({
                    'message': f'Event {payload.get("action", "unknown")} acknowledged but not processed'
                })
                
        except Exception as e:
            return jsonify({
                'error': 'Internal server error',
                'details': str(e),
                'timestamp': datetime.now().isoformat()
            }), 500
    
    # Handle manual review requests
    if request.method == 'POST' and path == 'review':
        try:
            data = request.get_json()
            if not data or 'repo' not in data or 'pr_number' not in data:
                return jsonify({'error': 'Missing repo or pr_number'}), 400
            
            result = pr_reviewer.review_pr(
                data['repo'], 
                data['pr_number'], 
                data.get('pr_data', {})
            )
            
            return jsonify({
                'message': 'Manual review completed',
                'result': result,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            return jsonify({
                'error': 'Review failed',
                'details': str(e),
                'timestamp': datetime.now().isoformat()
            }), 500
    
    # Default response for unknown routes
    return jsonify({
        'error': 'Not found',
        'method': request.method,
        'path': path,
        'available_endpoints': [
            'GET / or /health - Health check',
            'POST / or /webhook - GitHub webhook',
            'POST /review - Manual review'
        ]
    }), 404

if __name__ == '__main__':
    # For OpenFaaS, we run on port 5000
    app.run(host='0.0.0.0', port=5000, debug=False) 