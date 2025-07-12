import React, { useState } from 'react';
import './Annotations.css';

interface Annotation {
  id: string;
  imageName: string;
  type: string;
  description: string;
  status: 'pending' | 'completed' | 'review';
  createdAt: string;
  updatedAt: string;
}

const Annotations: React.FC = () => {
  const [selectedFilter, setSelectedFilter] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState('');

  // Datos de ejemplo
  const annotations: Annotation[] = [
    {
      id: '1',
      imageName: 'brain_scan_001.jpg',
      type: 'Tumor Detection',
      description: 'Anomalía detectada en lóbulo frontal derecho',
      status: 'completed',
      createdAt: '2024-01-15',
      updatedAt: '2024-01-16'
    },
    {
      id: '2',
      imageName: 'brain_scan_002.jpg',
      type: 'Vessel Analysis',
      description: 'Análisis de vasos sanguíneos cerebrales',
      status: 'pending',
      createdAt: '2024-01-14',
      updatedAt: '2024-01-14'
    },
    {
      id: '3',
      imageName: 'brain_scan_003.jpg',
      type: 'Tissue Segmentation',
      description: 'Segmentación de tejidos cerebrales',
      status: 'review',
      createdAt: '2024-01-13',
      updatedAt: '2024-01-15'
    }
  ];

  const filteredAnnotations = annotations.filter(annotation => {
    const matchesFilter = selectedFilter === 'all' || annotation.status === selectedFilter;
    const matchesSearch = annotation.imageName.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         annotation.type.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         annotation.description.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesFilter && matchesSearch;
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
        {filteredAnnotations.length === 0 ? (
          <div className="no-annotations">
            <div className="no-annotations-icon">📝</div>
            <h3>No se encontraron anotaciones</h3>
            <p>Intenta ajustar los filtros o crear una nueva anotación</p>
          </div>
        ) : (
          filteredAnnotations.map(annotation => (
            <div key={annotation.id} className="annotation-card">
              <div className="annotation-header">
                <div className="annotation-info">
                  <h3 className="annotation-title">{annotation.type}</h3>
                  <p className="annotation-image">{annotation.imageName}</p>
                </div>
                <div 
                  className="annotation-status"
                  style={{ backgroundColor: getStatusColor(annotation.status) }}
                >
                  {getStatusText(annotation.status)}
                </div>
              </div>
              
              <div className="annotation-content">
                <p className="annotation-description">{annotation.description}</p>
              </div>
              
              <div className="annotation-footer">
                <div className="annotation-dates">
                  <span>Creado: {annotation.createdAt}</span>
                  <span>Actualizado: {annotation.updatedAt}</span>
                </div>
                <div className="annotation-actions">
                  <button className="action-btn view-btn">Ver</button>
                  <button className="action-btn edit-btn">Editar</button>
                  <button className="action-btn delete-btn">Eliminar</button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      <div className="annotations-summary">
        <div className="summary-card">
          <h3>Resumen</h3>
          <div className="summary-stats">
            <div className="summary-stat">
              <span className="stat-number">{annotations.length}</span>
              <span className="stat-label">Total</span>
            </div>
            <div className="summary-stat">
              <span className="stat-number">
                {annotations.filter(a => a.status === 'completed').length}
              </span>
              <span className="stat-label">Completadas</span>
            </div>
            <div className="summary-stat">
              <span className="stat-number">
                {annotations.filter(a => a.status === 'pending').length}
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