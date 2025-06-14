#!/usr/bin/env python3
"""
Test script to simulate GitHub webhook events for testing the PR reviewer application.
"""

import requests
import json
import hmac
import hashlib
import os
from datetime import datetime

# Configuration
WEBHOOK_URL = "http://localhost:8080/webhook"
WEBHOOK_SECRET = "your_test_webhook_secret"  # Should match your .env file

def create_signature(payload_body: str, secret: str) -> str:
    """Create GitHub webhook signature"""
    signature = hmac.new(
        secret.encode('utf-8'),
        payload_body.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return f"sha256={signature}"

def test_pr_opened_webhook():
    """Test PR opened webhook event"""
    
    # Sample PR opened payload
    payload = {
        "action": "opened",
        "number": 123,
        "pull_request": {
            "number": 123,
            "title": "Add new feature for user authentication",
            "body": "This PR adds JWT-based authentication to the user management system.",
            "state": "open",
            "user": {
                "login": "developer123"
            },
            "head": {
                "sha": "abc123def456"
            },
            "base": {
                "sha": "def456ghi789"
            },
            "diff_url": "https://api.github.com/repos/owner/repo/pulls/123.diff",
            "created_at": datetime.now().isoformat()
        },
        "repository": {
            "full_name": "owner/test-repo",
            "name": "test-repo",
            "owner": {
                "login": "owner"
            }
        },
        "sender": {
            "login": "developer123"
        }
    }
    
    payload_json = json.dumps(payload)
    signature = create_signature(payload_json, WEBHOOK_SECRET)
    
    headers = {
        "Content-Type": "application/json",
        "X-GitHub-Event": "pull_request",
        "X-Hub-Signature-256": signature,
        "User-Agent": "GitHub-Hookshot/test"
    }
    
    print("🧪 Testing PR opened webhook...")
    print(f"URL: {WEBHOOK_URL}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(WEBHOOK_URL, data=payload_json, headers=headers)
        
        print(f"\n📊 Response:")
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            print("✅ Webhook test successful!")
        else:
            print("❌ Webhook test failed!")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to webhook URL. Make sure the application is running.")
    except Exception as e:
        print(f"❌ Error testing webhook: {e}")

def test_manual_review():
    """Test manual review endpoint"""
    
    payload = {
        "repo": "owner/test-repo",
        "pr_number": 123,
        "pr_data": {
            "title": "Add new feature for user authentication",
            "body": "This PR adds JWT-based authentication to the user management system.",
            "user": {
                "login": "developer123"
            }
        }
    }
    
    print("\n🧪 Testing manual review endpoint...")
    print(f"URL: http://localhost:8080/review")
    
    try:
        response = requests.post(
            "http://localhost:8080/review",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"\n📊 Response:")
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            print("✅ Manual review test successful!")
        else:
            print("❌ Manual review test failed!")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to review URL. Make sure the application is running.")
    except Exception as e:
        print(f"❌ Error testing manual review: {e}")

def test_health_check():
    """Test health check endpoint"""
    
    print("\n🧪 Testing health check...")
    
    try:
        response = requests.get("http://localhost:8080/health")
        
        print(f"📊 Response:")
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            print("✅ Health check successful!")
        else:
            print("❌ Health check failed!")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to health endpoint. Make sure the application is running.")
    except Exception as e:
        print(f"❌ Error testing health check: {e}")

if __name__ == "__main__":
    print("🚀 Starting PR Reviewer Application Tests")
    print("=" * 50)
    
    # Test health check first
    test_health_check()
    
    # Test manual review
    test_manual_review()
    
    # Test webhook
    test_pr_opened_webhook()
    
    print("\n" + "=" * 50)
    print("🏁 Tests completed!")
    print("\nNote: These tests require the application to be running locally.")
    print("Start the app with: python app.py")
    print("Make sure to configure your .env file with proper tokens for full functionality.") 