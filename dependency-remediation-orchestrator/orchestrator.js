require('dotenv').config();
const express = require('express');
const bodyParser = require('body-parser');
const crypto = require('crypto');
const axios = require('axios');

const app = express();
const PORT = process.env.PORT || 3000;

// Devin API configuration
const DEVIN_API_BASE = 'https://api.devin.ai/v3';
const DEVIN_API_KEY = process.env.DEVIN_API_KEY;
const DEVIN_ORG_ID = process.env.DEVIN_ORG_ID;

// GitHub configuration
const GITHUB_WEBHOOK_SECRET = process.env.GITHUB_WEBHOOK_SECRET;
const GITHUB_TOKEN = process.env.GITHUB_TOKEN;

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
            dependency_name: { type: 'string' },
            current_version: { type: 'string' },
            target_version: { type: 'string' },
            files_changed: { type: 'array', items: { type: 'string' } },
            fix_summary: { type: 'string' },
            validation_status: { type: 'string' }
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

    console.log('Devin session created:', response.data.session_id);
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

// Function to comment on GitHub issue
async function commentOnGitHubIssue(owner, repo, issueNumber, comment) {
  try {
    const response = await axios.post(
      `https://api.github.com/repos/${owner}/${repo}/issues/${issueNumber}/comments`,
      { body: comment },
      {
        headers: {
          'Authorization': `token ${GITHUB_TOKEN}`,
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

// Dependency issue patterns
const dependencyPatterns = {
  apispec: {
    current: 'apispec>=6.0.0,<6.7.0',
    target: 'apispec>=6.7.0',
    description: 'breaking unit test in 6.7.0',
    issue_reference: 'Known issue with 6.7.0 breaking a unit test'
  },
  'marshmallow-sqlalchemy': {
    current: 'marshmallow-sqlalchemy>=1.5.0',
    target: 'marshmallow-sqlalchemy>=1.5.0',
    description: 'memory regression in test suite',
    issue_reference: '1.4.1 introduced a memory regression'
  },
  'google-auth': {
    current: 'google-auth>=2.53.0,<3.0.0',
    target: 'google-auth>=2.53.0',
    description: 'install-path consistency issue',
    issue_reference: 'google-auth 2.53+ dropped its transitive dependency on cachetools'
  }
};

// Function to detect dependency issue from issue
function detectDependencyIssue(issue) {
  const content = (issue.title + ' ' + (issue.body || '')).toLowerCase();
  
  for (const [dep, config] of Object.entries(dependencyPatterns)) {
    if (content.includes(dep.toLowerCase()) || 
        content.includes(config.description.toLowerCase()) ||
        content.includes(config.issue_reference.toLowerCase())) {
      return { dependency: dep, config };
    }
  }
  
  return null;
}

// GitHub webhook endpoint for dependency issues
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

        // Check if this is a dependency issue
        const dependencyIssue = detectDependencyIssue(issue);
        
        if (dependencyIssue) {
          console.log(`Dependency issue detected: ${dependencyIssue.dependency}`);
          
          // Build prompt for Devin
          const prompt = `Analyze and fix this dependency upgrade blocker:

**Dependency:** ${dependencyIssue.dependency}
**Current constraint:** ${dependencyIssue.config.current}
**Target version:** ${dependencyIssue.config.target}
**Issue:** ${dependencyIssue.config.description}
**Reference:** ${dependencyIssue.config.issue_reference}

**Issue Context:**
Title: ${issue.title}
Body: ${issue.body}
Repository: ${repository.full_name}

**Task:**
1. Investigate why the current version constraint is in place
2. Analyze the code that uses this dependency
3. Identify what would break with the target version
4. Implement the necessary code changes to make the upgrade compatible
5. Update any related tests
6. Provide a comprehensive fix that allows unpinning the dependency

**Validation:**
- The fix should allow unpinning the dependency to the target version
- All tests should pass
- No breaking changes to existing functionality
- Follow Superset's coding standards`;

          // Create Devin session
          const session = await createDevinSession(
            prompt,
            [issue.html_url]
          );

          console.log(`Devin session created: ${session.session_id}`);

          // Comment on the GitHub issue
          const comment = `🤖 **Dependency Remediation Automation**

I've created a Devin session to analyze and fix the **${dependencyIssue.dependency}** dependency upgrade blocker.

**Session URL:** ${session.url}
**Session ID:** ${session.session_id}

**Issue Being Addressed:**
- Current constraint: \`${dependencyIssue.config.current}\`
- Target version: \`${dependencyIssue.config.target}\`
- Problem: ${dependencyIssue.config.description}

Devin will investigate the code, implement necessary fixes, and provide a validated solution. You can monitor the session progress at the link above.

**Expected Outcome:**
- Code changes to make the upgrade compatible
- Updated tests if needed
- Validation that the fix works
- Pull request with the complete remediation`;

          await commentOnGitHubIssue(
            repository.owner.login,
            repository.name,
            issue.number,
            comment
          );

          console.log(`Commented on issue #${issue.number}`);
        } else {
          console.log('No dependency issue detected in this issue');
        }
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
  res.json({ 
    status: 'ok', 
    message: 'Dependency remediation orchestrator is running',
    dependencies: Object.keys(dependencyPatterns)
  });
});

// Start the server
app.listen(PORT, () => {
  console.log(`🚀 Dependency remediation orchestrator running on port ${PORT}`);
  console.log(`🔗 Webhook endpoint: http://localhost:${PORT}/webhook/github`);
  console.log(`❤️  Health check: http://localhost:${PORT}/health`);
  console.log(`📦 Monitored dependencies: ${Object.keys(dependencyPatterns).join(', ')}`);
});
