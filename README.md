# Automated PR Review Service

A serverless Python application that automatically reviews pull requests using AI/LLM integration and posts detailed feedback to GitHub.

## Features

- 🤖 **Automated PR Reviews**: Uses OpenAI's GPT models to analyze code changes
- 🔍 **Code Quality Checks**: Performs basic static analysis and best practice checks
- 📝 **Detailed Feedback**: Posts comprehensive review comments with suggestions
- 🚀 **Serverless Ready**: Designed for Knative/OpenFaaS deployment
- 🔒 **Secure**: Webhook signature verification and secret management
- 📊 **Health Monitoring**: Built-in health checks and logging

## Architecture

```
GitHub Repository → Webhook → Knative Service → OpenAI API → GitHub API
                                    ↓
                            PR Analysis & Review
```

## Quick Start

### 1. Clone and Setup

```bash
git clone <your-repo>
cd pr-reviewer
cp env.example .env
# Edit .env with your actual tokens and keys
```

### 2. Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
python app.py
```

### 3. Docker Development

```bash
# Build and run with Docker Compose
docker-compose up --build
```

### 4. Test the Application

```bash
# Health check
curl http://localhost:8080/health

# Manual review test (replace with actual repo/PR)
curl -X POST http://localhost:8080/review \
  -H "Content-Type: application/json" \
  -d '{"repo": "owner/repo", "pr_number": 123}'
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GITHUB_TOKEN` | GitHub Personal Access Token with repo permissions | Yes |
| `GITHUB_WEBHOOK_SECRET` | Secret for webhook signature verification | Yes |
| `OPENAI_API_KEY` | OpenAI API key for LLM analysis | Yes |
| `OPENAI_MODEL` | OpenAI model to use (default: gpt-3.5-turbo) | No |
| `PORT` | Application port (default: 8080) | No |

### GitHub Token Permissions

Your GitHub token needs these permissions:
- `repo` (Full control of private repositories)
- `write:discussion` (Write access to discussions)

### Setting up GitHub Webhook

1. Go to your repository settings
2. Navigate to Webhooks
3. Add webhook with:
   - **Payload URL**: `https://your-service-url/webhook`
   - **Content type**: `application/json`
   - **Secret**: Same as `GITHUB_WEBHOOK_SECRET`
   - **Events**: Select "Pull requests"

## Deployment

### Knative Deployment

1. **Install Knative Serving** (if not already installed):
```bash
kubectl apply -f serving.yaml
```

2. **Create Secrets**:
```bash
# Encode your secrets
echo -n "your_github_token" | base64
echo -n "your_webhook_secret" | base64
echo -n "your_openai_key" | base64

# Edit secrets.yaml with encoded values
kubectl apply -f secrets.yaml
```

3. **Build and Push Docker Image**:
```bash
# Build image
docker build -t your-registry/pr-reviewer:latest .

# Push to registry
docker push your-registry/pr-reviewer:latest

# Update knative-service.yaml with your image
```

4. **Deploy Service**:
```bash
kubectl apply -f knative-service.yaml
```

5. **Get Service URL**:
```bash
kubectl get ksvc pr-reviewer -o jsonpath='{.status.url}'
```

### OpenFaaS Deployment

1. **Install OpenFaaS**:
```bash
# Install OpenFaaS CLI
curl -sLS https://cli.openfaas.com | sudo sh

# Deploy OpenFaaS
kubectl apply -f https://raw.githubusercontent.com/openfaas/faas-netes/master/namespaces.yml

# Create credentials
kubectl -n openfaas create secret generic basic-auth \
  --from-literal=basic-auth-user=admin \
  --from-literal=basic-auth-password=$(head -c 12 /dev/urandom | shasum| cut -d' ' -f1)

# Deploy OpenFaaS
kubectl apply -f https://raw.githubusercontent.com/openfaas/faas-netes/master/yaml/
```

2. **Create Function**:
```bash
# Initialize function
faas-cli new pr-reviewer --lang python3-flask

# Copy app code to pr-reviewer/handler.py
# Update pr-reviewer.yml with secrets

# Build and deploy
faas-cli build -f pr-reviewer.yml
faas-cli deploy -f pr-reviewer.yml
```

## API Endpoints

### `POST /webhook`
GitHub webhook endpoint for PR events.

### `POST /review`
Manual review trigger for testing.

**Request Body:**
```json
{
  "repo": "owner/repository",
  "pr_number": 123,
  "pr_data": {}
}
```

### `GET /health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2023-12-01T12:00:00",
  "github_configured": true,
  "openai_configured": true
}
```

## PR Review Features

### Basic Checks
- Large changeset detection
- Missing test files warning
- Sensitive file detection
- Code pattern analysis

### AI-Powered Analysis
- Code quality assessment
- Bug detection
- Security vulnerability identification
- Performance implications
- Documentation suggestions
- Best practices recommendations

### Review Comment Format
```markdown
## 🤖 Automated PR Review

**Review completed at:** 2023-12-01 12:00:00 UTC

### 📊 Summary
- **Files analyzed:** 5
- **Basic checks:** ✅ Passed

### 🔍 Basic Checks
✅ All basic checks passed!

### 🧠 AI Code Analysis
[Detailed AI-generated feedback]

### 📝 Files Changed
- `src/main.py` (modified) - +25/-10
- `tests/test_main.py` (added) - +50/-0
```

## Monitoring and Debugging

### Logs
```bash
# Knative logs
kubectl logs -l serving.knative.dev/service=pr-reviewer -f

# Docker logs
docker-compose logs -f pr-reviewer
```

### Health Checks
```bash
# Local health check
curl http://localhost:8080/health

# Kubernetes health check
kubectl get pods -l serving.knative.dev/service=pr-reviewer
```

## Security Considerations

- ✅ Webhook signature verification
- ✅ Non-root container user
- ✅ Secret management via Kubernetes secrets
- ✅ Resource limits and quotas
- ✅ HTTPS enforcement for webhooks

## Troubleshooting

### Common Issues

1. **Webhook not triggered**
   - Check webhook URL and secret
   - Verify GitHub token permissions
   - Check application logs

2. **OpenAI API errors**
   - Verify API key validity
   - Check rate limits
   - Review model availability

3. **GitHub API errors**
   - Check token permissions
   - Verify repository access
   - Review API rate limits

### Debug Mode
Set `FLASK_ENV=development` for detailed error messages.

## Development

### Adding New Checks
Extend the `perform_basic_checks()` method in `PRReviewer` class.

### Customizing AI Prompts
Modify the prompt in `analyze_code_with_llm()` method.

### Adding New Endpoints
Add new routes in the Flask app.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
- Create an issue on GitHub
- Check the troubleshooting section
- Review the logs for error details 