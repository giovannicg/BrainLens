import React from 'react';
import './PredictionResults.css';


import { ProcessingStatusResponse } from '../services/api';

interface PredictionResultsProps {
  prediction: ProcessingStatusResponse;
}


const PredictionResults: React.FC<PredictionResultsProps> = ({ prediction }) => {
  // Si no hay predicción válida, mostrar error

  if (!prediction || prediction.status !== 'completed' || !prediction.prediction) {
    return (
      <div className="prediction-results">
        <div className="error-message">
          <h3>❌ Error en la predicción</h3>
          <p>No se pudo obtener la predicción para esta imagen.</p>
        </div>
      </div>
    );
  }


  const getStatusColor = (esTumor: boolean) => {
    return esTumor ? '#e74c3c' : '#27ae60';
  };
  const getStatusIcon = (esTumor: boolean) => {
    return esTumor ? '⚠️' : '✅';
  };
  const getStatusText = (esTumor: boolean) => {
    return esTumor ? 'Tumor Detectado' : 'Sin Tumor';
  };

  const getProcessingTime = () => {
    if (prediction.processing_started && prediction.processing_completed) {
      try {
        const start = new Date(prediction.processing_started).getTime();
        const end = new Date(prediction.processing_completed).getTime();
        if (isNaN(start) || isNaN(end) || end < start) return 'N/A';
        return ((end - start) / 1000).toFixed(2) + 's';
      } catch {
        return 'N/A';
      }
    }
    return 'N/A';
  };

  return (
    <div className="prediction-results">
      <div className="prediction-header">
        <h3>Resultados del Análisis</h3>
        <div 
          className="prediction-status"
          style={{ color: getStatusColor(prediction.prediction.es_tumor) }}
        >
          {getStatusIcon(prediction.prediction.es_tumor)} {getStatusText(prediction.prediction.es_tumor)}
        </div>
      </div>

      <div className="prediction-content">
        <div className="prediction-summary">
          <div className="prediction-item">
            <span className="prediction-label">Confianza:</span>
            <span className="prediction-value">
              {typeof prediction.prediction.confianza === 'number' ? prediction.prediction.confianza.toFixed(3) : 'N/A'}
            </span>
          </div>
          <div className="prediction-item">
            <span className="prediction-label">Clase predicha:</span>
            <span className="prediction-value">{prediction.prediction.clase_predicha}</span>
          </div>
          <div className="prediction-item">
            <span className="prediction-label">Tiempo de procesamiento:</span>
            <span className="prediction-value">
              {getProcessingTime()}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PredictionResults;
