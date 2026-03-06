export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
export const WS_URL = API_BASE_URL.replace('http', 'ws') + '/ws';
export const APP_VERSION = '0.1.0';
export const MODEL_NAME = 'llama3.1:8b';
