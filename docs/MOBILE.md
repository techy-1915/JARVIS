# JARVIS Mobile App Specifications

See also: `mobile_app/api_contract.yaml` for the OpenAPI contract.

## Recommended Stack

- **React Native** (cross-platform) or **Flutter**
- JWT authentication stored in platform Secure Storage
- Background wake-word detection via on-device model (pvporcupine)

## Key User Flows

### 1. Voice Interaction
1. User says "Hey JARVIS" → wake word detected
2. App begins recording audio
3. Audio uploaded to `POST /voice/transcribe`
4. Transcribed text sent to `POST /chat/`
5. Response displayed and optionally spoken via TTS

### 2. Chat Interaction
1. User types message in chat UI
2. Message sent to `POST /chat/`
3. Response displayed in chat bubble

### 3. Task Monitoring
1. App connects to `ws://host:8000/ws`
2. Server pushes `task_complete` events
3. App displays push notification

## Security

- All communication over HTTPS in production
- JWT tokens stored in iOS Keychain / Android Keystore
- Token refresh flow to be implemented at `POST /auth/refresh`
