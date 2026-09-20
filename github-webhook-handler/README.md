# GitHub Webhook Handler

Programmatic GitHub issue handling using the Devin API for the Apache Superset project.

## Features

- **GitHub Webhook Handling**: Receives GitHub issue events via webhooks
- **Signature Verification**: GitHub webhook signature validation for security
- **Devin API Integration**: Programmatic session creation and management
- **GitHub Comments**: Automatic commenting on issues with session information
- **Structured Output**: Consistent JSON responses from Devin sessions

## Setup Instructions

### 1. Install Dependencies

```bash
npm install
```

### 2. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# Devin API Configuration
DEVIN_API_KEY=your-devin-api-key
DEVIN_ORG_ID=your-org-id

# GitHub Configuration
GITHUB_WEBHOOK_SECRET=your-webhook-secret
GITHUB_TOKEN=ghp-your-github-token

# Server Configuration
PORT=3000
```

### 3. Get Credentials

**Devin API Key:**
1. Go to https://app.devin.ai
2. Navigate to Settings → Service Users
3. Create service user with `ManageOrgSessions` permission
4. Copy the API key and organization ID

**GitHub Personal Access Token:**
1. Go to https://github.com/settings/tokens
2. Click "Generate new token" → "Classic"
3. Name it "Devin Webhook Handler"
4. Select `repo` scope
5. Generate and copy the token

**GitHub Webhook Secret:**
```bash
openssl rand -hex 32
```

### 4. Start the Server

```bash
npm start
```

### 5. Configure GitHub Webhook

1. Go to your GitHub repository settings
2. Navigate to Webhooks → Add webhook
3. **Payload URL**: Your server URL + `/webhook/github`
4. **Content type**: `application/json`
5. **Secret**: Your `GITHUB_WEBHOOK_SECRET`
6. **Events**: "Issues" → "Issue created"
7. Click "Add webhook"

**Note:** For local development, use ngrok to expose localhost:3000 to the internet.

## Usage

### Automatic Issue Processing

When a new GitHub issue is created:

1. GitHub sends webhook to your server
2. Server verifies webhook signature
3. Server creates Devin session via API
4. Server posts comment on GitHub issue with session URL
5. Devin analyzes the issue automatically

### Manual Testing

```bash
# Test health check
curl http://localhost:3000/health

# Test webhook manually
curl -X POST http://localhost:3000/webhook/github \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: sha256=..." \
  -d '{"action":"opened","issue":{"title":"Test","body":"Test body","number":1},"repository":{"full_name":"owner/repo","owner":{"login":"owner"},"name":"repo"}}'
```

## Architecture

```
GitHub Issue → GitHub Webhook → Express Server → Devin API → Devin Session → GitHub Comment
```

## API Usage

This component demonstrates programmatic Devin API usage:

```javascript
// Create Devin session
POST /organizations/{org_id}/sessions
{
  "prompt": "Fix the GitHub issue: " + issueTitle,
  "session_links": [issueUrl],
  "structured_output_required": true,
  "structured_output_schema": {
    "type": "object",
    "properties": {
      "status": { "type": "string" },
      "summary": { type: "string" },
      "files_changed": { "type": "array", "items": { type: "string" } }
    }
  }
}

// Get session status
GET /organizations/{org_id}/sessions/{session_id}
```

## License

MIT
