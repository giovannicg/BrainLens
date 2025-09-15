import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { apiService, ImageUploadResponse } from '../services/api';
import './Loading.css';

interface LocationState {
  file: File;
  userId: string;
  customName?: string;
}

const LoadingUpload: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [error, setError] = useState<string>('');

  const state = (location.state || {}) as LocationState;

  useEffect(() => {
    const run = async () => {
      try {
        if (!state || !state.file || !state.userId) {
          setError('Datos de subida incompletos');
          setTimeout(() => navigate('/upload'), 2000);
          return;
        }

        const resp: ImageUploadResponse = await apiService.uploadImage(state.file, state.userId, state.customName);
        if (!resp.image) {
          // Error en validación o predicción
          const msg = resp.message || 'Error procesando la imagen';
          const detail = resp.error_detail ? `: ${resp.error_detail}` : '';
          throw new Error(`${msg}${detail}`);
        }
        const imageId = resp.image.id;
        navigate(`/prediction/${imageId}`, { replace: true });
      } catch (e: any) {
        setError(e?.message || 'Error durante la subida');
        setTimeout(() => navigate('/upload'), 2500);
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
      <h2>Validando y guardando tu imagen...</h2>
      <p>Esto puede tardar unos segundos.</p>
      {error && <div className="error-message" style={{ marginTop: 16 }}>{error}</div>}
    </div>
  );
};

export default LoadingUpload;


