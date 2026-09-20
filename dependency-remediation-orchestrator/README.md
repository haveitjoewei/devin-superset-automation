# Dependency Remediation Orchestrator

Automated dependency upgrade remediation using Devin API for the Apache Superset project.

## Features

- **Pattern Detection**: Automatically detects dependency issues from GitHub issues
- **Business Logic**: Custom handling for specific Superset dependency blockers
- **Devin API Integration**: Programmatic session creation for dependency analysis
- **Multi-Dependency Support**: Handles apispec, marshmallow-sqlalchemy, and google-auth
- **Structured Output**: Consistent JSON responses from Devin sessions

## Real-World Issues

This orchestrator addresses documented Superset dependency blockers in `requirements/base.in`:

1. **apispec** - Pinned to `<6.7.0` due to breaking unit test
2. **marshmallow-sqlalchemy** - Pinned due to memory regression in test suite
3. **google-auth** - Pinned due to install-path consistency issue

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

### 3. Start the Orchestrator

```bash
npm start
```

### 4. Configure GitHub Webhook

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

When a GitHub issue mentions one of the monitored dependencies:

1. Orchestrator receives webhook
2. Validates it's a dependency issue
3. Creates Devin session via API
4. Devin investigates the dependency
5. Devin proposes and implements fixes
6. Orchestrator posts results to GitHub

### Triggering the Orchestrator

Create a GitHub issue mentioning one of the dependencies:

**Title:** "Fix apispec upgrade blocker"
**Body:** "The apispec dependency is pinned to <6.7.0 due to a breaking unit test. We need to investigate and fix this to allow the upgrade."

The orchestrator will detect "apispec" and trigger a focused Devin session.

## Architecture

```
GitHub Issue (Dependency) → Orchestrator → Devin API → Devin Session → GitHub Comment
```

## Business Value

### Why This Matters

Superset faces real-world upgrade blockers that prevent security updates:

- **2,059** dependency-bump PRs merged (last 12 months)
- **128** security-labeled PRs/commits
- **6** upgrades explicitly deferred as "needs eng attention"

**Estimated annual cost:** $67k for engineering time spent on dependency upgrade toil

### Devin Advantage

- **Scanners find, bots bump — neither fixes.** Devin edits code, runs tests, iterates until green
- **Throughput scales with sessions, not headcount.**
- **Async + unattended.** Event fires, PR waiting at standup.
- **One workflow, many problems.** Different upgrade problems delegated to autonomous agent.

## API Usage

This component demonstrates programmatic Devin API usage:

```javascript
// Create Devin session
POST /organizations/{org_id}/sessions
{
  "prompt": "Analyze and fix dependency upgrade: " + dependencyName,
  "session_links": [issueUrl],
  "structured_output_required": true,
  "structured_output_schema": {
    "type": "object",
    "properties": {
      "status": { "type": "string" },
      "dependency_name": { "type": "string" },
      "current_version": { "type": "string" },
      "target_version": { "type": "string" },
      "fix_summary": { "type": "string" }
    }
  }
}
```

## License

MIT
