import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiService, ImageUploadResponse } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import './ImageUpload.css';

/**
 * Interfaces que definen la estructura de datos para los archivos y el progreso de subida
 */
interface FileWithCustomName {
  file: File;
  customName: string;
  id: string; // Identificador único para cada archivo
}

interface UploadProgress {
  [key: string]: {
    status: 'pending' | 'uploading' | 'completed' | 'error';
    progress: number;
    result?: ImageUploadResponse;
    error?: string;
  };
}
const isValidUploadResponse = (x: any): x is ImageUploadResponse =>
  !!x && !!x.image && typeof x.image.id === 'string';

const ImageUpload: React.FC = () => {
  const [dragActive, setDragActive] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<FileWithCustomName[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<UploadProgress>({});
  const [uploadResults, setUploadResults] = useState<ImageUploadResponse[]>([]);
  const [error, setError] = useState<string>('');
  const errorTimeoutRef = useRef<any>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { user } = useAuth();
  const navigate = useNavigate();

  // Persistir estado en localStorage
  /**
 * Efectos que manejan la persistencia del estado en localStorage
 */
  useEffect(() => {
    // Carga el estado guardado al montar el componente
    const savedFiles = localStorage.getItem('uploadedFiles');
    const savedProgress = localStorage.getItem('uploadProgress');
    const savedResults = localStorage.getItem('uploadResults');
    
    if (savedFiles) {
      try {
        const parsedFiles = JSON.parse(savedFiles);
        console.log('Archivos guardados encontrados:', parsedFiles);
      } catch (e) {
        console.error('Error al cargar archivos guardados:', e);
      }
    }
    
    if (savedProgress) {
      try {
        setUploadProgress(JSON.parse(savedProgress));
      } catch (e) {
        console.error('Error al cargar progreso guardado:', e);
      }
    }
    
    if (savedResults) {
      try {
        const parsed = JSON.parse(savedResults);
        // Sanear: mantener solo respuestas válidas
        const filtered = Array.isArray(parsed) ? parsed.filter(isValidUploadResponse) : [];
        setUploadResults(filtered);
      } catch (e) {
        console.error('Error al cargar resultados guardados:', e);
      }
    }
  }, []);

  // Guardar estado en localStorage cuando cambie
  useEffect(() => {
    localStorage.setItem('uploadProgress', JSON.stringify(uploadProgress));
  }, [uploadProgress]);

  useEffect(() => {
    localStorage.setItem('uploadResults', JSON.stringify(uploadResults));
  }, [uploadResults]);
/**
 * Manejadores de eventos para drag & drop
 */
  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFiles(e.dataTransfer.files);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      handleFiles(e.target.files);
    }
  };
