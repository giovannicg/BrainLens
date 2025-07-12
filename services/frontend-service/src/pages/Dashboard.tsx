import React from 'react';
import './Dashboard.css';

const Dashboard: React.FC = () => {
  // Datos de ejemplo - en una aplicación real vendrían de la API
  const stats = {
    totalImages: 156,
    processedImages: 142,
    pendingImages: 14,
    totalAnnotations: 89
  };

  const recentActivity = [
    { id: 1, type: 'upload', message: 'Nueva imagen subida', time: '2 horas atrás' },
    { id: 2, type: 'annotation', message: 'Anotación completada', time: '4 horas atrás' },
    { id: 3, type: 'analysis', message: 'Análisis finalizado', time: '1 día atrás' },
    { id: 4, type: 'upload', message: 'Nueva imagen subida', time: '1 día atrás' }
  ];

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>Dashboard</h1>
        <p>Bienvenido de vuelta. Aquí tienes un resumen de tu actividad.</p>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon">📊</div>
          <div className="stat-content">
            <h3>Total de Imágenes</h3>
            <p className="stat-number">{stats.totalImages}</p>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">✅</div>
          <div className="stat-content">
            <h3>Procesadas</h3>
            <p className="stat-number">{stats.processedImages}</p>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">⏳</div>
          <div className="stat-content">
            <h3>Pendientes</h3>
            <p className="stat-number">{stats.pendingImages}</p>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">📝</div>
          <div className="stat-content">
            <h3>Anotaciones</h3>
            <p className="stat-number">{stats.totalAnnotations}</p>
          </div>
        </div>
      </div>

      <div className="dashboard-content">
        <div className="recent-activity">
          <h2>Actividad Reciente</h2>
          <div className="activity-list">
            {recentActivity.map(activity => (
              <div key={activity.id} className="activity-item">
                <div className="activity-icon">
                  {activity.type === 'upload' && '📤'}
                  {activity.type === 'annotation' && '📝'}
                  {activity.type === 'analysis' && '🔬'}
                </div>
                <div className="activity-content">
                  <p className="activity-message">{activity.message}</p>
                  <span className="activity-time">{activity.time}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="quick-actions">
          <h2>Acciones Rápidas</h2>
          <div className="actions-grid">
            <button className="action-button">
              <span className="action-icon">📤</span>
              <span>Subir Imagen</span>
            </button>
            <button className="action-button">
              <span className="action-icon">📝</span>
              <span>Crear Anotación</span>
            </button>
            <button className="action-button">
              <span className="action-icon">📊</span>
              <span>Ver Reportes</span>
            </button>
            <button className="action-button">
              <span className="action-icon">⚙️</span>
              <span>Configuración</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard; 