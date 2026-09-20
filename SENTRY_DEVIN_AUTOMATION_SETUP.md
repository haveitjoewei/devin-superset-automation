# Sentry → Devin Webhook Automation Setup

This guide walks you through setting up a Sentry → Devin automation using Devin's native webhook capabilities.

## Overview

This automation will automatically create a Devin session when Sentry detects an error, allowing Devin to analyze and potentially fix the issue.

## Prerequisites

- Sentry account (free tier available)
- Devin organization access with automation permissions
- Devin webhook URL (provided by Devin)

## Step 1: Create Sentry Project

1. **Go to Sentry**
   - Navigate to https://sentry.io
   - Sign up or log in (free tier available: 5,000 events/month)

2. **Create New Project**
   - Click "Create Project"
   - Select platform (e.g., "Python", "Node.js", "React")
   - Name your project (e.g., "Devin Test Project")
   - Select your team (or create a new one)
   - Click "Create Project"

3. **Get DSN** (Data Source Name)
   - Sentry will provide a DSN for your project
   - Save this for potential future use (not needed for webhook)

## Step 2: Create Webhook Automation in Devin

1. **Go to Devin Dashboard**
   - Navigate to https://app.devin.ai
   - Go to **Automations** section
   - Click **"Create New Automation"**

2. **Configure Webhook Trigger**
   - **Trigger Type**: `webhook:incoming`
   - Devin will generate a unique webhook URL
   - Devin will generate a webhook secret for authentication

3. **Configure Action**
   - **Action Type**: `start_session`
   - **Prompt Template**:
     ```
     Analyze and help fix this Sentry error:
     
     Error Message: {{payload.message}}
     Error Level: {{payload.level}}
     Error Type: {{payload.exception.values[0].type}}
     Stack Trace: {{payload.exception.values[0].stacktrace}}
     
     Context: This is an error from the application. Analyze the error and provide a technical fix if applicable.
     ```
   - **Session Links**: Include the Sentry event URL if available
   - **Structured Output**: Enable for consistent responses

4. **Save and Enable**
   - Name the automation: "Sentry Error Analysis"
   - Save the automation
   - Enable it

5. **Copy Webhook Details**
   - Copy the webhook URL (starts with `https://...`)
   - Copy the webhook secret (for authentication)

## Step 3: Configure Sentry Webhook

1. **Go to Sentry Project Settings**
   - In Sentry, go to your project
   - Click **Settings** (gear icon)
   - Navigate to **Webhooks** or **Integrations**

2. **Add Webhook**
   - Click **"Add Webhook"** or **"Create Integration"**
   - **Webhook URL**: Paste the Devin webhook URL
   - **Secret**: Paste the Devin webhook secret
   - **Events to Trigger**: Select which events should trigger the webhook:
     - `issue.created` (new issues)
     - `issue.occurred` (error occurred)
     - `issue.resolved` (issue resolved)
   - Click **Save**

3. **Test Webhook**
   - Sentry should provide a test button
   - Click **"Test Webhook"** to verify connectivity
   - Check Devin dashboard for the test event

## Step 4: Test the Automation

### Option 1: Trigger Real Error (If You Have an App)

1. **Add Sentry to Your Application**
   - Install Sentry SDK in your application
   - Configure with your project DSN
   - Deploy or run your application

2. **Trigger an Error**
   - Create an error condition in your app
   - Sentry will capture the error
   - Webhook should trigger Devin automation

### Option 2: Manual Test (Simulated)

1. **Send Test Webhook**
   ```bash
   curl -X POST YOUR_DEVIN_WEBHOOK_URL \
     -H "X-Webhook-Secret: YOUR_WEBHOOK_SECRET" \
     -H "Content-Type: application/json" \
     -d '{
       "message": "Test error from webhook",
       "level": "error",
       "exception": {
         "values": [{
           "type": "TestError",
           "stacktrace": "Simulated stack trace for testing"
         }]
       }
     }'
   ```

2. **Monitor Devin Dashboard**
   - Check if the automation triggered
   - Look for the new Devin session
   - Monitor session progress

## Example Automation Configuration