/**
 * Funciones de utilidad para manejar archivos
 */
  const handleFiles = (files: FileList) => {
    const newFiles = Array.from(files).filter(file => 
      file.type.startsWith('image/')
    ).map(file => ({
      file,
      customName: file.name.replace(/\.[^/.]+$/, ''), // Remover extensión para el nombre personalizado
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}` // ID único
    }));
    setUploadedFiles((prev: FileWithCustomName[]) => [...prev, ...newFiles]);
    setError('');
  };

  const removeFile = (index: number) => {
    setUploadedFiles((prev: FileWithCustomName[]) => prev.filter((_: FileWithCustomName, i: number) => i !== index));
  };

  const updateCustomName = (index: number, customName: string) => {
    setUploadedFiles((prev: FileWithCustomName[]) => prev.map((item: FileWithCustomName, i: number) => 
      i === index ? { ...item, customName } : item
    ));
  };
/*
 * Función principal de subida
 */
  const handleUpload = async () => {
    if (uploadedFiles.length === 0) return;
    if (!user) {
      setError('Debes estar autenticado para subir imágenes');
      // Limpiar error automáticamente después de 6 segundos
      if (errorTimeoutRef.current) {
        window.clearTimeout(errorTimeoutRef.current);
      }
      errorTimeoutRef.current = window.setTimeout(() => {
        setError('');
      }, 6000);
      return;
    }

    setUploading(true);
    setError('');
    if (errorTimeoutRef.current) {
      window.clearTimeout(errorTimeoutRef.current);
    }
    const results: ImageUploadResponse[] = [];

    try {
      for (const fileWithName of uploadedFiles) {
        // Inicializar progreso para este archivo
        setUploadProgress((prev: UploadProgress) => ({
          ...prev,
          [fileWithName.id]: {
            status: 'uploading',
            progress: 0
          }
        }));

        try {
          // Navegar a página de carga y dejar que allí se ejecute la subida y redirección
          navigate('/loading/upload', {
            state: {
              file: fileWithName.file,
              userId: user.id,
              customName: fileWithName.customName,
            }
          });
          return; // salir tras navegar para un mejor UX
        } catch (error) {
          console.error('Error uploading file:', fileWithName.file.name, error);
          const errorMessage = error instanceof Error ? error.message : 'Error desconocido';
          
          // Actualizar progreso con error
          setUploadProgress((prev: UploadProgress) => ({
            ...prev,
            [fileWithName.id]: {
              status: 'error',
              progress: 0,
              error: errorMessage
            }
          }));
          
          console.log('Setting error message:', `Error al subir ${fileWithName.file.name}: ${errorMessage}`);
          setError(`Error al subir ${fileWithName.file.name}: ${errorMessage}`);
          
          // Limpiar error automáticamente después de 10 segundos (aumentar tiempo)
          if (errorTimeoutRef.current) {
            window.clearTimeout(errorTimeoutRef.current);
          }
          errorTimeoutRef.current = window.setTimeout(() => {
            console.log('Clearing error message after timeout');
            setError('');
          }, 10000); // Aumentar a 10 segundos
        }
      }
      
      setUploadResults((prev: ImageUploadResponse[]) => [...prev, ...results]);
      
      // Solo limpiar archivos y progreso si hay resultados exitosos
      if (results.length > 0) {
        setUploadedFiles([]);
        setUploadProgress({});
      }
      if (results.length > 0) {
        // Mostrar notificación más amigable
        const successCount = results.length;
        const totalCount = uploadedFiles.length;
        const message = `${successCount} de ${totalCount} imagen(es) con validación completada`;
        
        const notification = document.createElement('div');
        notification.className = 'upload-notification success';
        notification.textContent = message;
        document.body.appendChild(notification);
        
        setTimeout(() => {
          document.body.removeChild(notification);
        }, 5000);
      }
    } catch (error) {
      console.error('Upload failed:', error);
      setError('Error al subir las imágenes');
      // Limpiar error automáticamente después de 6 segundos
      if (errorTimeoutRef.current) {
        window.clearTimeout(errorTimeoutRef.current);
      }
      errorTimeoutRef.current = window.setTimeout(() => {
        setError('');
      }, 6000);
    } finally {
      setUploading(false);
      setUploadedFiles([]);
      setUploadProgress({});
    }
  };

  const openFileDialog = () => {
    fileInputRef.current?.click();
  };

  const clearResults = () => {
    setUploadResults([]);
    setUploadProgress({});
    localStorage.removeItem('uploadResults');
    localStorage.removeItem('uploadProgress');
    setError('');
  };

  return (
    <div className="image-upload">
      <div className="upload-header">
        <h1>Subir Imágenes</h1>
        <p>Sube imágenes médicas para análisis y anotación</p>
      </div>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      <div className="upload-container">
        <div 
          className={`upload-area ${dragActive ? 'drag-active' : ''}`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={openFileDialog}
        >
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept="image/*"
            onChange={handleChange}
            className="file-input"
          />
          
          <div className="upload-content">
            <div className="upload-icon">📤</div>
            <h3>Arrastra y suelta imágenes aquí</h3>
            <p>o haz clic para seleccionar archivos</p>
            <p className="upload-hint">
              Formatos soportados: JPG, PNG, DICOM
            </p>
          </div>
        </div>

        {uploadedFiles.length > 0 && (
          <div className="uploaded-files">
            <h3>Archivos seleccionados ({uploadedFiles.length})</h3>
            <div className="files-list">
              {uploadedFiles.map((fileWithName, index) => (
                <div key={fileWithName.id} className="file-item">
                  <div className="file-info">
                    <div className="file-header">
                      <span className="file-name">{fileWithName.file.name}</span>
                      <span className="file-size">
                        {(fileWithName.file.size / 1024 / 1024).toFixed(2)} MB
                      </span>
                    </div>
                    <div className="custom-name-input">
                      <label htmlFor={`custom-name-${fileWithName.id}`}>Nombre personalizado:</label>
                      <input
                        type="text"
                        id={`custom-name-${fileWithName.id}`}
                        value={fileWithName.customName}
                        onChange={(e) => updateCustomName(index, e.target.value)}
                        placeholder="Ingresa un nombre para la imagen"
                        className="name-input"
                      />
                    </div>
                  </div>
                  <button
                    onClick={() => removeFile(index)}
                    className="remove-file"
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
            
            <button
              onClick={handleUpload}
              disabled={uploading}
              className="upload-button"
            >
              {uploading ? 'Subiendo...' : 'Subir Imágenes'}
            </button>
          </div>
        )}

        {/* Mostrar progreso de subida */}
        {Object.keys(uploadProgress).length > 0 && (
          <div className="upload-progress">
            <h3>Progreso de subida</h3>
            <div className="progress-list">
              {Object.entries(uploadProgress).map(([fileId, progress]) => (
                <div key={fileId} className={`progress-item ${progress.status}`}>
                  <div className="progress-header">
                    <span className="progress-status">
                      {progress.status === 'uploading' && '⏳ Subiendo...'}
                      {progress.status === 'completed' && '✅ Completado'}
                      {progress.status === 'error' && '❌ Error'}
                    </span>
                    <span className="progress-percentage">{progress.progress}%</span>
                  </div>
                  {progress.status === 'uploading' && (
                    <div className="progress-bar">
                      <div 
                        className="progress-fill" 
                        style={{ width: `${progress.progress}%` }}
                      ></div>
                    </div>
                  )}
                  {progress.error && (
                    <div className="progress-error">{progress.error}</div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

       {uploadResults.length > 0 && (
          <div className="upload-results">
            <div className="results-header">
              <h3>Resultados de la subida</h3>
              <button onClick={clearResults} className="clear-results">
                Limpiar resultados
              </button>
            </div>
            <div className="results-list">
              {uploadResults
                .filter((r): r is ImageUploadResponse => {
                  if (!r) return false;
                  const img = (r as any).image;
                  return img && typeof img === 'object' && img !== null;
                })
                .map((result, index) => {
                  const img = (result as any).image;
                  if (!img || typeof img !== 'object') {
                    return null; // Skip invalid entries
                  }
                  const fileName = (typeof img.original_filename === 'string' && img.original_filename.trim()) ? img.original_filename : '(sin nombre)';
                  const sizeMB = typeof img.file_size === 'number' ? (img.file_size / 1024 / 1024).toFixed(2) : '0.00';
                  const processing = (result as any).processing_status || img.processing_status || 'pending';
                  const imageId = img.id ? img.id : undefined;

                  return (
                    <div key={index} className="result-item">
                      <div className="result-header">
                        <span className="result-success">✅ {fileName}</span>
                        <span className="result-size">{sizeMB} MB</span>
                      </div>

                      <div className="result-status">
                        <span className="status-label">Estado:</span>
                        <span className={`status-${processing}`}>
                          {processing === 'pending' && '⏳ En cola para procesamiento'}
                          {processing === 'processing' && '🔄 Procesando...'}
                          {processing === 'completed' && '✅ Procesamiento completado'}
                          {processing === 'failed' && '❌ Error en procesamiento'}
                        </span>
                      </div>

                      {result.message && <div className="result-message">{result.message}</div>}

                      <div style={{ marginTop: 8 }}>
                        <button
                          onClick={() => imageId && navigate(`/chat/${imageId}`)}
                          className="action-button"
                          disabled={!imageId}
                          title={imageId ? 'Abrir chat' : 'No hay ID de imagen'}
                        >
                          💬 Ir al chat de la imagen
                        </button>
                      </div>
                    </div>
                  );
                })
                .filter(Boolean)}
            </div>
            <div className="processing-info">
              <h4>ℹ️ Información sobre el procesamiento</h4>
              <p>Las imágenes se procesan automáticamente en background para detectar tumores cerebrales. Puedes ver el progreso en la página "Mis Imágenes".</p>
            </div>
          </div>
        )}
      </div>

      <div className="upload-info">
        <h3>Información importante</h3>
        <ul>
          <li>Las imágenes deben ser de alta calidad para un mejor análisis</li>
          <li>Formatos soportados: JPG, PNG, DICOM</li>
          <li>Tamaño máximo por archivo: 50MB</li>
          <li>Se procesarán automáticamente después de la subida</li>
          <li>El progreso se guarda automáticamente - puedes cambiar de pestaña sin perder información</li>
        </ul>
      </div>
    </div>
  );
};

export default ImageUpload;