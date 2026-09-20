# Slack → Devin Automation Workflow

This project demonstrates a real-world automation workflow where issues reported in Slack are automatically sent to Devin for analysis and resolution.

## Architecture

```
Slack Message → Slack Bot → Node.js App → Devin API → Devin Session → Result → Slack Reply
```

## Features

- **Slash Command**: `/devin fix issue #44433` - Creates Devin session to fix specific issues
- **Message Trigger**: Mention "devin" in any message to trigger automation
- **Action Buttons**: Open session URL or check session status
- **Multiple Actions**: Support for fix, implement, analyze, and test commands
- **Session Management**: Create and monitor Devin sessions programmatically

## Setup Instructions

### 1. Create Slack App

1. Go to https://api.slack.com/apps
2. Click "Create New App"
3. Choose "From scratch"
4. Name your app (e.g., "Devin Bot")
5. Select your workspace

### 2. Configure Slack App Permissions

**OAuth & Permissions:**
- Add Bot Token Scopes:
  - `chat:write` - Send messages
  - `commands` - Use slash commands
  - `app_mentions:read` - Read bot mentions

**Socket Mode:**
- Enable Socket Mode (simpler than setting up HTTP endpoints)
- Copy the App-Level Token

**Slash Commands:**
- Create a new slash command: `/devin`
- Request URL: Not needed with Socket Mode
- Short description: "Trigger Devin automation"

### 3. Install App to Workspace

1. Go to "Install to Workspace"
2. Install the app
3. Copy the Bot User OAuth Token (starts with `xoxb-`)

### 4. Get Devin API Credentials

1. Go to https://app.devin.ai
2. Navigate to Settings → Service Users
3. Create a new service user with required permissions
4. Copy the API key
5. Copy your organization ID from Settings

### 5. Configure Environment Variables

```bash
cd slack-devin-workflow
cp .env.example .env
```

Edit `.env` with your credentials:

```env
SLACK_BOT_TOKEN=xoxb-your-actual-bot-token
SLACK_SIGNING_SECRET=your-actual-signing-secret
SLACK_APP_TOKEN=xapp-your-actual-app-token
SLACK_APP_ID=your-actual-app-id

DEVIN_API_KEY=your-actual-devin-api-key
DEVIN_ORG_ID=your-actual-org-id

PORT=3000
```

### 6. Install Dependencies

```bash
npm install
```

### 7. Start the Bot

```bash
npm start
```

## Usage

### Slash Command

In any Slack channel where the bot is installed:

```
/devin fix issue #44433
/devin implement OAuth2 support
/devin analyze security vulnerability
/devin test user authentication
```

### Message Trigger

Simply mention "devin" in any message:

```
Can devin help fix the SQL injection in presto.py?
```

### Example Response

The bot will respond with:

```
🤖 Creating Devin session to: fix issue #44433

✅ Devin session created!

Task: fix issue #44433
Session URL: https://app.devin.ai/sessions/devin-abc123
Session ID: devin-abc123

[Open Session] [Check Status]
```

## Workflow Examples

### 1. Bug Fix Workflow

**Slack Command:**
```
/devin fix issue #44433
```

**Devin Session:**
- Analyzes the issue
- Identifies the problem
- Creates a fix
- Opens a PR

**Slack Response:**
- Session link for monitoring
- PR link when complete

### 2. Feature Implementation

**Slack Command:**
```
/devin implement OAuth2 support for database connections
```

**Devin Session:**
- Designs the implementation
- Writes the code
- Creates tests
- Opens PR

### 3. Security Analysis

**Slack Command:**
```
/devin analyze SQL injection vulnerability in presto.py
```

**Devin Session:**
- Analyzes the vulnerability
- Proposes security fix
- Creates security advisory

## Demo Scenarios

### Scenario 1: Quick Bug Fix

1. Engineer posts in `#engineering`: `/devin fix SQL injection in presto.py`
2. Bot creates Devin session
3. Devin analyzes and fixes the issue
4. Bot responds with session link and PR

### Scenario 2: Feature Request

1. PM posts in `#product-dev`: `/devin implement user role management`
2. Bot creates Devin session for implementation
3. Devin designs and implements the feature
4. Bot provides progress updates

### Scenario 3: Security Incident

1. Security engineer posts: `/devin analyze vulnerability in auth system`
2. Bot creates high-priority Devin session
3. Devin performs security analysis
4. Bot provides security assessment

## Troubleshooting

### Bot not responding
- Check that the bot is installed in the workspace
- Verify Socket Mode is enabled
- Check the bot token is correct

### Devin API errors
- Verify API key is valid
- Check organization ID matches
- Ensure service user has correct permissions

### Command not recognized
- Verify slash command is configured in Slack app
- Check bot has `commands` scope
- Try refreshing Slack

## Development

### Project Structure

```
slack-devin-workflow/
├── index.js          # Main application logic
├── package.json      # Dependencies
├── .env.example      # Environment variables template
├── .env              # Your actual credentials (gitignored)
└── README.md         # This file
```

### Adding New Commands

Edit `index.js` to add new actions:

```javascript
case 'security':
  prompt = `Perform security analysis for: ${task}`;
  break;
```

### Customizing Devin Prompts

Modify the `createDevinSession` function to customize prompts based on your use case.

## Production Considerations

### Security
- Store credentials in environment variables
- Use proper secret management in production
- Implement rate limiting for API calls
- Add error handling and logging

### Scalability
- Implement session queuing for high volume
- Add database to track session history
- Implement webhook for session completion
- Add monitoring and alerting

### Reliability
- Add retry logic for failed API calls
- Implement circuit breakers
- Add health checks
- Implement graceful degradation

## Next Steps

1. **Add GitHub Integration**: Automatically create PRs from Devin sessions
2. **Add Linear Integration**: Update internal tickets with session status
3. **Add Sentry Integration**: Trigger sessions from error alerts
4. **Add Scheduled Tasks**: Daily security scans via Devin
5. **Add Multi-Channel Support**: Teams, Discord, etc.

## License

MIT

## Support

For issues with this implementation, please check:
- Slack API documentation: https://api.slack.com/
- Devin API documentation: https://docs.devin.ai/api-reference/overview
