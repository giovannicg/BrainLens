import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { apiService, ProcessingStatusResponse } from '../services/api';
import PredictionResults from '../components/PredictionResults';
import './PredictionResults.css';

const PredictionResultsPage: React.FC = () => {
  const { imageId } = useParams<{ imageId: string }>();
  const navigate = useNavigate();
  const [statusData, setStatusData] = useState<ProcessingStatusResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    if (imageId) {
      loadPredictionResults();
    }
  }, [imageId]);

  const loadPredictionResults = async () => {
    if (!imageId) return;

    try {
      setLoading(true);
      setError('');
      const data = await apiService.getProcessingStatus(imageId);
      setStatusData(data);
    } catch (err) {
      console.error('Error loading prediction results:', err);
      setError('Error al cargar los resultados de predicción');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string): string => {
    if (!dateString) return 'N/A';
    try {
      return new Date(dateString).toLocaleDateString('es-ES', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      });
    } catch (error) {
      return 'N/A';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return '#27ae60';
      case 'processing':
        return '#f39c12';
      case 'pending':
        return '#3498db';
      case 'failed':
        return '#e74c3c';
      default:
        return '#666';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'completed':
        return 'Completado';
      case 'processing':
        return 'Procesando';
      case 'pending':
        return 'Pendiente';
      case 'failed':
        return 'Falló';
      default:
        return status;
    }
  };

  if (loading) {
    return (
      <div className="prediction-results-page">
        <div className="loading">
          <div className="loading-spinner"></div>
          <p>Cargando resultados...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="prediction-results-page">
        <div className="error-message">
          <h2>❌ Error</h2>
          <p>{error}</p>
          <button onClick={() => navigate('/predictions')} className="back-button">
            ← Volver a Imágenes
          </button>
        </div>
      </div>
    );
  }

  if (!statusData) {
    return (
      <div className="prediction-results-page">
        <div className="error-message">
          <h2>❌ No se encontraron datos</h2>
          <p>No se pudieron cargar los resultados de predicción.</p>
          <button onClick={() => navigate('/predictions')} className="back-button">
            ← Volver a Imágenes
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="prediction-results-page">
      <div className="results-header">
        <button onClick={() => navigate('/images')} className="back-button">
          ← Volver a Imágenes
        </button>
        <h1>📊 Resultados del Análisis de Tumor</h1>
      </div>

      <div className="results-container">
        {/* Información del procesamiento */}
        <div className="processing-info">
          <h2>🔄 Información del Procesamiento</h2>
          <div className="info-grid">
            <div className="info-item">
              <strong>Estado:</strong>
              <span 
                className={`status-${statusData.status}`}
                style={{ color: getStatusColor(statusData.status) }}
              >
                {getStatusText(statusData.status)}
              </span>
            </div>
            <div className="info-item">
              <strong>Iniciado:</strong>
              <span>{formatDate(statusData.processing_started || '')}</span>
            </div>
            {statusData.processing_completed && (
              <div className="info-item">
                <strong>Completado:</strong>
                <span>{formatDate(statusData.processing_completed)}</span>
              </div>
            )}
          </div>
        </div>

        {/* Resultados de predicción */}
        {statusData && (
          <div className="prediction-section">
            <h2>🧠 Resultados de la Predicción</h2>
            <PredictionResults prediction={statusData} />
          </div>
        )}

  {/* Mensaje de estado eliminado: 'message' no existe en ProcessingStatusResponse */}
        {/* Acciones */}
        <div className="actions-section">
          <button onClick={() => navigate('/predictions')} className="action-button">
            🧠 Ver Todas las Predicciones
          </button>
          <button onClick={() => navigate('/images')} className="action-button">
            📋 Ver Todas las Imágenes
          </button>
          <button onClick={() => navigate('/upload')} className="action-button primary">
            📤 Subir Nueva Imagen
          </button>
        </div>
      </div>
    </div>
  );
};

export default PredictionResultsPage;
