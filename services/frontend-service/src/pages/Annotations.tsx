import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import './Annotations.css';

interface Annotation {
  id: string;
  image_id: string;
  user_id: string;
  title: string;
  description: string;
  category: string;
  confidence: number;
  status: string;
  shapes: {
    type: string;
    points: { x: number; y: number }[];
    properties: Record<string, any>;
  }[];
  metadata: Record<string, any>;
  created_at: string;
  updated_at: string;
  reviewed_by?: string;
  reviewed_at?: string;
  review_notes?: string;
}

interface ImageWithAnnotations {
  image_id: string;
  image_name: string;
  image_url: string;
  annotations: Annotation[];
  total_annotations: number;
  pending_annotations: number;
  completed_annotations: number;
  last_annotation_date: string;
}

const Annotations: React.FC = () => {
  const [selectedFilter, setSelectedFilter] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [imagesWithAnnotations, setImagesWithAnnotations] = useState<ImageWithAnnotations[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { user } = useAuth();

  // Cargar imágenes y sus anotaciones
  useEffect(() => {
    const loadImagesWithAnnotations = async () => {
      if (!user) return;
      
      try {
        setLoading(true);
        
        // Obtener todas las imágenes del usuario
        const imagesResponse = await apiService.getImages(user.id);
        const images = imagesResponse.images;
        
        // Obtener todas las anotaciones del usuario
        const annotationsResponse = await apiService.getAnnotationsByUser(user.id);
        const allAnnotations = annotationsResponse.annotations;
        
        // Agrupar anotaciones por imagen
        const imagesWithAnnotationsData: ImageWithAnnotations[] = images.map(image => {
          const imageAnnotations = allAnnotations.filter(ann => ann.image_id === image.id);
          
          const pendingCount = imageAnnotations.filter(ann => ann.status === 'pending').length;
          const completedCount = imageAnnotations.filter(ann => ann.status === 'completed').length;
          
          const lastAnnotationDate = imageAnnotations.length > 0 
            ? Math.max(...imageAnnotations.map(ann => new Date(ann.updated_at).getTime()))
            : new Date(image.upload_date).getTime();
          
          return {
            image_id: image.id,
            image_name: image.original_filename,
            image_url: apiService.getImageDownloadUrl(image.id),
            annotations: imageAnnotations,
            total_annotations: imageAnnotations.length,
            pending_annotations: pendingCount,
            completed_annotations: completedCount,
            last_annotation_date: new Date(lastAnnotationDate).toISOString()
          };
        });
        
        setImagesWithAnnotations(imagesWithAnnotationsData);
      } catch (err) {
        console.error('Error loading images with annotations:', err);
        setError('Error al cargar las imágenes y anotaciones');
      } finally {
        setLoading(false);
      }
    };

    loadImagesWithAnnotations();
  }, [user]);

  // Funciones para manejar acciones
  const handleViewImage = (imageWithAnnotations: ImageWithAnnotations) => {
    // Navegar a la página de anotación de la imagen
    window.open(`/annotate/${imageWithAnnotations.image_id}`, '_blank');
  };

  const handleDeleteAnnotation = async (annotation: Annotation) => {
    if (!window.confirm('¿Estás seguro de que quieres eliminar esta anotación?')) {
      return;
    }

    try {
      await apiService.deleteAnnotation(annotation.id);
      // Recargar datos después de eliminar
      const loadImagesWithAnnotations = async () => {
        if (!user) return;
        
        const imagesResponse = await apiService.getImages(user.id);
        const images = imagesResponse.images;
        
        const annotationsResponse = await apiService.getAnnotationsByUser(user.id);
        const allAnnotations = annotationsResponse.annotations;
        
        const imagesWithAnnotationsData: ImageWithAnnotations[] = images.map(image => {
          const imageAnnotations = allAnnotations.filter(ann => ann.image_id === image.id);
          
          const pendingCount = imageAnnotations.filter(ann => ann.status === 'pending').length;
          const completedCount = imageAnnotations.filter(ann => ann.status === 'completed').length;
          
          const lastAnnotationDate = imageAnnotations.length > 0 
            ? Math.max(...imageAnnotations.map(ann => new Date(ann.updated_at).getTime()))
            : new Date(image.upload_date).getTime();
          
          return {
            image_id: image.id,
            image_name: image.original_filename,
            image_url: apiService.getImageDownloadUrl(image.id),
            annotations: imageAnnotations,
            total_annotations: imageAnnotations.length,
            pending_annotations: pendingCount,
            completed_annotations: completedCount,
            last_annotation_date: new Date(lastAnnotationDate).toISOString()
          };
        });
        
        setImagesWithAnnotations(imagesWithAnnotationsData);
      };
      
      loadImagesWithAnnotations();
    } catch (err) {
      console.error('Error deleting annotation:', err);
      alert('Error al eliminar la anotación');
    }
  };

  const filteredImagesWithAnnotations = imagesWithAnnotations.filter(imageWithAnnotations => {
    const hasMatchingAnnotations = imageWithAnnotations.annotations.some(annotation => {
      const matchesFilter = selectedFilter === 'all' || annotation.status === selectedFilter;
      const matchesSearch = annotation.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           annotation.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           annotation.category.toLowerCase().includes(searchTerm.toLowerCase());
      return matchesFilter && matchesSearch;
    });
    
    const matchesImageName = imageWithAnnotations.image_name.toLowerCase().includes(searchTerm.toLowerCase());
    
    return hasMatchingAnnotations || matchesImageName;
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return '#4CAF50';
      case 'pending':
        return '#FF9800';
      case 'review':
        return '#2196F3';
      default:
        return '#666';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'completed':
        return 'Completado';
      case 'pending':
        return 'Pendiente';
      case 'review':
        return 'En Revisión';
      default:
        return status;
    }
  };

  return (
    <div className="annotations">
      <div className="annotations-header">
        <h1>Anotaciones</h1>
        <p>Gestiona y revisa las anotaciones de tus imágenes médicas</p>
      </div>

      <div className="annotations-controls">
        <div className="search-box">
          <input
            type="text"
            placeholder="Buscar anotaciones..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="search-input"
          />
        </div>

        <div className="filter-buttons">
          <button
            className={`filter-btn ${selectedFilter === 'all' ? 'active' : ''}`}
            onClick={() => setSelectedFilter('all')}
          >
            Todas
          </button>
          <button
            className={`filter-btn ${selectedFilter === 'pending' ? 'active' : ''}`}
            onClick={() => setSelectedFilter('pending')}
          >
            Pendientes
          </button>
          <button
            className={`filter-btn ${selectedFilter === 'completed' ? 'active' : ''}`}
            onClick={() => setSelectedFilter('completed')}
          >
            Completadas
          </button>
          <button
            className={`filter-btn ${selectedFilter === 'review' ? 'active' : ''}`}
            onClick={() => setSelectedFilter('review')}
          >
            En Revisión
          </button>
        </div>
      </div>

      <div className="annotations-list">
        {loading ? (
          <div className="loading-annotations">
            <div className="loading-icon">⏳</div>
            <h3>Cargando imágenes y anotaciones...</h3>
          </div>
        ) : error ? (
          <div className="error-annotations">
            <div className="error-icon">❌</div>
            <h3>Error al cargar imágenes y anotaciones</h3>
            <p>{error}</p>
          </div>
        ) : filteredImagesWithAnnotations.length === 0 ? (
          <div className="no-annotations">
            <div className="no-annotations-icon">📝</div>
            <h3>No se encontraron imágenes con anotaciones</h3>
            <p>Intenta ajustar los filtros o subir una nueva imagen</p>
          </div>
        ) : (
          filteredImagesWithAnnotations.map(imageWithAnnotations => (
            <div key={imageWithAnnotations.image_id} className="image-annotation-card">
              <div className="image-annotation-header">
                <div className="image-info">
                  <img 
                    src={imageWithAnnotations.image_url} 
                    alt={imageWithAnnotations.image_name}
                    className="image-thumbnail"
                  />
                  <div className="image-details">
                    <h3 className="image-title">{imageWithAnnotations.image_name}</h3>
                    <div className="annotation-stats">
                      <span className="stat-item">
                        📊 Total: {imageWithAnnotations.total_annotations}
                      </span>
                      <span className="stat-item">
                        ⏳ Pendientes: {imageWithAnnotations.pending_annotations}
                      </span>
                      <span className="stat-item">
                        ✅ Completadas: {imageWithAnnotations.completed_annotations}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="image-actions">
                  <button 
                    className="action-btn view-btn"
                    onClick={() => handleViewImage(imageWithAnnotations)}
                  >
                    Ver Imagen
                  </button>
                </div>
              </div>
              
              {imageWithAnnotations.annotations.length > 0 && (
                <div className="annotations-section">
                  <h4>Anotaciones ({imageWithAnnotations.annotations.length})</h4>
                  <div className="annotations-grid">
                    {imageWithAnnotations.annotations.map(annotation => (
                      <div key={annotation.id} className="annotation-item">
                        <div className="annotation-item-header">
                          <span className="annotation-title">{annotation.title}</span>
                          <div 
                            className="annotation-status-small"
                            style={{ backgroundColor: getStatusColor(annotation.status) }}
                          >
                            {getStatusText(annotation.status)}
                          </div>
                        </div>
                        <p className="annotation-description">{annotation.description}</p>
                        <p className="annotation-category">Categoría: {annotation.category}</p>
                        <div className="annotation-item-footer">
                          <span className="annotation-date">
                            {new Date(annotation.updated_at).toLocaleDateString()}
                          </span>
                          <button 
                            className="delete-btn-small"
                            onClick={() => handleDeleteAnnotation(annotation)}
                          >
                            🗑️
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))
        )}
      </div>

      <div className="annotations-summary">
        <div className="summary-card">
          <h3>Resumen</h3>
          <div className="summary-stats">
            <div className="summary-stat">
              <span className="stat-number">{filteredImagesWithAnnotations.length}</span>
              <span className="stat-label">Imágenes</span>
            </div>
            <div className="summary-stat">
              <span className="stat-number">
                {filteredImagesWithAnnotations.reduce((total, img) => total + img.total_annotations, 0)}
              </span>
              <span className="stat-label">Anotaciones</span>
            </div>
            <div className="summary-stat">
              <span className="stat-number">
                {filteredImagesWithAnnotations.reduce((total, img) => total + img.completed_annotations, 0)}
              </span>
              <span className="stat-label">Completadas</span>
            </div>
            <div className="summary-stat">
              <span className="stat-number">
                {filteredImagesWithAnnotations.reduce((total, img) => total + img.pending_annotations, 0)}
              </span>
              <span className="stat-label">Pendientes</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Annotations; 