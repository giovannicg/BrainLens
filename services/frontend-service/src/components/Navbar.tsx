import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import './Navbar.css';

const Navbar: React.FC = () => {
  const location = useLocation();
  const { isAuthenticated, user, logout } = useAuth();

  const handleLogout = () => {
    logout();
  };

  return (
    <nav className="navbar">
      <div className="navbar-container">
        <Link to="/" className="navbar-brand">
          BrainLens
        </Link>
        
        <div className="navbar-menu">
          <Link 
            to="/" 
            className={`navbar-link ${location.pathname === '/' ? 'active' : ''}`}
          >
            Inicio
          </Link>
          {isAuthenticated && (
            <>
              <Link 
                to="/upload" 
                className={`navbar-link ${location.pathname === '/upload' ? 'active' : ''}`}
              >
                Subir Imagen
              </Link>
              <Link 
                to="/images" 
                className={`navbar-link ${location.pathname === '/images' ? 'active' : ''}`}
              >
                Mis Imágenes
              </Link>
              <Link 
                to="/predictions" 
                className={`navbar-link ${location.pathname === '/predictions' ? 'active' : ''}`}
              >
                Predicciones
              </Link>
              <Link 
                to="/dashboard" 
                className={`navbar-link ${location.pathname === '/dashboard' ? 'active' : ''}`}
              >
                Dashboard
              </Link>
            </>
          )}
        </div>

        <div className="navbar-auth">
          {isAuthenticated ? (
            <div className="navbar-user">
              <span className="navbar-username">Hola, {user?.username}</span>
              <button onClick={handleLogout} className="navbar-button logout">
                Cerrar Sesión
              </button>
            </div>
          ) : (
            <>
              <Link to="/login" className="navbar-link">
                Iniciar Sesión
              </Link>
              <Link to="/register" className="navbar-button">
                Registrarse
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navbar; 