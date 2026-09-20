require('dotenv').config();
const express = require('express');
const bodyParser = require('body-parser');
const axios = require('axios');
const crypto = require('crypto');

const app = express();
const PORT = process.env.PORT || 3000;

// Devin API configuration
const DEVIN_API_BASE = 'https://api.devin.ai/v3';
const DEVIN_API_KEY = process.env.DEVIN_API_KEY;
const DEVIN_ORG_ID = process.env.DEVIN_ORG_ID;

// GitHub webhook secret
const GITHUB_WEBHOOK_SECRET = process.env.GITHUB_WEBHOOK_SECRET;

// Middleware to verify GitHub webhook signature
function verifyGitHubSignature(req, res, next) {
  const signature = req.headers['x-hub-signature-256'];
  if (!signature) {
    return res.status(401).json({ error: 'No signature provided' });
  }

  const hmac = crypto.createHmac('sha256', GITHUB_WEBHOOK_SECRET);
  const digest = hmac.update(req.body).digest('hex');
  const expectedSignature = `sha256=${digest}`;

  if (signature !== expectedSignature) {
    return res.status(401).json({ error: 'Invalid signature' });
  }

  next();
}

// Function to create Devin session via API
async function createDevinSession(prompt, sessionLinks = []) {
  try {
    const response = await axios.post(
      `${DEVIN_API_BASE}/organizations/${DEVIN_ORG_ID}/sessions`,
      {
        prompt: prompt,
        session_links: sessionLinks,
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

    console.log('Devin API response:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error creating Devin session:', error.response?.data || error.message);
    if (error.response) {
      console.error('Response status:', error.response.status);
      console.error('Response data:', error.response.data);
    }
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

// Function to comment on GitHub issue
async function commentOnGitHubIssue(owner, repo, issueNumber, comment) {
  try {
    const response = await axios.post(
      `https://api.github.com/repos/${owner}/${repo}/issues/${issueNumber}/comments`,
      { body: comment },
      {
        headers: {
          'Authorization': `token ${process.env.GITHUB_TOKEN}`,
          'Content-Type': 'application/json'
        }
      }
    );

    return response.data;
  } catch (error) {
    console.error('Error commenting on GitHub issue:', error.response?.data || error.message);
    throw error;
  }
}

// GitHub webhook endpoint
app.post('/webhook/github', 
  bodyParser.raw({ type: 'application/json' }),
  verifyGitHubSignature,
  async (req, res) => {
    try {
      const payload = JSON.parse(req.body.toString());
      
      console.log('GitHub webhook received:', payload.action);

      // Handle issue creation
      if (payload.action === 'opened' && payload.issue) {
        const issue = payload.issue;
        const repository = payload.repository;

        console.log(`Processing issue #${issue.number}: ${issue.title}`);

        // Build prompt for Devin
        const prompt = `Analyze and help fix this GitHub issue:

Issue Title: ${issue.title}
Issue Body: ${issue.body}
Issue Number: ${issue.number}
Repository: ${repository.full_name}
Author: ${issue.user.login}

Context: This is an Apache Superset repository. Focus on the specific issue mentioned and provide a technical solution with code changes if applicable.`;

        // Create Devin session
        const session = await createDevinSession(
          prompt,
          [issue.html_url]
        );

        console.log(`Devin session created: ${session.session_id}`);

        // Comment on the GitHub issue
        const comment = `🤖 **Devin Automation**

I've created a Devin session to analyze this issue automatically.

**Session URL:** ${session.url}
**Session ID:** ${session.session_id}

Devin will analyze the issue and provide technical solutions. You can monitor the session progress at the link above.`;

        await commentOnGitHubIssue(
          repository.owner.login,
          repository.name,
          issue.number,
          comment
        );

        console.log(`Commented on issue #${issue.number}`);
      }

      res.status(200).json({ success: true });
    } catch (error) {
      console.error('Error processing webhook:', error);
      res.status(500).json({ error: 'Internal server error' });
    }
  }
);

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'ok', message: 'GitHub webhook handler is running' });
});

// Start the server
app.listen(PORT, () => {
  console.log(`🚀 GitHub webhook handler running on port ${PORT}`);
  console.log(`🔗 Webhook endpoint: http://localhost:${PORT}/webhook/github`);
  console.log(`❤️  Health check: http://localhost:${PORT}/health`);
});
