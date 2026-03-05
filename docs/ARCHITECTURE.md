# JARVIS System Architecture

## Overview

JARVIS is a modular AI assistant built around nine independent layers, each responsible for a specific concern and replaceable without affecting the others.

```
┌────────────────────────────────────────────────┐
│              INTERFACE LAYER                   │
│   Desktop Dashboard (Web)  •  Mobile App      │
└────────────────┬───────────────────────────────┘
                 │ HTTP / WebSocket
┌────────────────▼───────────────────────────────┐
│              API SERVER (FastAPI)               │
│  /chat  /voice  /tasks  /memory  /status  /ws  │
└────────────────┬───────────────────────────────┘
                 │
┌────────────────▼───────────────────────────────┐
│           PERCEPTION LAYER                      │
│  SpeechRecognizer  TextInput  WakeWord  Normalizer │
└────────────────┬───────────────────────────────┘
                 │
┌────────────────▼───────────────────────────────┐
│           REASONING LAYER (AI Brain)            │
│  BrainInterface ◄── LocalLLM (Ollama)          │
│                ◄── [future: custom transformer] │
└────────────────┬───────────────────────────────┘
                 │
┌────────────────▼───────────────────────────────┐
│        AGENT ORCHESTRATION LAYER                │
│  Commander  Planner  Reasoning  Specialists     │
│              ↕  MessageBus (pub/sub)            │
└────────────────┬───────────────────────────────┘
                 │
┌────────────────▼───────────────────────────────┐
│         TOOL & PLUGIN LAYER                     │
│  Browser  FileManager  WebSearch  DocProcessor  │
│  SystemMonitor  PluginLoader                    │
└────────────────┬───────────────────────────────┘
                 │
┌────────────────▼───────────────────────────────┐
│          EXECUTION ENGINE                       │
│  Executor  AppLauncher  ScriptRunner            │
│  FileOperations  BrowserController  APIClient   │
└────────────────┬───────────────────────────────┘
                 │
┌────────────────▼───────────────────────────────┐
│            MEMORY SYSTEM                        │
│  ShortTerm  LongTerm  Knowledge  Embeddings     │
└────────────────┬───────────────────────────────┘
                 │
┌────────────────▼───────────────────────────────┐
│           SECURITY LAYER                        │
│  Validator  Permissions  Sandbox  Auth          │
│  Confirmation  Encryption                       │
└────────────────────────────────────────────────┘
```

## Key Design Principles

1. **Replaceable Brain** – `BrainInterface` is an ABC; swap Ollama for a custom model with no other changes.
2. **Security First** – Every execution path passes through `CommandValidator` and `PermissionManager`.
3. **Async Throughout** – All I/O operations use `async/await` to avoid blocking.
4. **Modular Layers** – Each layer can be tested and deployed independently.

## Data Flow

1. Input arrives via API (`/chat/` or `/voice/transcribe`)
2. `InputNormalizer` cleans and tags the input
3. `CommanderAgent` interprets intent and orchestrates agents
4. Agents use tools and call the AI brain as needed
5. Results pass through `ResponseManager` for formatting/TTS
6. Response is returned via HTTP and/or WebSocket broadcast
