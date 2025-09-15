import React from 'react';
import { Link } from 'react-router-dom';
import './Home.css';

const Home: React.FC = () => {
  return (
    <div className="home">
      <section className="hero">
        <div className="hero-content">
          <h1 className="hero-title">
            BrainLens
          </h1>
          <p className="hero-subtitle">
            Plataforma avanzada para análisis y anotación de imágenes médicas
          </p>
          <p className="hero-description">
            Utiliza inteligencia artificial para analizar imágenes cerebrales y crear anotaciones precisas
            que ayudan a los profesionales médicos en el diagnóstico y tratamiento.
          </p>
          <div className="hero-buttons">
            <Link to="/upload" className="btn btn-primary">
              Comenzar Análisis
            </Link>
            <Link to="/register" className="btn btn-secondary">
              Registrarse
            </Link>
          </div>
        </div>
      </section>

      <section className="features">
        <div className="container">
          <h2 className="section-title">Características Principales</h2>
          <div className="features-grid">
            <div className="feature-card">
              <div className="feature-icon">🔬</div>
              <h3>Análisis Avanzado</h3>
              <p>Algoritmos de IA para detectar anomalías y patrones en imágenes cerebrales</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">📝</div>
              <h3>Anotaciones Precisas</h3>
              <p>Crear y gestionar anotaciones detalladas con herramientas intuitivas</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">📊</div>
              <h3>Dashboard Interactivo</h3>
              <p>Visualiza estadísticas y resultados en tiempo real</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">🔒</div>
              <h3>Seguridad Garantizada</h3>
              <p>Protección de datos médicos con estándares de seguridad avanzados</p>
            </div>
          </div>
        </div>
      </section>

      <section className="cta">
        <div className="container">
          <h2>¿Listo para comenzar?</h2>
          <p>Únete a BrainLens y revoluciona tu análisis de imágenes médicas</p>
          <Link to="/register" className="btn btn-primary">
            Registrarse Gratis
          </Link>
        </div>
      </section>
    </div>
  );
};

export default Home; 