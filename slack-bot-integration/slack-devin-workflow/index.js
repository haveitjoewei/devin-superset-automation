require('dotenv').config();
const { App } = require('@slack/bolt');
const axios = require('axios');

const app = new App({
  token: process.env.SLACK_BOT_TOKEN,
  signingSecret: process.env.SLACK_SIGNING_SECRET,
  socketMode: true,
  appToken: process.env.SLACK_APP_TOKEN,
});

// Devin API configuration
const DEVIN_API_BASE = 'https://api.devin.ai/v3';
const DEVIN_API_KEY = process.env.DEVIN_API_KEY;
const DEVIN_ORG_ID = process.env.DEVIN_ORG_ID;

// Function to create Devin session
async function createDevinSession(prompt, context = {}) {
  try {
    const response = await axios.post(
      `${DEVIN_API_BASE}/organizations/${DEVIN_ORG_ID}/sessions`,
      {
        prompt: prompt,
        session_links: context.links || [],
        structured_output_required: true,
        structured_output_schema: {
          type: 'object',
          properties: {
            status: { type: 'string' },
            summary: { type: 'string' },
            files_changed: { type: 'array', items: { type: 'string' } },
            pull_request_url: { type: 'string' }
          }
        }
      },
      {
        headers: {
          'Authorization': `Bearer ${DEVIN_API_KEY}`,
          'Content-Type': 'application/json'
        }
      }
    );

    return response.data;
  } catch (error) {
    console.error('Error creating Devin session:', error.response?.data || error.message);
    throw error;
  }
}

// Function to get Devin session status
async function getDevinSession(sessionId) {
  try {
    const response = await axios.get(
      `${DEVIN_API_BASE}/organizations/${DEVIN_ORG_ID}/sessions/${sessionId}`,
      {
        headers: {
          'Authorization': `Bearer ${DEVIN_API_KEY}`,
          'Content-Type': 'application/json'
        }
      }
    );

    return response.data;
  } catch (error) {
    console.error('Error getting Devin session:', error.response?.data || error.message);
    throw error;
  }
}

// Slack command handler
app.command('/devin', async ({ command, ack, respond, client }) => {
  await ack();

  const text = command.text.trim();
  const channel = command.channel_id;
  const user = command.user_id;

  // Parse the command
  const parts = text.split(' ');
  const action = parts[0].toLowerCase();
  const task = parts.slice(1).join(' ');

  try {
    // Show initial response
    await respond({
      text: `🤖 Creating Devin session to: ${action} ${task}`,
      response_type: 'in_channel'
    });

    // Build prompt based on action
    let prompt = '';
    let context = {};

    switch (action) {
      case 'fix':
        prompt = `Fix the following issue in the Apache Superset repository: ${task}`;
        break;
      case 'implement':
        prompt = `Implement the following feature in Apache Superset: ${task}`;
        break;
      case 'analyze':
        prompt = `Analyze the following in Apache Superset: ${task}`;
        break;
      case 'test':
        prompt = `Create tests for the following in Apache Superset: ${task}`;
        break;
      default:
        prompt = `Help with the following task in Apache Superset: ${text}`;
    }

    // Add repository context
    context.links = ['https://github.com/apache/superset'];

    // Create Devin session
    const session = await createDevinSession(prompt, context);

    // Send session link to Slack
    await client.chat.postMessage({
      channel: channel,
      text: `✅ Devin session created!`,
      blocks: [
        {
          type: 'section',
          text: {
            type: 'mrkdwn',
            text: `✅ *Devin session created*\n\n*Task:* ${action} ${task}\n*Session URL:* ${session.url}\n*Session ID:* ${session.session_id}`
          }
        },
        {
          type: 'actions',
          elements: [
            {
              type: 'button',
              text: {
                type: 'plain_text',
                text: 'Open Session'
              },
              url: session.url,
              action_id: 'open_session'
            },
            {
              type: 'button',
              text: {
                type: 'plain_text',
                text: 'Check Status'
              },
              action_id: 'check_status',
              value: session.session_id
            }
          ]
        }
      ]
    });

  } catch (error) {
    await respond({
      text: `❌ Error creating Devin session: ${error.message}`,
      response_type: 'in_channel'
    });
  }
});

// Button action handler
app.action('check_status', async ({ action, ack, respond, body, client }) => {
  await ack();

  const sessionId = action.value;
  const channel = body.channel.id;

  try {
    await respond({
      text: '🔍 Checking session status...',
      response_type: 'in_channel'
    });

    const session = await getDevinSession(sessionId);

    await client.chat.postMessage({
      channel: channel,
      text: `📊 *Session Status*\n\n*Session ID:* ${session.session_id}\n*Status:* ${session.status}\n*URL:* ${session.url}`,
      blocks: [
        {
          type: 'section',
          text: {
            type: 'mrkdwn',
            text: `📊 *Session Status*\n\n*Session ID:* ${session.session_id}\n*Status:* ${session.status}\n*URL:* ${session.url}`
          }
        }
      ]
    });

  } catch (error) {
    await respond({
      text: `❌ Error checking session status: ${error.message}`,
      response_type: 'in_channel'
    });
  }
});

// Message handler for @mentions
app.message(/devin/i, async ({ message, say }) => {
  // Only respond to messages containing "devin"
  if (message.text && message.text.toLowerCase().includes('devin')) {
    const task = message.text.replace(/devin/gi, '').trim();

    if (task.length > 0) {
      try {
        await say(`🤖 Creating Devin session to help with: ${task}`);

        const session = await createDevinSession(
          `Help with the following task in Apache Superset: ${task}`,
          { links: ['https://github.com/apache/superset'] }
        );

        await say(`✅ Devin session created: ${session.url}`);

      } catch (error) {
        await say(`❌ Error creating Devin session: ${error.message}`);
      }
    }
  }
});

// Start the server
(async () => {
  await app.start(process.env.PORT || 3000);
  console.log('⚡️ Slack bot is running!');
})();
