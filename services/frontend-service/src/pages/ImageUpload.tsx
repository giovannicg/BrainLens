import React, { useState, useRef } from 'react';
import { apiService, ImageUploadResponse } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import './ImageUpload.css';

interface FileWithCustomName {
  file: File;
  customName: string;
}

const ImageUpload: React.FC = () => {
  const [dragActive, setDragActive] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<FileWithCustomName[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadResults, setUploadResults] = useState<ImageUploadResponse[]>([]);
  const [error, setError] = useState<string>('');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { user } = useAuth();

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

  const handleFiles = (files: FileList) => {
    const newFiles = Array.from(files).filter(file => 
      file.type.startsWith('image/')
    ).map(file => ({
      file,
      customName: file.name.replace(/\.[^/.]+$/, '') // Remover extensión para el nombre personalizado
    }));
    setUploadedFiles(prev => [...prev, ...newFiles]);
    setError('');
  };

  const removeFile = (index: number) => {
    setUploadedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const updateCustomName = (index: number, customName: string) => {
    setUploadedFiles(prev => prev.map((item, i) => 
      i === index ? { ...item, customName } : item
    ));
  };

  const handleUpload = async () => {
    if (uploadedFiles.length === 0) return;
    if (!user) {
      setError('Debes estar autenticado para subir imágenes');
      return;
    }

    setUploading(true);
    setError('');
    const results: ImageUploadResponse[] = [];
    
    try {
      for (const fileWithName of uploadedFiles) {
        try {
          const result = await apiService.uploadImage(fileWithName.file, user.id, fileWithName.customName);
          results.push(result);
        } catch (error) {
          console.error('Error uploading file:', fileWithName.file.name, error);
          setError(`Error al subir ${fileWithName.file.name}: ${error instanceof Error ? error.message : 'Error desconocido'}`);
        }
      }
      
      setUploadResults(results);
      setUploadedFiles([]);
      
      if (results.length > 0) {
        alert(`${results.length} imagen(es) subida(s) exitosamente`);
      }
    } catch (error) {
      console.error('Upload failed:', error);
      setError('Error al subir las imágenes');
    } finally {
      setUploading(false);
    }
  };

  const openFileDialog = () => {
    fileInputRef.current?.click();
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
                <div key={index} className="file-item">
                  <div className="file-info">
                    <div className="file-header">
                      <span className="file-name">{fileWithName.file.name}</span>
                      <span className="file-size">
                        {(fileWithName.file.size / 1024 / 1024).toFixed(2)} MB
                      </span>
                    </div>
                    <div className="custom-name-input">
                      <label htmlFor={`custom-name-${index}`}>Nombre personalizado:</label>
                      <input
                        type="text"
                        id={`custom-name-${index}`}
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

        {uploadResults.length > 0 && (
          <div className="upload-results">
            <h3>Resultados de la subida</h3>
            <div className="results-list">
              {uploadResults.map((result, index) => (
                <div key={index} className="result-item">
                  <div className="result-header">
                    <span className="result-success">✅ {result.image.original_filename}</span>
                    <span className="result-size">
                      {(result.image.file_size / 1024 / 1024).toFixed(2)} MB
                    </span>
                  </div>
                  <div className="result-status">
                    <span className="status-label">Estado:</span>
                    <span className={`status-${result.processing_status}`}>
                      {result.processing_status === 'pending' && '⏳ En cola para procesamiento'}
                      {result.processing_status === 'processing' && '🔄 Procesando...'}
                      {result.processing_status === 'completed' && '✅ Procesamiento completado'}
                      {result.processing_status === 'failed' && '❌ Error en procesamiento'}
                    </span>
                  </div>
                  <div className="result-message">
                    {result.message}
                  </div>
                </div>
              ))}
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
        </ul>
      </div>
    </div>
  );
};

export default ImageUpload; 