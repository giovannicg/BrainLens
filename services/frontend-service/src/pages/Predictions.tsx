import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiService, ImageResponse, ProcessingStatusResponse } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import './Predictions.css';

const Predictions: React.FC = () => {
  const [images, setImages] = useState<ImageResponse[]>([]);
  const [predictions, setPredictions] = useState<Record<string, ProcessingStatusResponse>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');
  const { user } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (user) {
      loadImages();
    }
  }, [user]);

  const loadImages = async () => {
    if (!user) return;
    
    try {
      setLoading(true);
      const response = await apiService.getImages(user.id);
      const completedImages = response.images.filter(img => img.processing_status === 'completed');
      setImages(completedImages);
      
      // Cargar predicciones para cada imagen completada
      const predictionsData: Record<string, ProcessingStatusResponse> = {};
      for (const image of completedImages) {
        try {
          let prediction = await apiService.getProcessingStatus(image.id);
          // Fallback: si no viene predicción pero la imagen la trae embebida, úsala
          if ((!prediction || !prediction.prediction) && (image as any).prediction) {
            const p: any = (image as any).prediction;
            prediction = {
              image_id: image.id,
              status: 'completed',
              prediction: {
                es_tumor: Boolean(p.es_tumor ?? /tumor|sí|si|true|1/i.test(String(p.clase_predicha ?? ''))),
                clase_predicha: String(p.clase_predicha ?? ''),
                confianza: Number(p.confianza ?? p.mean_score ?? 0),
                probabilidades: p.probabilidades ?? {},
                recomendacion: p.recomendacion ?? ''
              }
            } as ProcessingStatusResponse;
          }
          // Segundo fallback: pedir al proxy Colab directamente y mostrar resultado
          if (!prediction || !prediction.prediction) {
            try {
              prediction = await apiService.predictImageViaColab(image.id);
            } catch (e) {
              console.error('predict via colab failed', e);
            }
          }
          predictionsData[image.id] = prediction;
        } catch (err) {
          console.error(`Error loading prediction for image ${image.id}:`, err);
        }
      }
      setPredictions(predictionsData);
      setError('');
    } catch (error) {
      console.error('Error loading images:', error);
      setError('Error al cargar las imágenes');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('es-ES', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
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

  if (error) {
    return (
      <div className="predictions-container">
        <div className="error-message">
          {error}
        </div>
      </div>
    );
  }

  return (
    <div className="predictions-container">
      <div className="predictions-header">
        <h1>🧠 Predicciones de Tumores</h1>
        <p>Resultados de análisis de todas tus imágenes procesadas</p>
      </div>

      {loading ? (
        <div className="loading">
          <div className="loading-spinner"></div>
          <p>Cargando predicciones...</p>
        </div>
      ) : images.length === 0 ? (
        <div className="no-predictions">
          <div className="no-predictions-icon">🧠</div>
          <h3>No hay predicciones disponibles</h3>
          <p>Sube una imagen y espera a que se procese para ver los resultados</p>
          <button onClick={() => navigate('/upload')} className="upload-button">
            📤 Subir Nueva Imagen
          </button>
        </div>
      ) : (
        <div className="predictions-grid">
          {images.map((image) => {
            const prediction = predictions[image.id];
            return (
              <div key={image.id} className="prediction-card">
                <div className="prediction-image">
                  <img
                    src={apiService.getImageDownloadUrl(image.id)}
                    alt={image.original_filename}
                    onError={(e) => {
                      const target = e.target as HTMLImageElement;
                      target.style.display = 'none';
                      const placeholder = target.nextElementSibling as HTMLElement;
                      if (placeholder) {
                        placeholder.style.display = 'flex';
                      }
                    }}
                  />
                  <div className="image-placeholder" style={{ display: 'none' }}>
                    <span>📷</span>
                    <p>Vista previa no disponible</p>
                  </div>
                </div>
                
                <div className="prediction-info">
                  <h4>{image.original_filename}</h4>
                  
                  {prediction && prediction.status === 'completed' && prediction.prediction ? (
                    <div className="prediction-results">
                      <div className="prediction-status">
                        <span className={`status-badge ${prediction.prediction.es_tumor ? 'tumor-detected' : 'no-tumor'}`}>
                          {prediction.prediction.es_tumor ? '⚠️ Tumor Detectado' : '✅ Sin Tumor'}
                        </span>
                      </div>
                      <div className="prediction-details">
                        <div className="prediction-item">
                          <strong>Confianza:</strong>
                          <span className="prediction-value">{typeof prediction.prediction.confianza === 'number' ? prediction.prediction.confianza.toFixed(3) : 'N/A'}</span>
                        </div>
                        <div className="prediction-item">
                          <strong>Clase predicha:</strong>
                          <span className="prediction-value">{prediction.prediction.clase_predicha}</span>
                        </div>
                        <div className="prediction-item">
                          <strong>Tiempo de procesamiento:</strong>
                          <span className="prediction-value">{prediction.processing_completed ? formatDate(prediction.processing_completed) : 'N/A'}</span>
                        </div>
                        <div className="prediction-item">
                          <strong>Procesado:</strong>
                          <span className="prediction-value">{formatDate(prediction.processing_completed || '')}</span>
                        </div>
                        {prediction.prediction.recomendacion && prediction.prediction.recomendacion.trim() && (
                          <div className="prediction-item">
                            <strong>Recomendación:</strong>
                            <span className="prediction-value">{prediction.prediction.recomendacion}</span>
                          </div>
                        )}
                      </div>
                      <div className="prediction-actions">
                        <button 
                          onClick={() => {
                            navigate(`/prediction/${image.id}`);
                          }}
                          className="view-details-button"
                          style={{ 
                            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                            color: 'white',
                            border: 'none',
                            padding: '0.75rem 1.5rem',
                            borderRadius: '8px',
                            fontSize: '0.9rem',
                            fontWeight: '500',
                            cursor: 'pointer',
                            width: '100%',
                            marginTop: '1rem'
                          }}
                        >
                          📊 Ver Detalles Completos
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div className="no-prediction-data">
                      <p>{'No se pudieron cargar los datos de predicción'}</p>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default Predictions;
