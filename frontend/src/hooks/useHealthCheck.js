/**
 * useHealthCheck.js — Custom React hook for backend health polling.
 */

import { useState, useEffect, useCallback } from 'react';
import { checkHealth } from '../services/api';

/**
 * @typedef {'idle' | 'loading' | 'connected' | 'error'} HealthStatus
 */

/**
 * Hook that checks backend health on mount and exposes refresh capability.
 * @returns {{ status: HealthStatus, service: string | null, retry: Function }}
 */
export function useHealthCheck() {
  const [status, setStatus] = useState('loading');
  const [service, setService] = useState(null);

  const check = useCallback(async () => {
    setStatus('loading');
    try {
      const data = await checkHealth();
      setService(data.service);
      setStatus('connected');
    } catch {
      setService(null);
      setStatus('error');
    }
  }, []);

  useEffect(() => {
    check();
  }, [check]);

  return { status, service, retry: check };
}
