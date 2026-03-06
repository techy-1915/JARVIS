# JARVIS Frontend

A modern React-based chat interface for the JARVIS AI assistant.

## Tech Stack

- **React 18** with functional components and hooks
- **Vite** for fast builds and dev server
- **Tailwind CSS** for styling
- **react-markdown** + **remark-gfm** for Markdown rendering
- **react-syntax-highlighter** for code blocks
- **uuid** for unique IDs

## Getting Started

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

## Building

```bash
npm run build
```

## Configuration

Set `VITE_API_URL` environment variable to point to a different API backend (default: http://localhost:8000).

## Features

- Dark theme ChatGPT-like UI
- Markdown + code syntax highlighting
- Conversation history stored in localStorage
- WebSocket connection status
- Collapsible sidebar and event log panel
- Responsive layout