```json
{
  "name": "Sentry Error Analysis",
  "triggers": [
    {
      "event_type": "webhook:incoming",
      "filters": {
        "regex": "level.*error"
      }
    }
  ],
  "actions": [
    {
      "type": "start_session",
      "prompt": "Analyze and fix this Sentry error: {{payload.message}}\n\nStack trace: {{payload.exception.values[0].stacktrace}}",
      "structured_output_required": true,
      "structured_output_schema": {
        "type": "object",
        "properties": {
          "error_analysis": { "type": "string" },
          "proposed_fix": { "type": "string" },
          "files_to_change": { "type": "array", "items": { "type": "string" } }
        }
      }
    }
  ]
}
```

## Advanced Configuration Options

### Filter by Error Level
Only trigger for high-severity errors:
```json
"filters": {
  "regex": "level.*(fatal|critical)"
}
```

### Filter by Error Type
Only trigger for specific error types:
```json
"filters": {
  "regex": "exception.values[0].type.*(SQLInjection|XSS)"
}
```

### Multiple Actions
Configure different actions based on error severity:
```json
"actions": [
  {
    "type": "start_session",
    "condition": "payload.level === 'fatal'",
    "prompt": "Critical error: {{payload.message}}"
  },
  {
    "type": "start_session",
    "condition": "payload.level === 'warning'",
    "prompt": "Warning: {{payload.message}}"
  }
]
```

## Troubleshooting

### Webhook Not Triggering

**Check:**
- Webhook URL is correct in Sentry
- Webhook secret matches between Sentry and Devin
- Automation is enabled in Devin
- Sentry events match trigger conditions

**Fix:**
- Verify webhook URL is accessible
- Check webhook secret is correct
- Test webhook from Sentry dashboard
- Review automation logs in Devin

### Session Creation Fails

**Check:**
- Devin API credentials are valid
- Service user has proper permissions
- Prompt template handles webhook payload correctly
- Webhook payload format matches expectations

**Fix:**
- Verify service user permissions in Devin
- Check prompt template for syntax errors
- Review webhook payload structure
- Add error handling in prompt template

### Webhook Authentication Issues

**Check:**
- Webhook secret is configured correctly
- Secret is passed in correct header format
- No proxy/firewall issues blocking webhooks

**Fix:**
- Regenerate webhook secret in Devin
- Update Sentry webhook configuration
- Check network connectivity
- Use header-based authentication instead of query params

## Monitoring and Logging

### View Automation Logs
- Go to Devin dashboard → Automations
- Click on your automation
- View execution history and logs
- Monitor success/failure rates

### Session Monitoring
- All created sessions appear in Devin sessions list
- Filter by automation to see webhook-triggered sessions
- Monitor session status and results

### Performance Metrics
- Track webhook trigger frequency
- Monitor session success rates
- Measure average session duration
- Analyze error patterns

## Security Considerations

- **Webhook Security**: Always use webhook secrets for authentication
- **Payload Filtering**: Filter sensitive data from webhook payloads
- **Access Control**: Limit webhook triggers to specific error types
- **Secrets Management**: Never commit webhook secrets to repository
- **Audit Logs**: Monitor webhook deliveries for security events

## Scaling Considerations

- **Rate Limiting**: Configure appropriate webhook rate limits
- **Priority Queues**: Prioritize critical errors over warnings
- **Deduplication**: Prevent duplicate sessions for same error
- **Cost Management**: Monitor Devin session usage for high-volume errors

## Presentation Demo

For your presentation, demonstrate:

1. **Webhook Configuration**: Show the webhook URL and secret
2. **Manual Test**: Send a test webhook payload
3. **Session Creation**: Show Devin session being created
4. **Error Analysis**: Display Devin's analysis of the error
5. **Universal Integration**: Emphasize this works with ANY webhook-based system

This demonstrates Devin's flexibility to integrate with any system that supports webhooks, not just native integrations.

## Alternative: No Sentry Account

If you don't want to set up Sentry, you can:

1. **Use Postman/curl** to test webhooks directly
2. **Create a simple HTTP server** to send test webhooks
3. **Use other error monitoring tools** (DataDog, Rollbar, etc.)
4. **Skip this integration** and move to scheduled automation

The key demonstration is webhook integration, not specifically Sentry.
