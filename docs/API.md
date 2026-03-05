# JARVIS API Documentation

Base URL: `http://localhost:8000`

Interactive docs: `http://localhost:8000/docs`

## Authentication

When `require_auth: true` in config, include a JWT Bearer token:

```
Authorization: Bearer <token>
```

## Endpoints

### GET /
Root endpoint. Returns API name and links.

### GET /status/
Health check. Returns system status, timestamp, and platform info.

### GET /status/version
Returns version and build information.

---

### POST /chat/
Send a text message and receive a response.

**Request body:**
```json
{
  "message": "What is the capital of France?",
  "session_id": "optional-session-id",
  "speak": false
}
```

**Response:**
```json
{
  "response": "The capital of France is Paris.",
  "session_id": "default",
  "spoken": false
}
```

---

### POST /voice/transcribe
Upload an audio file and receive a text transcription.

**Request:** `multipart/form-data` with `audio` field (WAV/MP3/M4A)

**Response:**
```json
{
  "text": "Turn on the lights",
  "available": true
}
```

---

### POST /tasks/execute
Execute a system task.

**Request body:**
```json
{
  "action_type": "file.read",
  "parameters": {"path": "README.md"}
}
```

**Supported action types:**
- `file.read` – params: `path`
- `file.write` – params: `path`, `content`
- `file.delete` – params: `path`
- `app.launch` – params: `app`, `args`
- `script.python` – params: `script`
- `shell.run` – params: `command`
- `browser.navigate` – params: `url`

---

### GET /tasks/history?limit=50
Returns recent task execution history.

---

### POST /memory/set
Store a key-value pair in long-term memory.

```json
{"key": "user_name", "value": "Alice"}
```

### GET /memory/get/{key}
Retrieve a value from long-term memory.

### GET /memory/keys
List all memory keys.

### POST /memory/learn
Add a document to knowledge memory.

```json
{"content": "...", "title": "My Doc", "tags": ["tag1"]}
```

### GET /memory/search?q=query&limit=5
Search knowledge memory.

---

## WebSocket

Connect to `ws://localhost:8000/ws` for real-time updates.

Messages are JSON objects. The server echoes received messages with `"type": "ack"`.
