import { useState, useEffect, useRef, useCallback } from 'react';
import { WS_URL } from '../config';

export function useWebSocket(onMessage) {
  const [status, setStatus] = useState('disconnected');
  const wsRef = useRef(null);
  const reconnectRef = useRef(null);
  const mountedRef = useRef(true);

  const connect = useCallback(() => {
    if (!mountedRef.current) return;
    try {
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;
      setStatus('connecting');

      ws.onopen = () => { if (mountedRef.current) setStatus('connected'); };
      ws.onmessage = (e) => { if (mountedRef.current && onMessage) onMessage(e.data); };
      ws.onerror = () => { if (mountedRef.current) setStatus('error'); };
      ws.onclose = () => {
        if (!mountedRef.current) return;
        setStatus('disconnected');
        reconnectRef.current = setTimeout(connect, 5000);
      };
    } catch {
      setStatus('error');
    }
  }, [onMessage]);

  useEffect(() => {
    mountedRef.current = true;
    connect();
    return () => {
      mountedRef.current = false;
      clearTimeout(reconnectRef.current);
      if (wsRef.current) wsRef.current.close();
    };
  }, [connect]);

  const send = useCallback((data) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(typeof data === 'string' ? data : JSON.stringify(data));
    }
  }, []);

  return { status, send };
}
