import React from 'react';
import './PredictionResults.css';

interface PredictionResultsProps {
  prediction: {
    es_tumor: boolean;
    clase_predicha: string;
    confianza: number;
    probabilidades: Record<string, number>;
    recomendacion: string;
  };
}

const PredictionResults: React.FC<PredictionResultsProps> = ({ prediction }) => {
  const getStatusColor = (esTumor: boolean) => {
    return esTumor ? '#e74c3c' : '#27ae60';
  };

  const getStatusIcon = (esTumor: boolean) => {
    return esTumor ? '⚠️' : '✅';
  };

  const getStatusText = (esTumor: boolean) => {
    return esTumor ? 'Tumor Detectado' : 'Sin Tumor';
  };

  const getClassColor = (clase: string) => {
    const colors: Record<string, string> = {
      'glioma': '#e74c3c',
      'meningioma': '#f39c12',
      'no_tumor': '#27ae60',
      'pituitary': '#9b59b6'
    };
    return colors[clase] || '#666';
  };

  const getClassName = (clase: string) => {
    const names: Record<string, string> = {
      'glioma': 'Glioma',
      'meningioma': 'Meningioma',
      'no_tumor': 'Sin Tumor',
      'pituitary': 'Pituitario'
    };
    return names[clase] || clase;
  };

  const sortedProbabilities = Object.entries(prediction.probabilidades)
    .sort(([, a], [, b]) => b - a);

  return (
    <div className="prediction-results">
      <div className="prediction-header">
        <h3>Resultados del Análisis</h3>
        <div 
          className="prediction-status"
          style={{ color: getStatusColor(prediction.es_tumor) }}
        >
          {getStatusIcon(prediction.es_tumor)} {getStatusText(prediction.es_tumor)}
        </div>
      </div>

      <div className="prediction-content">
        <div className="prediction-summary">
          <div className="prediction-item">
            <span className="prediction-label">Clase Predicha:</span>
            <span 
              className="prediction-value"
              style={{ color: getClassColor(prediction.clase_predicha) }}
            >
              {getClassName(prediction.clase_predicha)}
            </span>
          </div>
          
          <div className="prediction-item">
            <span className="prediction-label">Confianza:</span>
            <span className="prediction-value">
              {(prediction.confianza * 100).toFixed(1)}%
            </span>
          </div>
        </div>

        <div className="probabilities-section">
          <h4>Probabilidades por Clase:</h4>
          <div className="probabilities-list">
            {sortedProbabilities.map(([clase, probabilidad]) => (
              <div key={clase} className="probability-item">
                <div className="probability-header">
                  <span 
                    className="probability-class"
                    style={{ color: getClassColor(clase) }}
                  >
                    {getClassName(clase)}
                  </span>
                  <span className="probability-percentage">
                    {(probabilidad * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="probability-bar">
                  <div 
                    className="probability-fill"
                    style={{ 
                      width: `${probabilidad * 100}%`,
                      backgroundColor: getClassColor(clase)
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="recommendation-section">
          <h4>Recomendación:</h4>
          <div className="recommendation-text">
            {prediction.recomendacion}
          </div>
        </div>
      </div>
    </div>
  );
};

export default PredictionResults;
