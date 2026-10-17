# server.js Reference Pattern

This annotated reference shows the exact patterns to follow when generating `server.js` for a
BAW custom user task interface. Adapt field names and routes to match the user's schema.

---

## Boilerplate setup

```js
require('dotenv').config();
const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');
const axios = require('axios');
const https = require('https');
const fs = require('fs');
const path = require('path');

// Fail-fast environment variable validation
const PLACEHOLDER = /^(your_username|your_password|<.+>)$|your-baw-server/i;
const missing = ['BAW_SERVER_BASE_URL', 'BAW_USERNAME', 'BAW_PASSWORD'].filter((name) => {
  const value = (process.env[name] || '').trim();
  return !value || PLACEHOLDER.test(value);
});
if (missing.length) {
  console.error(`Missing or placeholder values in .env: ${missing.join(', ')}. See .env.example.`);
  process.exit(1);
}

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));
app.use(express.static('public'));

// Honour the IGNORE_SSL_CERTIFICATES env flag for dev environments
const httpsAgent = new https.Agent({
  rejectUnauthorized: process.env.IGNORE_SSL_CERTIFICATES !== 'true'
});

const BAW_BASE_URL = process.env.BAW_SERVER_BASE_URL.replace(/\/+$/, '') + '/bpm/';
const BAW_USERNAME = process.env.BAW_USERNAME;
const BAW_PASSWORD = process.env.BAW_PASSWORD;

// Schema source: the exported OpenAPI contract (ExtRest.json) or fields-spec.json for described fields
const SCHEMA_FILE = path.basename(process.env.SCHEMA_FILE || 'ExtRest.json');
```

---

## CSRF token helper & auto-retry

```js
async function getCsrfToken() {
  const response = await axios.post(
    `${BAW_BASE_URL}system/login`,
    { refresh_groups: false },
    {
      auth: { username: BAW_USERNAME, password: BAW_PASSWORD },
      httpsAgent,
      headers: { 'Content-Type': 'application/json' }
    }
  );
  return response.data.csrf_token;
}

async function retryWithFreshToken(apiCall) {
  try {
    return await apiCall();
  } catch (error) {
    if (
      error.response?.status === 403 &&
      error.response?.data?.Data?.errorMessage?.includes('CWTBG0651E')
    ) {
      // CSRF token expired; retry once
      return await apiCall();
    }
    throw error;
  }
}
```

---

## Schema endpoint with inline $ref resolution

```js
app.get('/api/schema', (req, res) => {
  try {
    const raw = fs.readFileSync(path.join(__dirname, SCHEMA_FILE), 'utf8');
    const schema = JSON.parse(raw);

    function resolveRefs(obj, root) {
      if (typeof obj !== 'object' || obj === null) return obj;
      if (Array.isArray(obj)) return obj.map(item => resolveRefs(item, root));
      const resolved = {};
      for (const [key, value] of Object.entries(obj)) {
        if (key === '$ref' && typeof value === 'string') {
          const parts = value.replace('#/', '').split('/');
          let ref = root;
          for (const part of parts) ref = ref ? ref[part] : undefined;
          return resolveRefs(ref, root);
        }
        resolved[key] = resolveRefs(value, root);
      }
      return resolved;
    }

    res.json(resolveRefs(schema, schema));
  } catch (err) {
    console.error('Schema load error:', err.message);
    res.status(500).json({ error: 'Failed to load schema' });
  }
});
```

---

## Config endpoint

```js
app.get('/api/config', (req, res) => {
  res.json({
    bawServerUrl: process.env.BAW_SERVER_BASE_URL
  });
});
```

---

## Fetch user task endpoint

```js
app.get('/api/user-task/:taskId', async (req, res) => {
  const { taskId } = req.params;
  try {
    const result = await retryWithFreshToken(async () => {
      const csrfToken = await getCsrfToken();
      const response = await axios.get(
        `${BAW_BASE_URL}user-tasks/${taskId}`,
        {
          params: { optional_parts: 'data' },
          auth: { username: BAW_USERNAME, password: BAW_PASSWORD },
          httpsAgent,
          headers: {
            'BPMCSRFToken': csrfToken,
            'Content-Type': 'application/json'
          }
        }
      );
      return response.data;
    });
    res.json(result);
  } catch (err) {
    console.error('Fetch task error:', err.response?.data || err.message);
    res.status(err.response?.status || 500).json({
      error: 'Failed to fetch user task',
      details: err.response?.data || err.message
    });
  }
});
```

---

## Complete user task endpoint

```js
app.post('/api/user-task/:taskId/complete', async (req, res) => {
  const { taskId } = req.params;
  const outputData = req.body; // Expects { output: [{name, data}] }
  try {
    const result = await retryWithFreshToken(async () => {
      const csrfToken = await getCsrfToken();
      const response = await axios.post(
        `${BAW_BASE_URL}user-tasks/${taskId}/complete`,
        outputData,
        {
          auth: { username: BAW_USERNAME, password: BAW_PASSWORD },
          httpsAgent,
          headers: {
            'BPMCSRFToken': csrfToken,
            'Content-Type': 'application/json'
          }
        }
      );
      return response.data;
    });
    res.json(result);
  } catch (err) {
    console.error('Complete task error:', err.response?.data || err.message);
    res.status(err.response?.status || 500).json({
      error: 'Failed to complete user task',
      details: err.response?.data || err.message
    });
  }
});
```

---

## Main page & bind to localhost

```js
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Bind to 127.0.0.1 — never 0.0.0.0
app.listen(PORT, '127.0.0.1', () => {
  console.log(`Server running on http://127.0.0.1:${PORT}`);
  console.log(`BAW Base URL: ${BAW_BASE_URL}`);
});
```

---

## Data transformation helpers (Client or Server)

**Reading input array from BAW:**
```js
function inputArrayToMap(inputArray) {
  const map = {};
  (inputArray || []).forEach(item => {
    if (!item.name.startsWith('@')) {
      map[item.name] = item.data;
    }
  });
  return map;
}
```

**Serializing form values to output array for BAW:**
```js
function formDataToOutputArray(formValues) {
  return Object.entries(formValues)
    .filter(([name]) => !name.startsWith('@'))
    .map(([name, data]) => ({ name, data }));
}
```
