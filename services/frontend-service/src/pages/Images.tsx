import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiService, ImageResponse } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import { useProcessingStatus } from '../hooks/useProcessingStatus';
import PredictionResults from '../components/PredictionResults';
import './Images.css';

const Images: React.FC = () => {
  const [images, setImages] = useState<ImageResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');
  const [selectedImageId, setSelectedImageId] = useState<string | null>(null);
  const { user } = useAuth();
  const navigate = useNavigate();

  // Hook para el estado de procesamiento de la imagen seleccionada
  const { status: processingStatus } = useProcessingStatus({
    imageId: selectedImageId || '',
    enabled: !!selectedImageId && (selectedImageId === 'pending' || selectedImageId === 'processing'),
    interval: 3000
  });

  useEffect(() => {
    if (user) {
      loadImages();
    }
  }, [user]);

  // Actualizar imagen cuando cambie el estado de procesamiento
  useEffect(() => {
    if (processingStatus && selectedImageId) {
      setImages(prev => prev.map(img => 
        img.id === selectedImageId 
          ? { ...img, processing_status: processingStatus.status }
          : img
      ));
    }
  }, [processingStatus, selectedImageId]);

  const loadImages = async () => {
    if (!user) return;
    
    try {
      setLoading(true);
      const response = await apiService.getImages(user.id);
      setImages(response.images);
      setError('');
    } catch (error) {
      console.error('Error loading images:', error);
      setError('Error al cargar las imágenes');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteImage = async (imageId: string) => {
    if (!window.confirm('¿Estás seguro de que quieres eliminar esta imagen?')) {
      return;
    }

    try {
      await apiService.deleteImage(imageId);
      setImages(prev => prev.filter(img => img.id !== imageId));
      alert('Imagen eliminada exitosamente');
    } catch (error) {
      console.error('Error deleting image:', error);
      alert('Error al eliminar la imagen');
    }
  };

  const handleDownloadImage = (imageId: string, filename: string) => {
    const downloadUrl = apiService.getImageDownloadUrl(imageId);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleViewPrediction = (imageId: string) => {
    setSelectedImageId(selectedImageId === imageId ? null : imageId);
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
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
      <div className="images-container">
        <div className="error-message">
          {error}
        </div>
      </div>
    );
  }

  return (
    <div className="images-container">
      <div className="images-header">
        <h1>Mis Imágenes</h1>
        <button onClick={() => navigate('/upload')} className="upload-button">
          📤 Subir Nueva Imagen
        </button>
      </div>

      {loading ? (
        <div className="loading">
          <div className="loading-spinner"></div>
          <p>Cargando imágenes...</p>
        </div>
      ) : images.length === 0 ? (
        <div className="no-images">
          <div className="no-images-icon">📷</div>
          <h3>No tienes imágenes subidas</h3>
          <p>Sube tu primera imagen para comenzar</p>
        </div>
      ) : (
        <div className="images-grid">
          {images.map((image) => (
            <div key={image.id} className="image-card">
              <div className="image-preview">
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
              
              <div className="image-info">
                <h4>{image.original_filename}</h4>
                <div className="image-details">
                  <span className="detail-item">
                    <strong>Tamaño:</strong> {formatFileSize(image.file_size)}
                  </span>
                  <span className="detail-item">
                    <strong>Tipo:</strong> {image.mime_type}
                  </span>
                  {image.width && image.height && (
                    <span className="detail-item">
                      <strong>Dimensiones:</strong> {image.width} x {image.height}
                    </span>
                  )}
                  <span className="detail-item">
                    <strong>Estado:</strong> 
                    <span 
                      className={`status-${image.processing_status}`}
                      style={{ color: getStatusColor(image.processing_status) }}
                    >
                      {getStatusText(image.processing_status)}
                    </span>
                  </span>
                  <span className="detail-item">
                    <strong>Subida:</strong> {formatDate(image.upload_date)}
                  </span>
                </div>
              </div>
              
              <div className="image-actions">
                <button
                  onClick={() => navigate(`/annotate/${image.id}`)}
                  className="action-button annotate"
                >
                  ✏️ Anotar
                </button>
                <button
                  onClick={() => handleDownloadImage(image.id, image.original_filename)}
                  className="action-button download"
                >
                  📥 Descargar
                </button>
                <button
                  onClick={() => handleDeleteImage(image.id)}
                  className="action-button delete"
                >
                  🗑️ Eliminar
                </button>
              </div>

              {/* Mostrar resultados de predicción si está completado */}
              {image.processing_status === 'completed' && processingStatus?.prediction && (
                <div className="prediction-section">
                  <button
                    onClick={() => handleViewPrediction(image.id)}
                    className="prediction-toggle"
                  >
                    {selectedImageId === image.id ? '🔽' : '🔼'} Ver Resultados del Análisis
                  </button>
                  
                  {selectedImageId === image.id && (
                    <PredictionResults prediction={processingStatus.prediction} />
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Images; 