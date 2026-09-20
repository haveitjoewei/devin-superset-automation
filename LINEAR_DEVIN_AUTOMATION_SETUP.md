# Linear → Devin Native Automation Setup

This guide walks you through setting up a Linear → Devin automation using Devin's native integration capabilities.

## Overview

This automation will automatically create a Devin session whenever a Linear ticket is created or updated, allowing Devin to analyze and potentially work on the ticket.

## Prerequisites

- Linear workspace access
- Devin organization access with automation permissions
- Linear API key

## Step 1: Get Linear API Key

1. **Go to Linear Settings**
   - Navigate to https://linear.app
   - Go to your workspace settings
   - Find "API" section

2. **Create API Key**
   - Click "Create API key"
   - Name it "Devin Automation"
   - Select appropriate permissions:
     - `read` (to read ticket details)
     - `write` (to update ticket status/comments)
   - Generate and copy the key

## Step 2: Configure Linear Connection in Devin

1. **Go to Devin Dashboard**
   - Navigate to https://app.devin.ai
   - Go to your organization settings

2. **Add Linear Integration**
   - Find "Integrations" or "Connections" section
   - Click "Add Integration" → "Linear"
   - Enter your Linear API key
   - Select the workspace you want to automate

## Step 3: Create Linear → Devin Automation

1. **Navigate to Automations**
   - In Devin dashboard, go to "Automations" section
   - Click "Create New Automation"

2. **Configure Trigger**
   - **Trigger Type**: `linear:issue`
   - **Workspace**: Select your Linear workspace
   - **Event**: `issue.created` (new ticket created)
   - **Filters** (optional):
     - Only trigger for tickets with specific labels
     - Only trigger for tickets in specific teams
     - Only trigger for tickets with specific priorities

3. **Configure Action**
   - **Action Type**: `start_session`
   - **Prompt Template**:
     ```
     Analyze and help with this Linear ticket:

     Ticket Title: {{issue.title}}
     Ticket Description: {{issue.description}}
     Ticket ID: {{issue.identifier}}
     Team: {{team.name}}
     Priority: {{issue.priority}}
     Labels: {{issue.labels}}

     Context: This is for the Apache Superset project. Focus on the specific ticket and provide technical implementation if applicable.
     ```
   - **Session Links**: Include the Linear ticket URL
   - **Structured Output**: Enable for consistent responses

4. **Configure Output** (optional)
   - **Linear Integration**: Have Devin update ticket status
   - **Slack Notification**: Send session link to Slack channel
   - **GitHub Integration**: Create related GitHub issues

5. **Save and Enable**
   - Name the automation (e.g., "Linear Ticket Analysis")
   - Save the automation
   - Enable it to start listening for Linear events

## Step 4: Test the Automation

1. **Create a Test Ticket**
   - Go to your Linear workspace
   - Create a new ticket with a clear title and description
   - Example: "Test automation: Implement user authentication"

2. **Monitor Devin Dashboard**
   - Go to Devin automations dashboard
   - Check if the automation triggered
   - Look for the new Devin session
   - Monitor session progress

3. **Verify Session Creation**
   - Devin should create a session with the ticket context
   - Session should include the Linear ticket URL as context
   - Devin should analyze the ticket and provide suggestions

## Example Automation Configuration

```json
{
  "name": "Linear Ticket Analysis",
  "triggers": [
    {
      "event_type": "linear:issue",
      "workspace": "your-workspace",
      "filters": {
        "action": "create",
        "team": "Engineering"
      }
    }
  ],
  "actions": [
    {
      "type": "start_session",
      "prompt": "Analyze and implement: {{issue.title}}\n\n{{issue.description}}",
      "session_links": ["{{issue.url}}"],
      "structured_output_required": true,
      "structured_output_schema": {
        "type": "object",
        "properties": {
          "analysis": { "type": "string" },
          "implementation_plan": { "type": "string" },
          "estimated_time": { "type": "string" }
        }
      }
    }
  ]
}
```

## Advanced Configuration Options

### Filter by Team
Only trigger for specific teams:
```json
"filters": {
  "teams": ["Engineering", "Backend"]
}
```

### Filter by Priority
Only trigger for high-priority tickets:
```json
"filters": {
  "priorities": ["urgent", "high"]
}
```

### Filter by Labels
Only trigger for specific labels:
```json
"filters": {
  "labels": ["bug", "feature", "enhancement"]
}
```

### Multiple Actions
Configure different actions based on ticket type:
```json
"actions": [
  {
    "type": "start_session",
    "condition": "issue.labels.includes('bug')",
    "prompt": "Fix the bug: {{issue.title}}"
  },
  {
    "type": "start_session",
    "condition": "issue.labels.includes('feature')",
    "prompt": "Implement the feature: {{issue.title}}"
  }
]
```

## Troubleshooting

### Automation Not Triggering

**Check:**
- Linear integration is properly connected
- Workspace is selected in automation settings
- Automation is enabled
- Linear webhook is properly configured

**Fix:**
- Re-authorize Linear integration
- Check workspace permissions
- Verify webhook delivery in Linear settings

### Session Creation Fails

**Check:**
- Devin API credentials are valid
- Service user has proper permissions
- Prompt template syntax is correct
- Linear API key has correct permissions

**Fix:**
- Verify service user permissions in Devin
- Check prompt template for syntax errors
- Review automation logs in Devin dashboard
- Regenerate Linear API key if needed

### Linear API Rate Limits

**Check:**
- Linear API rate limits
- Automation frequency

**Fix:**
- Implement rate limiting in automation
- Use Linear authentication for higher limits
- Filter triggers to reduce frequency

## Monitoring and Logging

### View Automation Logs
- Go to Devin dashboard → Automations
- Click on your automation
- View execution history and logs
- Monitor success/failure rates

### Session Monitoring
- All created sessions appear in Devin sessions list
- Filter by automation to see automation-generated sessions
- Monitor session status and results

### Performance Metrics
- Track automation trigger frequency
- Monitor session success rates
- Measure average session duration

## Next Steps

Once Linear automation is working:

1. **Add More Linear Triggers**
   - `linear:issue.updated` - For ticket updates
   - `linear:issue.commented` - For comments on tickets
   - `linear:issue.status_changed` - For status changes

2. **Add Output Integrations**
   - Configure Slack notifications
   - Set up GitHub issue creation
   - Add Sentry integration

3. **Refine Prompt Templates**
   - Optimize prompts for better results
   - Add workspace-specific context
   - Include project-specific guidelines

## Security Considerations

- **Access Control**: Limit automation to specific workspaces
- **Permissions**: Use principle of least privilege for Linear API key
- **Secrets Management**: Never commit API keys to repository
- **Audit Logs**: Monitor automation execution for security events

## Scaling Considerations

- **Rate Limiting**: Configure appropriate trigger frequency
- **Cost Management**: Monitor Devin session usage and costs
- **Prioritization**: Implement priority queues for important tickets
- **Deduplication**: Prevent duplicate sessions for same ticket

## Presentation Demo

For your presentation, demonstrate:

1. **Automation Dashboard**: Show the configured Linear automation
2. **Real-time Trigger**: Create a Linear ticket live
3. **Session Creation**: Show Devin session being created
4. **Analysis Results**: Display Devin's analysis and implementation plan
5. **Multi-channel**: Mention this works alongside GitHub and Slack

This demonstrates Devin's native multi-channel capabilities for PM tools, not just developer tools.
