import { API_BASE_URL } from '../config';

export async function sendMessage(message, sessionId) {
  const body = { message };
  if (sessionId) body.session_id = sessionId;

  const res = await fetch(`${API_BASE_URL}/chat/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function getStatus() {
  const res = await fetch(`${API_BASE_URL}/status/`);
  if (!res.ok) throw new Error(`Status check failed: ${res.status}`);
  return res.json();
}
