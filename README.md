# Devin Superset Automation

A comprehensive demonstration of Devin's multi-channel automation capabilities for the Apache Superset project, showcasing event-driven workflows using the Devin API.

## Overview

This repository contains multiple automation implementations that demonstrate how Devin can be integrated into different enterprise issue intake channels:

- **Slack Bot Integration** - Chat-based workflow for real-time issue reporting
- **GitHub Webhook Handler** - Programmatic GitHub issue handling via Devin API
- **Dependency Remediation Orchestrator** - Automated dependency upgrade remediation for security updates

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Issue Intake Channels                         │
├──────────────┬──────────────┬──────────────┬────────────────┤
│  Slack       │  GitHub      │  Linear      │  Dependency   │
│  Integration │  Integration │  Integration │  Remediation   │
└──────┬───────┴──────┬───────┴──────┬───────┴────────┴──────────┘
      │              │              │              │
      │              │              │              │
      └──────────────┴──────────────┴──────────────┘
                           │
                    ┌──────▼──────┐
                    │  Devin API  │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
         ┌────▼────┐ ┌────▼────┐ ┌────▼────┐
         │  Slack   │ │  GitHub  │ │ Linear   │
         │  Reply  │ │  PR/Comment│ │  Status  │
         └─────────┘ └─────────┘ └─────────┘
```

## Components

### 1. Slack Bot Integration

**Location:** `slack-bot-integration/`

**Purpose:** Real-time engineer workflow automation via Slack commands and message triggers.

**Features:**
- Slash commands (`/devin fix`, `/devin implement`, `/devin analyze`, `/devin test`)
- Message triggers (mentions of "devin")
- Session management via Devin API
- Interactive buttons (Open Session, Check Status)
- Structured output for consistent responses

**Setup:** See `slack-bot-integration/SETUP_GUIDE.md`

### 2. GitHub Webhook Handler

**Location:** `github-webhook-handler/`

**Purpose:** Programmatic GitHub issue handling using the Devin API.

**Features:**
- GitHub webhook signature verification
- Automatic Devin session creation for new issues
- GitHub issue comments with session links
- Structured output for analysis results
- Customizable prompt templates

**Setup:** See `github-webhook-handler/README.md`

### 3. Dependency Remediation Orchestrator

**Location:** `dependency-remediation-orchestrator/`

**Purpose:** Automated dependency upgrade remediation for security and version compatibility.

**Features:**
- Pattern detection for dependency issues (apispec, marshmallow-sqlalchemy, google-auth)
- Custom Devin prompts for specific dependency problems
- Business logic for different remediation strategies
- Integration with Superset's documented dependency blockers

**Setup:** See `dependency-remediation-orchestrator/README.md`

## Quick Start

### Prerequisites

- Node.js 18+
- Devin API key and organization ID
- GitHub personal access token
- Slack app (for Slack integration only)

### Installation

Each component has its own `package.json` and dependencies:

```bash
# Slack Bot
cd slack-bot-integration
npm install
npm start

# GitHub Webhook Handler
cd github-webhook-handler
npm install
npm start

# Dependency Orchestrator
cd dependency-remediation-orchestrator
npm install
npm start
```

### Configuration

Each component requires a `.env` file with the appropriate credentials:

```env
# Devin API Configuration
DEVIN_API_KEY=your-devin-api-key
DEVIN_ORG_ID=your-org-id

# GitHub Configuration
GITHUB_WEBHOOK_SECRET=your-webhook-secret
GITHUB_TOKEN=ghp-your-github-token

# Slack Configuration (Slack Bot only)
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_SIGNING_SECRET=your-signing-secret
SLACK_APP_TOKEN=xapp-your-app-token
SLACK_APP_ID=your-app-id

# Server Configuration
PORT=3000
```

## Usage Examples

### Slack Bot

```bash
cd slack-bot-integration
npm start

# In Slack:
/devin fix issue #44433
```

### GitHub Webhook Handler

```bash
cd github-webhook-handler
npm start

# Configure GitHub webhook to:
# http://your-server:3000/webhook/github
```

### Dependency Orchestrator

```bash
cd dependency-remediation-orchestrator
npm start

# Create GitHub issue mentioning "apispec" to trigger
```

## API Usage

All components use the Devin API v3 for programmatic session management:

```javascript
// Create session
POST /organizations/{org_id}/sessions
{
  "prompt": "...",
  "session_links": ["..."],
  "structured_output_required": true,
  "structured_output_schema": {...}
}

// Get session status
GET /organizations/{org_id}/sessions/{session_id}
```

## Business Value

### Why This Matters

Superset faces real-world upgrade blockers documented in `requirements/base.in`:

- **apispec** - Pinned to `<6.0.0,<6.7.0` due to breaking unit test
- **marshmallow-sqlalchemy** - Pinned due to memory regression
- **google-auth** - Pinned due to install-path consistency

These blockers prevent security updates and feature improvements, costing engineering time and technical debt.

### Impact Model

Based on the codebase analysis:
- **2,059** dependency-bump PRs merged (last 12 months)
- **128** security-labeled PRs/commits
- **343** direct dependencies
- **6** upgrades explicitly deferred as "needs eng attention"

**Estimated annual cost:** $67k for engineering time spent on dependency upgrade toil

### Devin Advantage

- **Scanners find, bots bump — neither fixes.** Devin edits code, runs tests, iterates until green
- **Throughput scales with sessions, not headcount.**
- **Async + unattended.** Event fires, PR waiting at standup.
- **One workflow, many problems.** Different upgrade problems delegated to autonomous agent.

## For Presentations

### Demonstration Flow

1. **Slack Integration** - Show chat-based workflow
2. **GitHub Integration** - Show repo-based workflow  
3. **Dependency Remediation** - Show security workflow with business impact

### Key Talking Points

- **Multi-channel capability**: Devin integrates with Slack, GitHub, Linear, and monitoring systems
- **API flexibility**: Programmatic control vs. native automations
- **Real-world impact**: Addresses actual Superset dependency blockers
- **Scalability**: Event-driven architecture handles high-volume automation
- **Business value**: $67k/year savings on upgrade toil

## Requirements

- **Devin API key** with `ManageOrgSessions` permission
- **GitHub personal access token** with `repo` scope
- **Slack app** (for Slack integration only)
- **Node.js 18+** for running servers
- **ngrok** (optional, for exposing localhost to internet)

## Security Considerations

- **Webhook Secrets**: Always use webhook signature verification
- **API Key Management**: Never commit keys to repository
- **Environment Variables**: Use `.env` files (gitignored)
- **RBAC**: Use principle of least privilege for service users
- **Audit Logging**: Monitor automation execution for security events

## License

MIT

## Related Repositories

- **Apache Superset**: https://github.com/apache/superset
- **Superset Fork**: https://github.com/haveitjoewei/superset

## Contact

For questions about this automation demonstration, please refer to the individual component README files.
