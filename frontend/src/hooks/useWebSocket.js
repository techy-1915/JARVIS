import { useState, useEffect, useRef, useCallback } from 'react';
import { WS_URL } from '../config';

const WS_RECONNECT_DELAY_MS = 5000;

export function useWebSocket(onMessage) {
  const [status, setStatus] = useState('disconnected');
  const wsRef = useRef(null);
  const reconnectRef = useRef(null);
  const mountedRef = useRef(true);
  const connectRef = useRef(null);
  const onMessageRef = useRef(onMessage);

  useEffect(() => { onMessageRef.current = onMessage; }, [onMessage]);

  useEffect(() => {
    mountedRef.current = true;

    const connect = () => {
      if (!mountedRef.current) return;
      try {
        const ws = new WebSocket(WS_URL);
        wsRef.current = ws;
        setStatus('connecting');

        ws.onopen = () => { if (mountedRef.current) setStatus('connected'); };
        ws.onmessage = (e) => { if (mountedRef.current && onMessageRef.current) onMessageRef.current(e.data); };
        ws.onerror = () => { if (mountedRef.current) setStatus('error'); };
        ws.onclose = () => {
          if (!mountedRef.current) return;
          setStatus('disconnected');
          reconnectRef.current = setTimeout(connectRef.current, WS_RECONNECT_DELAY_MS);
        };
      } catch {
        setStatus('error');
      }
    };
    connectRef.current = connect;
    connect();

    return () => {
      mountedRef.current = false;
      clearTimeout(reconnectRef.current);
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  const send = useCallback((data) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(typeof data === 'string' ? data : JSON.stringify(data));
    }
  }, []);

  return { status, send };
}
