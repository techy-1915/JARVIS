export function formatTimestamp(date) {
  return new Date(date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

export function formatDate(date) {
  const d = new Date(date);
  const now = new Date();
  const diff = now - d;
  const day = 86400000;
  if (diff < day) return 'Today';
  if (diff < 2 * day) return 'Yesterday';
  return d.toLocaleDateString([], { month: 'short', day: 'numeric' });
}

export function truncate(str, n = 40) {
  return str.length > n ? str.slice(0, n) + '…' : str;
}
