# JARVIS Mobile App

Specifications and API contracts for the iOS and Android mobile client.

## Overview

The mobile app provides:
- Voice input with wake-word detection
- Chat interface
- Speech playback of responses
- Background listening mode
- Push notifications for task completion

## Tech Stack (Recommended)

| Platform | Framework |
|----------|-----------|
| Cross-platform | React Native or Flutter |
| iOS native | Swift / SwiftUI |
| Android native | Kotlin / Jetpack Compose |

## API Endpoints Used

| Feature | Endpoint | Method |
|---------|----------|--------|
| Chat | `/chat/` | POST |
| Voice transcribe | `/voice/transcribe` | POST |
| Task status | `/tasks/history` | GET |
| Memory recall | `/memory/get/{key}` | GET |
| Real-time updates | `/ws` | WebSocket |
| Health check | `/status/` | GET |

## Authentication

All requests include a JWT in the Authorization header:

```
Authorization: Bearer <token>
```

Token acquisition endpoint (planned): `POST /auth/token`

## Chat Message Format

```json
POST /chat/
{
  "message": "What's the weather?",
  "session_id": "device-uuid-here",
  "speak": false
}
```

Response:
```json
{
  "response": "I don't have access to live weather data...",
  "session_id": "device-uuid-here",
  "spoken": false
}
```

## Voice Upload Format

```
POST /voice/transcribe
Content-Type: multipart/form-data
audio: <binary audio file> (WAV, MP3, M4A)
```

Response:
```json
{
  "text": "Turn off the lights",
  "available": true
}
```

## WebSocket Events

Connect to `ws://<host>:8000/ws`.

### Server → Client

```json
{"type": "task_complete", "task_id": "...", "result": {...}}
{"type": "agent_event", "agent": "Commander", "data": {...}}
{"type": "ack", "echo": {...}}
```

### Client → Server

```json
{"type": "ping"}
{"type": "subscribe", "channel": "tasks"}
```

## Wake Word

- Default phrase: **"Hey JARVIS"**
- Configurable in app settings
- Uses on-device keyword spotting (pvporcupine recommended)

## Security Notes

- HTTPS required in production (use TLS certificates)
- JWT tokens expire after 1 hour; implement refresh flow
- Audio is processed locally before upload when possible
- Sensitive data stored in platform secure storage (Keychain / Keystore)
