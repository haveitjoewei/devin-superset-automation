# Slack Bot Integration

Real-time Slack workflow automation using Devin API for the Apache Superset project.

## Features

- **Slash Commands**: `/devin fix`, `/devin implement`, `/devin analyze`, `/devin test`
- **Message Triggers**: Automatic response to messages containing "devin"
- **Session Management**: Create and monitor Devin sessions programmatically
- **Interactive UI**: Buttons to open sessions and check status
- **Structured Output**: Consistent JSON responses from Devin

## Setup Instructions

See [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed setup instructions.

## Usage

### Slash Commands

```bash
cd slack-bot-integration
npm start

# In Slack:
/devin fix issue #44433
/devin implement OAuth2 support
/devin analyze security vulnerability
/devin test user authentication
```

### Message Triggers

Simply mention "devin" in any Slack message:
```
Can devin help fix the SQL injection?
```

## Architecture

```
Slack Message → Slack Bot → Devin API → Devin Session → Slack Reply
```

## Requirements

- Node.js 18+
- Slack app with bot permissions
- Devin API key with `ManageOrgSessions` permission
- Slack bot token, signing secret, and app token

## License

MIT
