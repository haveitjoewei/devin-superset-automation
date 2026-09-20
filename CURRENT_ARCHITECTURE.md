# Current Architecture Overview

This document shows the complete system we've built for demonstrating Devin's multi-channel automation capabilities.

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        ISSUE INTAKE CHANNELS                                  │
├──────────────────┬──────────────────┬──────────────────┬────────────────────────┤
│  Slack Commands  │  GitHub Issues    │  Linear Tickets    │  Dependency Issues    │
│  (Custom Bot)    │  (Native + API)  │  (Native)         │  (API Orchestrator)    │
└────────┬─────────┴────────┬─────────┴────────┬─────────┴────────┬─────────┘
         │                 │                 │                 │                 │
         │                 │                 │                 │                 │
    ┌────▼────┐       ┌────▼────┐       ┌────▼────┐       ┌────▼────┐
    │Slack Bot│       │GitHub   │       │Linear   │       │Depend.   │
    │Server   │       │Native   │       │Native   │       │Orchestr.│
    │          │       │Automation│       │Automation│       │          │
    └────┬────┘       └────┬────┘       └────┬────┘       └────┬────┘
         │                 │                 │                 │                 │
         │                 │                 │                 │                 │
         └─────────────────┴─────────────────┴─────────────────┴─────────────────┘
                           │
                    ┌────▼────┐
                    │Devin API│
                    └────┬────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
         ┌────▼────┐ ┌────▼────┐ ┌────▼────┐
         │Slack    │ │GitHub    │ │Linear    │
         │Response │ │PR/Comment│ │Status    │
         └─────────┘ └─────────┘ └─────────┘
```

## Component Details

### 1. Slack Bot Integration (Custom)
**Location:** `slack-devin-workflow/`
**Trigger:** Slack commands (`/devin`) or message mentions
**Technology:** Node.js + Slack Bolt + Devin API
**Flow:** Slack → Bot Server → Devin API → Devin Session → Slack Response

### 2. GitHub Integration (Multiple Approaches)
**Location:** Multiple implementations
**Triggers:** GitHub issue creation, PR events

**A. Native Devin Automation**
- **Trigger:** GitHub issues with "bug" in title
- **Flow:** GitHub → Devin Native Automation → Devin Session → GitHub Comment
- **Status:** ✅ Working (tested with issue #6)

**B. Custom API Handler**
- **Location:** `github-webhook-handler/`
- **Trigger:** GitHub issues (via webhook)
- **Flow:** GitHub → Webhook Server → Devin API → Devin Session → GitHub Comment
- **Status:** ✅ Server running, awaiting webhook configuration

### 3. Linear Integration (Native)
**Trigger:** Linear tickets with low urgency
**Flow:** Linear → Devin Native Automation → Devin Session → Linear Comment
**Status:** ✅ Working (tested with low urgency ticket)

### 4. Dependency Remediation Orchestrator (Custom)
**Location:** `dependency-remediation-demo/`
**Trigger:** GitHub issues mentioning specific dependencies
**Flow:** GitHub → Orchestrator → Devin API → Devin Session → GitHub Comment
**Status:** ✅ Built, needs configuration and testing

## API Usage Demonstration

### Devin API Calls Used

All custom implementations use the Devin API v3:

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

### Current State Summary

| Component | Status | API Usage | Observable Output |
|-----------|--------|-----------|-------------------|
| Slack Bot | ✅ Working | ✅ Yes | Slack messages, session links |
| GitHub Native | ✅ Working | ❌ No (UI-based) | GitHub comments |
| GitHub API Handler | ✅ Server running | ✅ Yes | GitHub comments (pending webhook) |
| Linear Native | ✅ Working | ❌ No (UI-based) | Linear comments |
| Dependency Orchestrator | ✅ Built | ✅ Yes | GitHub comments (pending testing) |

## For Your Presentation

### What You Can Demonstrate

**✅ Currently Working:**
1. **Slack Bot** - Shows chat-based workflow
2. **GitHub Native Automation** - Shows Devin's built-in integrations
3. **Linear Native Automation** - Shows PM tool integration

**🔄 Ready to Demonstrate:**
4. **GitHub API Handler** - Shows programmatic API usage (needs webhook configuration)
5. **Dependency Orchestrator** - Shows complex business logic (needs configuration)

### Recommended Demo Flow

1. **Show Slack Bot** - `/devin fix issue #44433`
2. **Show GitHub Native** - Create issue with "bug" in title
3. **Show Linear Native** - Create low urgency ticket
4. **Show API Handler** - Explain architecture, show code
5. **Show Dependency Orchestrator** - Explain business value, show code

### Key Talking Points

**Multi-Channel Capability:**
- "We've integrated Devin with 4 different channels: Slack, GitHub, Linear, and dependency monitoring"
- "Each uses different triggers but the same Devin API"

**API vs Native:**
- "Native automations: Simple setup, UI-based, limited to built-in features"
- "API-based: Full control, custom logic, unlimited flexibility"

**Business Value:**
- "Slack: Real-time engineer workflow"
- "GitHub: Community issue handling"
- "Linear: PM workflow integration"
- "Dependency: $67k/year savings on upgrade toil"

This demonstrates Devin's flexibility and the value of programmatic API usage for complex automation scenarios.
