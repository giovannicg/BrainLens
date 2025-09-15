import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import './Loading.css';

interface LocationState {
  imageId: string;
  runPath?: string; // opcional: ruta a la que navegar tras completar
}

const LoadingPredict: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [error, setError] = useState<string>('');

  const state = (location.state || {}) as LocationState;

  useEffect(() => {
    const run = async () => {
      try {
        if (!state || !state.imageId) {
          setError('Falta el ID de imagen');
          setTimeout(() => navigate('/images'), 2000);
          return;
        }

        const next = state.runPath || `/prediction/${state.imageId}`;
        navigate(next, { replace: true });
      } catch (e: any) {
        setError(e?.message || 'Error durante la predicción');
        setTimeout(() => navigate(`/prediction/${state.imageId}`), 2500);
      }
    };
    run();
  }, [state, navigate]);

  return (
    <div className="loading-page">
      <div className="brain-spinner">
        <div className="brain"></div>
        <div className="pulse"></div>
      </div>
      <h2>Generando la predicción...</h2>
      <p>Un momento por favor.</p>
      {error && <div className="error-message" style={{ marginTop: 16 }}>{error}</div>}
    </div>
  );
};

export default LoadingPredict;


