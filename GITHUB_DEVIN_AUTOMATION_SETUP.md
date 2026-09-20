# GitHub → Devin Native Automation Setup

This guide walks you through setting up a GitHub → Devin automation using Devin's native integration capabilities.

## Overview

This automation will automatically create a Devin session whenever a new GitHub issue is created in your repository, allowing Devin to analyze and potentially fix the issue.

## Prerequisites

- GitHub repository access
- Devin organization access with automation permissions
- GitHub personal access token (for Devin to access your repo)

## Step 1: Configure GitHub Connection in Devin

1. **Go to Devin Dashboard**
   - Navigate to https://app.devin.ai
   - Go to your organization settings

2. **Add GitHub Integration**
   - Find "Integrations" or "Connections" section
   - Click "Add Integration" → "GitHub"
   - Authorize Devin to access your GitHub account
   - Select the repositories you want to automate

3. **Generate GitHub Personal Access Token** (if needed)
   - Go to https://github.com/settings/tokens
   - Click "Generate new token" → "Classic"
   - Name it "Devin Automation"
   - Select scopes:
     - `repo` (for full repository access)
     - `issues` (for issue access)
     - `pull_requests` (for PR creation)
   - Generate and copy the token
   - Add it to Devin's GitHub connection settings

## Step 2: Create GitHub → Devin Automation

1. **Navigate to Automations**
   - In Devin dashboard, go to "Automations" section
   - Click "Create New Automation"

2. **Configure Trigger**
   - **Trigger Type**: `github:issue`
   - **Repository**: Select your target repository (e.g., `apache/superset`)
   - **Event**: `issues.created` (new issue created)
   - **Filters** (optional):
     - Only trigger for issues with specific labels
     - Only trigger for issues with specific keywords in title

3. **Configure Action**
   - **Action Type**: `start_session`
   - **Prompt Template**:
     ```
     Analyze and help fix the GitHub issue described below.

     Issue Title: {{issue.title}}
     Issue Body: {{issue.body}}
     Issue Number: {{issue.number}}
     Repository: {{repository.full_name}}
     Author: {{issue.user.login}}

     Context: This is an Apache Superset repository. Focus on the specific issue mentioned and provide a technical solution with code changes if applicable.
     ```
   - **Session Links**: Include the GitHub issue URL
   - **Structured Output**: Enable for consistent responses

4. **Configure Output** (optional)
   - **GitHub Integration**: Have Devin create a PR for fixes
   - **Slack Notification**: Send session link to Slack channel
   - **Linear Integration**: Update related Linear tickets

5. **Save and Enable**
   - Name the automation (e.g., "GitHub Issue Analysis")
   - Save the automation
   - Enable it to start listening for GitHub events

## Step 3: Test the Automation

1. **Create a Test Issue**
   - Go to your GitHub repository
   - Create a new issue with a clear title and description
   - Example: "Test automation: Fix simple bug in documentation"

2. **Monitor Devin Dashboard**
   - Go to Devin automations dashboard
   - Check if the automation triggered
   - Look for the new Devin session
   - Monitor session progress

3. **Verify Session Creation**
   - Devin should create a session with the issue context
   - Session should include the GitHub issue URL as context
   - Devin should analyze the issue and provide suggestions

## Example Automation Configuration

```json
{
  "name": "GitHub Issue Analysis",
  "triggers": [
    {
      "event_type": "github:issue",
      "repository": "apache/superset",
      "filters": {
        "action": "opened",
        "label": "bug"
      }
    }
  ],
  "actions": [
    {
      "type": "start_session",
      "prompt": "Analyze and fix the GitHub issue: {{issue.title}}\n\n{{issue.body}}",
      "session_links": ["{{issue.html_url}}"],
      "structured_output_required": true,
      "structured_output_schema": {
        "type": "object",
        "properties": {
          "analysis": { "type": "string" },
          "proposed_fix": { "type": "string" },
          "files_to_change": { "type": "array", "items": { "type": "string" } }
        }
      }
    }
  ]
}
```

## Advanced Configuration Options

### Filter by Issue Labels
Only trigger for specific types of issues:
```json
"filters": {
  "labels": ["bug", "security", "high-priority"]
}
```

### Filter by Repository
Only trigger for specific repositories:
```json
"filters": {
  "repositories": ["apache/superset", "your-org/your-repo"]
}
```

### Multiple Actions
Configure multiple actions based on issue type:
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
- GitHub integration is properly connected
- Repository is selected in automation settings
- Automation is enabled
- GitHub webhook is properly configured

**Fix:**
- Re-authorize GitHub integration
- Check repository permissions
- Verify webhook delivery in GitHub repository settings

### Session Creation Fails

**Check:**
- Devin API credentials are valid
- Service user has proper permissions
- Prompt template syntax is correct

**Fix:**
- Verify service user permissions in Devin
- Check prompt template for syntax errors
- Review automation logs in Devin dashboard

### GitHub API Rate Limits

**Check:**
- GitHub API rate limits (5,000 requests/hour)
- Automation frequency

**Fix:**
- Implement rate limiting in automation
- Use GitHub authentication for higher limits
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

Once GitHub automation is working:

1. **Add More GitHub Triggers**
   - `github:pr` - For pull request events
   - `github:push` - For code push events
   - `github:dependabot` - For security alerts

2. **Add Output Integrations**
   - Configure Slack notifications
   - Set up Linear ticket updates
   - Add Sentry issue comments

3. **Refine Prompt Templates**
   - Optimize prompts for better results
   - Add repository-specific context
   - Include coding standards

## Security Considerations

- **Access Control**: Limit automation to specific repositories
- **Permissions**: Use principle of least privilege for GitHub token
- **Secrets Management**: Never commit tokens to repository
- **Audit Logs**: Monitor automation execution for security events

## Scaling Considerations

- **Rate Limiting**: Configure appropriate trigger frequency
- **Cost Management**: Monitor Devin session usage and costs
- **Prioritization**: Implement priority queues for important issues
- **Deduplication**: Prevent duplicate sessions for same issue

## Presentation Demo

For your presentation, demonstrate:

1. **Automation Dashboard**: Show the configured automation
2. **Real-time Trigger**: Create a GitHub issue live
3. **Session Creation**: Show Devin session being created
4. **Analysis Results**: Display Devin's analysis and proposed fix
5. **Multi-channel**: Mention this works alongside your Slack bot

This demonstrates Devin's native multi-channel capabilities without custom code.
