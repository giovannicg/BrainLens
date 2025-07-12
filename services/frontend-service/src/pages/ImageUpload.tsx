import React, { useState, useRef } from 'react';
import './ImageUpload.css';

const ImageUpload: React.FC = () => {
  const [dragActive, setDragActive] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

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
    );
    setUploadedFiles(prev => [...prev, ...newFiles]);
  };

  const removeFile = (index: number) => {
    setUploadedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleUpload = async () => {
    if (uploadedFiles.length === 0) return;

    setUploading(true);
    
    // TODO: Implementar llamada a la API
    console.log('Uploading files:', uploadedFiles);
    
    // Simular upload
    setTimeout(() => {
      setUploading(false);
      setUploadedFiles([]);
      alert('Imágenes subidas exitosamente');
    }, 2000);
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
              {uploadedFiles.map((file, index) => (
                <div key={index} className="file-item">
                  <div className="file-info">
                    <span className="file-name">{file.name}</span>
                    <span className="file-size">
                      {(file.size / 1024 / 1024).toFixed(2)} MB
                    </span>
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