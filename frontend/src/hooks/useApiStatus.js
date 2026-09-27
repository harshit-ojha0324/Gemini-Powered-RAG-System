import { useEffect, useState } from 'react';
import api from '../services/api';

const POLL_MS = 15000;

/** 'checking' until the first health check returns, then 'online' or 'offline'. */
export default function useApiStatus() {
  const [status, setStatus] = useState('checking');

  useEffect(() => {
    let cancelled = false;
    const check = async () => {
      try {
        await api.get('/api/health', { timeout: 5000 });
        if (!cancelled) setStatus('online');
      } catch {
        if (!cancelled) setStatus('offline');
      }
    };

    check();
    const timer = setInterval(check, POLL_MS);
    window.addEventListener('focus', check);
    return () => {
      cancelled = true;
      clearInterval(timer);
      window.removeEventListener('focus', check);
    };
  }, []);

  return status;
}
