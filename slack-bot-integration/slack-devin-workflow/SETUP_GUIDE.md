# Slack App Setup Guide

This guide walks you through creating and configuring the Slack app for the Devin automation workflow.

## Step 1: Create Slack App

1. Go to https://api.slack.com/apps
2. Click **"Create New App"**
3. Choose **"From scratch"**
4. **App Name**: Enter "Devin Bot" (or your preferred name)
5. **Pick a workspace**: Select your development workspace
6. Click **"Create App"**

## Step 2: Enable Socket Mode

1. In the left sidebar, click **"Socket Mode"**
2. Toggle **"Enable Socket Mode"** to ON
3. Click **"Generate Token and Scopes"**
4. Copy the **App-Level Token** (starts with `xapp-`)
5. Save this token as `SLACK_APP_TOKEN` in your `.env` file

## Step 3: Configure Bot Permissions

1. In the left sidebar, click **"OAuth & Permissions"**
2. Scroll to **"Scopes"** section
3. Under **"Bot Token Scopes"**, add the following scopes:
   - `chat:write` - Send messages to channels
   - `commands` - Use slash commands
   - `app_mentions:read` - Read bot mentions
4. Scroll to top and click **"Install to Workspace"**
5. Review permissions and click **"Allow"**
6. Copy the **Bot User OAuth Token** (starts with `xoxb-`)
7. Save this token as `SLACK_BOT_TOKEN` in your `.env` file

## Step 4: Create Slash Command

1. In the left sidebar, click **"Slash Commands"**
2. Click **"Create New Command"**
3. Fill in the form:
   - **Command**: `/devin`
   - **Request URL**: Leave empty (Socket Mode doesn't need this)
   - **Short Description**: "Trigger Devin automation"
   - **Long Description**: "Create Devin sessions to fix issues, implement features, or analyze code"
4. Click **"Save"**
5. Click **"Install to Workspace"** if prompted

## Step 5: Get App Credentials

1. In the left sidebar, click **"Basic Information"**
2. Scroll to **"App Credentials"** section
3. Copy the following values:
   - **App ID**: Save as `SLACK_APP_ID` in `.env`
   - **Signing Secret**: Save as `SLACK_SIGNING_SECRET` in `.env`
   - **Client ID**: (not needed for this demo)
   - **Client Secret**: (not needed for this demo)

## Step 6: Configure Environment Variables

Create your `.env` file:

```bash
cd slack-devin-workflow
cp .env.example .env
```

Edit `.env` with your actual credentials:

```env
# Slack Configuration
SLACK_BOT_TOKEN=xoxb-your-actual-bot-token
SLACK_SIGNING_SECRET=your-actual-signing-secret
SLACK_APP_TOKEN=xapp-your-actual-app-token
SLACK_APP_ID=your-actual-app-id

# Devin API Configuration
DEVIN_API_KEY=your-devin-api-key
DEVIN_ORG_ID=your-org-id

# Server Configuration
PORT=3000
```

## Step 7: Get Devin API Credentials

1. Go to https://app.devin.ai
2. Navigate to **Settings** → **Service Users**
3. Click **"Create Service User"**
4. Name it "Slack Bot Integration"
5. Assign permissions:
   - `ManageOrgSessions` - Create and manage sessions
   - `ImpersonateOrgSessions` - Create sessions on behalf of users (optional)
6. Click **"Create"**
7. Copy the **API Key** - save as `DEVIN_API_KEY` in `.env`
8. Copy your **Organization ID** from Settings page - save as `DEVIN_ORG_ID` in `.env`

## Step 8: Start the Bot

```bash
cd slack-devin-workflow
npm start
```

You should see:
```
⚡️ Slack bot is running!
```

## Step 9: Test the Bot

In your Slack workspace, try:

1. **Slash Command Test**:
   ```
   /devin fix issue #44433
   ```

2. **Message Trigger Test**:
   ```
   Can devin help fix the SQL injection?
   ```

Expected response:
```
🤖 Creating Devin session to: fix issue #44433

✅ Devin session created!

Task: fix issue #44433
Session URL: https://app.devin.ai/sessions/devin-abc123
Session ID: devin-abc123

[Open Session] [Check Status]
```

## Troubleshooting

### Bot not responding

**Check:**
- Bot is installed in the workspace
- Socket Mode is enabled
- Bot token is correct in `.env`
- App token is correct in `.env`
- Node.js app is running (`npm start`)

**Fix:**
- Restart the bot with `npm start`
- Check console for error messages
- Verify credentials in Slack app settings

### Slash command not found

**Check:**
- Slash command is configured in Slack app
- Bot has `commands` scope
- Command is installed to workspace

**Fix:**
- Reinstall the app to workspace
- Clear Slack cache
- Try refreshing Slack

### Devin API errors

**Check:**
- API key is valid
- Organization ID is correct
- Service user has correct permissions

**Fix:**
- Regenerate API key in Devin
- Verify service user permissions
- Check Devin organization settings

### Socket Mode connection issues

**Check:**
- App token is correct
- Socket Mode is enabled
- No firewall blocking WebSocket connections

**Fix:**
- Regenerate App-Level Token
- Check network connectivity
- Verify Slack service status

## Production Deployment

For production deployment, consider:

1. **Environment Variables**: Use proper secret management (AWS Secrets Manager, etc.)
2. **Error Handling**: Add comprehensive error handling and logging
3. **Rate Limiting**: Implement rate limiting for API calls
4. **Monitoring**: Add health checks and monitoring
5. **HTTPS**: Use HTTPS for HTTP endpoints (if not using Socket Mode)
6. **Database**: Add database to track session history
7. **Webhooks**: Implement webhooks for session completion notifications

## Security Best Practices

1. **Never commit `.env` file** to version control
2. **Use environment-specific credentials** (dev/staging/prod)
3. **Rotate API keys regularly**
4. **Implement proper authentication** for HTTP endpoints
5. **Log security events** for audit trails
6. **Use principle of least privilege** for service user permissions

## Next Steps

Once the basic Slack → Devin workflow is working:

1. **Add GitHub Integration**: Automatically create PRs from Devin sessions
2. **Add Session Monitoring**: Poll session status and update Slack
3. **Add Error Handling**: Graceful handling of API failures
4. **Add Multi-Channel Support**: Teams, Discord, etc.
5. **Add Analytics**: Track session success rates and patterns

## Support

- Slack API documentation: https://api.slack.com/
- Devin API documentation: https://docs.devin.ai/api-reference/overview
- Slack Bolt documentation: https://slack.dev/bolt-js/
