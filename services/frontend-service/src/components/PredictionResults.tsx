import React, { useState } from 'react';
import './PredictionResults.css';
import { ProcessingStatusResponse, apiService } from '../services/api';

interface PredictionResultsProps {
  prediction: ProcessingStatusResponse; // <- usar el tipo del API
}

const getClassName = (clase: string): string => {
  const names: Record<string, string> = {
    glioma: 'Glioma',
    meningioma: 'Meningioma',
    pituitary: 'Tumor Pituitario',
    no_tumor: 'Sin Tumor',
  };
  return names[clase] || clase;
};

const getClassColor = (clase: string): string => {
  const colors: Record<string, string> = {
    glioma: '#8e44ad',
    meningioma: '#2980b9',
    pituitary: '#d35400',
    no_tumor: '#27ae60',
  };
  return colors[clase] || '#2c3e50';
};

// Normaliza status del API a lo que muestra la UI
const toUiStatus = (s: ProcessingStatusResponse['status']) =>
  s === 'failed' ? 'error' : s; // 'failed' -> 'error'

const PredictionResults: React.FC<PredictionResultsProps> = ({ prediction }) => {

  // Función de apoyo alineada con ApiService para evitar falsos positivos por "notumor"
  const isTumorLabel = (label: string): boolean => {
    const norm = String(label || '').toLowerCase().trim().replace(/\s+/g, '_');
    const noTumorSet = new Set(['no_tumor','notumor','sin_tumor','no-tumor','negativo']);
    if (noTumorSet.has(norm)) return false;
    return norm === 'tumor' || norm === 'tumour' || norm === 'positivo';
  };

  // si no hay predicción lista
  if (!prediction || toUiStatus(prediction.status) !== 'completed' || !prediction.prediction) {
    return (
      <div className="prediction-results">
        <div className="error-message">
          <h3>❌ Error en la predicción</h3>
          <p>No se pudo obtener la predicción para esta imagen.</p>
        </div>
      </div>
    );
  }

  const getStatusColor = (esTumor: boolean) => (esTumor ? '#e74c3c' : '#27ae60');
  const getStatusIcon = (esTumor: boolean) => (esTumor ? '⚠️' : '✅');
  const getStatusText = (esTumor: boolean) => (esTumor ? 'Tumor Detectado' : 'Sin Tumor');

  const getProcessingTime = () => {
    if (prediction.processing_started && prediction.processing_completed) {
      const start = new Date(prediction.processing_started).getTime();
      const end = new Date(prediction.processing_completed).getTime();
      if (isNaN(start) || isNaN(end) || end < start) return 'N/A';
      return ((end - start) / 1000).toFixed(2) + 's';
    }
    return 'N/A';
  };

  const { clase_predicha, confianza, probabilidades } = prediction.prediction;
  // SIEMPRE recalcular es_tumor basado en la clase predicha para evitar inconsistencias del backend
  const es_tumor = isTumorLabel(clase_predicha);
  const sortedProbabilities = Object.entries(probabilidades || {}).sort((a, b) => b[1] - a[1]);

  return (
    <div className="prediction-results">
      <div className="prediction-header">
        <h3>Resultados del Análisis</h3>
        <div className="prediction-status" style={{ color: getStatusColor(es_tumor) }}>
          {getStatusIcon(es_tumor)} {getStatusText(es_tumor)}
        </div>
      </div>

      <div className="prediction-details">
        <div>
          <strong>Clase Predicha:</strong>{' '}
          <span style={{ color: getClassColor(clase_predicha) }}>
            {getClassName(clase_predicha)}
          </span>
        </div>
        <div>
          <strong>Confianza:</strong> {(confianza * 100).toFixed(2)}%
        </div>
        <div>
          <strong>Probabilidades:</strong>
          <ul>
            {sortedProbabilities.map(([clase, prob]) => (
              <li key={clase} style={{ color: getClassColor(clase) }}>
                {getClassName(clase)}: {(prob * 100).toFixed(2)}%
              </li>
            ))}
          </ul>
        </div>
        <div className="processing-time">
          <strong>Tiempo de proceso:</strong> {getProcessingTime()}
        </div>
      </div>
      </div>
  );
};

export default PredictionResults;
