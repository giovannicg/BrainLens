import { useState, useEffect, useRef } from 'react';
import { apiService, ProcessingStatusResponse } from '../services/api';

interface UseProcessingStatusOptions {
  imageId: string;
  enabled?: boolean;
  interval?: number;
  onStatusChange?: (status: ProcessingStatusResponse) => void;
}

export const useProcessingStatus = ({
  imageId,
  enabled = true,
  interval = 2000,
  onStatusChange
}: UseProcessingStatusOptions) => {
  const [status, setStatus] = useState<ProcessingStatusResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const fetchStatus = async () => {
    if (!enabled || !imageId) return;

    try {
      setLoading(true);
      setError(null);
      const statusData = await apiService.getProcessingStatus(imageId);
      setStatus(statusData);
      
      if (onStatusChange) {
        onStatusChange(statusData);
      }

      // Si el procesamiento está completado o falló, detener el polling
      if (statusData.status === 'completed' || statusData.status === 'failed') {
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al obtener el estado');
      console.error('Error fetching processing status:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!enabled || !imageId) return;

    // Obtener estado inicial
    fetchStatus();

    // Configurar polling
    intervalRef.current = setInterval(fetchStatus, interval);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [imageId, enabled, interval]);

  const stopPolling = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  };

  const startPolling = () => {
    if (!intervalRef.current && enabled) {
      intervalRef.current = setInterval(fetchStatus, interval);
    }
  };

  return {
    status,
    loading,
    error,
    stopPolling,
    startPolling,
    refetch: fetchStatus
  };
};
