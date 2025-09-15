import React, { useState, useRef, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { apiService } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import './ImageAnnotation.css';

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

interface DrawingPath {
  id: string;
  points: { x: number; y: number }[];
  color: string;
  thickness: number;
}

const ImageAnnotation: React.FC = () => {
  const { imageId } = useParams<{ imageId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [image, setImage] = useState<any>(null);
  const [annotations, setAnnotations] = useState<Annotation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');
  const [annotationType, setAnnotationType] = useState<'text' | 'drawing' | 'marker'>('text');
  const [textContent, setTextContent] = useState('');
  const [isDrawing, setIsDrawing] = useState(false);
  const [currentDrawingPath, setCurrentDrawingPath] = useState<{ x: number; y: number }[]>([]);
  const [drawingPaths, setDrawingPaths] = useState<DrawingPath[]>([]);
  const [selectedColor, setSelectedColor] = useState('#ff0000');
  const [selectedThickness, setSelectedThickness] = useState(2);
  const [showSaveDialog, setShowSaveDialog] = useState(false);
  const [annotationTitle, setAnnotationTitle] = useState('');
  const [annotationDescription, setAnnotationDescription] = useState('');
  
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const imageRef = useRef<HTMLImageElement>(null);

  useEffect(() => {
    if (imageId) {
      loadImage();
      loadAnnotations();
    }
  }, [imageId]);

  const loadImage = async () => {
    try {
      const imageData = await apiService.getImage(imageId!);
      setImage(imageData);
    } catch (error) {
      setError('Error al cargar la imagen');
      console.error('Error loading image:', error);
    }
  };

  const loadAnnotations = async () => {
    try {
      const annotationsData = await apiService.getAnnotations(imageId!);
      setAnnotations(annotationsData.annotations);
    } catch (error) {
      console.error('Error loading annotations:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCanvasMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (annotationType === 'drawing') {
      setIsDrawing(true);
      const rect = canvasRef.current!.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      setCurrentDrawingPath([{ x, y }]);
    }
  };

  const handleCanvasMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (isDrawing && annotationType === 'drawing') {
      const rect = canvasRef.current!.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      setCurrentDrawingPath(prev => [...prev, { x, y }]);
    }
  };

  const handleCanvasMouseUp = () => {
    if (isDrawing && annotationType === 'drawing') {
      setIsDrawing(false);
      if (currentDrawingPath.length > 2) {
        const newDrawingPath: DrawingPath = {
          id: Date.now().toString(),
          points: [...currentDrawingPath],
          color: selectedColor,
          thickness: selectedThickness
        };
        setDrawingPaths(prev => [...prev, newDrawingPath]);
        setCurrentDrawingPath([]);
      }
    }
  };

  const saveAllDrawings = async () => {
    if (drawingPaths.length === 0) return;

    try {
      const shapes = drawingPaths.map(path => ({
        type: 'polygon',
        points: path.points,
        properties: {
          color: path.color,
          thickness: path.thickness
        }
      }));

      const annotation = await apiService.createAnnotation({
        image_id: imageId!,
        user_id: user!.id,
        title: annotationTitle || 'Dibujos múltiples',
        description: annotationDescription || 'Anotación con múltiples dibujos',
        category: 'drawing',
        confidence: 1.0,
        status: 'pending',
        shapes: shapes,
        metadata: {
          annotation_type: 'drawing',
          drawings_count: drawingPaths.length,
          total_points: drawingPaths.reduce((sum, path) => sum + path.points.length, 0)
        }
      });

      console.log('Anotación con múltiples dibujos guardada exitosamente:', annotation);
      setAnnotations(prev => [...prev, annotation]);
      setDrawingPaths([]);
      setShowSaveDialog(false);
      setAnnotationTitle('');
      setAnnotationDescription('');
    } catch (error) {
      console.error('Error al guardar anotación con múltiples dibujos:', error);
      setError('Error al guardar la anotación');
    }
  };

  const clearDrawings = () => {
    setDrawingPaths([]);
    setCurrentDrawingPath([]);
  };

  const removeDrawing = (drawingId: string) => {
    setDrawingPaths(prev => prev.filter(path => path.id !== drawingId));
  };

  const handleTextAnnotation = async () => {
    if (!textContent.trim()) return;

    try {
      const annotation = await apiService.createAnnotation({
        image_id: imageId!,
        user_id: user!.id,
        title: 'Anotación de texto',
        description: textContent,
        category: 'text',
        confidence: 1.0,
        status: 'pending',
        shapes: [],
        metadata: {
          annotation_type: 'text',
          content: textContent
        }
      });

      setAnnotations(prev => [...prev, annotation]);
      setTextContent('');
    } catch (error) {
      setError('Error al guardar la anotación');
      console.error('Error saving annotation:', error);
    }
  };

  const handleMarkerAnnotation = async (e: React.MouseEvent<HTMLCanvasElement>) => {
    const rect = canvasRef.current!.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    try {
      const annotation = await apiService.createAnnotation({
        image_id: imageId!,
        user_id: user!.id,
        title: 'Marcador',
        description: 'Punto de referencia marcado',
        category: 'marker',
        confidence: 1.0,
        status: 'pending',
        shapes: [{
          type: 'point',
          points: [{ x, y }],
          properties: {
            color: '#ff0000',
            size: 5
          }
        }],
        metadata: {
          annotation_type: 'marker',
          coordinates: { x, y }
        }
      });

      setAnnotations(prev => [...prev, annotation]);
    } catch (error) {
      setError('Error al guardar la anotación');
      console.error('Error saving annotation:', error);
    }
  };

  const deleteAnnotation = async (annotationId: string) => {
    try {
      await apiService.deleteAnnotation(annotationId);
      setAnnotations(prev => prev.filter(a => a.id !== annotationId));
    } catch (error) {
      setError('Error al eliminar la anotación');
      console.error('Error deleting annotation:', error);
    }
  };

  const renderAnnotations = () => {
    const canvas = canvasRef.current;
    if (!canvas) {
      console.log('Canvas no disponible');
      return;
    }

    const ctx = canvas.getContext('2d');
    if (!ctx) {
      console.log('Contexto 2D no disponible');
      return;
    }

    console.log('Renderizando anotaciones:', annotations.length);

    // Limpiar canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Dibujar imagen
    if (imageRef.current) {
      ctx.drawImage(imageRef.current, 0, 0, canvas.width, canvas.height);
    }

                    // Dibujar anotaciones existentes
        annotations.forEach(annotation => {
          annotation.shapes.forEach(shape => {
            if (shape.type === 'polygon' && shape.points.length > 1) {
              ctx.beginPath();
              ctx.strokeStyle = shape.properties.color || '#ff0000';
              ctx.lineWidth = shape.properties.thickness || 2;
              ctx.moveTo(shape.points[0].x, shape.points[0].y);
              shape.points.forEach((point: { x: number; y: number }) => {
                ctx.lineTo(point.x, point.y);
              });
              ctx.stroke();
            } else if (shape.type === 'point' && shape.points.length > 0) {
              const point = shape.points[0];
              ctx.fillStyle = shape.properties.color || '#ff0000';
              ctx.beginPath();
              ctx.arc(point.x, point.y, shape.properties.size || 5, 0, 2 * Math.PI);
              ctx.fill();
            }
          });
        });

    // Dibujar todos los paths guardados
    drawingPaths.forEach(path => {
      if (path.points.length > 1) {
        ctx.beginPath();
        ctx.strokeStyle = path.color;
        ctx.lineWidth = path.thickness;
        ctx.moveTo(path.points[0].x, path.points[0].y);
        path.points.forEach((point: { x: number; y: number }) => {
          ctx.lineTo(point.x, point.y);
        });
        ctx.stroke();
      }
    });

    // Dibujar path actual si está dibujando
    if (currentDrawingPath.length > 1) {
      ctx.beginPath();
      ctx.strokeStyle = selectedColor;
      ctx.lineWidth = selectedThickness;
      ctx.moveTo(currentDrawingPath[0].x, currentDrawingPath[0].y);
      currentDrawingPath.forEach((point: { x: number; y: number }) => {
        ctx.lineTo(point.x, point.y);
      });
      ctx.stroke();
    }
  };

  useEffect(() => {
    renderAnnotations();
  }, [annotations, drawingPaths, currentDrawingPath, selectedColor, selectedThickness]);

  if (loading) {
    return <div className="loading">Cargando imagen...</div>;
  }

  if (error) {
    return <div className="error">{error}</div>;
  }

  return (
    <div className="image-annotation">
      <div className="annotation-header">
        <h1>Anotar Imagen</h1>
        <button onClick={() => navigate('/images')} className="back-button">
          ← Volver a Mis Imágenes
        </button>
      </div>

      {image && (
        <div className="annotation-container">
          <div className="image-container">
            <canvas
              ref={canvasRef}
              width={800}
              height={600}
              onMouseDown={handleCanvasMouseDown}
              onMouseMove={handleCanvasMouseMove}
              onMouseUp={handleCanvasMouseUp}
              onClick={annotationType === 'marker' ? handleMarkerAnnotation : undefined}
              className="annotation-canvas"
            />
            <img
              ref={imageRef}
              src={apiService.getImageDownloadUrl(imageId!)}
              alt={image.original_filename}
              style={{ display: 'none' }}
              onLoad={() => renderAnnotations()}
            />
          </div>

          <div className="annotation-tools">
            <div className="tool-section">
              <h3>Herramientas de Anotación</h3>
              
              <div className="tool-buttons">
                <button
                  className={`tool-button ${annotationType === 'text' ? 'active' : ''}`}
                  onClick={() => setAnnotationType('text')}
                >
                  📝 Texto
                </button>
                <button
                  className={`tool-button ${annotationType === 'drawing' ? 'active' : ''}`}
                  onClick={() => setAnnotationType('drawing')}
                >
                  ✏️ Dibujo
                </button>
                <button
                  className={`tool-button ${annotationType === 'marker' ? 'active' : ''}`}
                  onClick={() => setAnnotationType('marker')}
                >
                  🎯 Marcador
                </button>
              </div>

              {annotationType === 'text' && (
                <div className="text-input-section">
                  <textarea
                    value={textContent}
                    onChange={(e) => setTextContent(e.target.value)}
                    placeholder="Escribe tu anotación aquí..."
                    className="annotation-textarea"
                  />
                  <button
                    onClick={handleTextAnnotation}
                    disabled={!textContent.trim()}
                    className="save-button"
                  >
                    Guardar Anotación
                  </button>
                </div>
              )}

              {annotationType === 'drawing' && (
                <div className="drawing-controls">
                  <div className="color-picker">
                    <label>Color:</label>
                    <input
                      type="color"
                      value={selectedColor}
                      onChange={(e) => setSelectedColor(e.target.value)}
                      className="color-input"
                    />
                  </div>
                  
                  <div className="thickness-control">
                    <label>Grosor: {selectedThickness}px</label>
                    <input
                      type="range"
                      min="1"
                      max="10"
                      value={selectedThickness}
                      onChange={(e) => setSelectedThickness(parseInt(e.target.value))}
                      className="thickness-slider"
                    />
                  </div>
                  
                  <div className="drawing-actions">
                    <button
                      onClick={() => setShowSaveDialog(true)}
                      disabled={drawingPaths.length === 0}
                      className="save-drawings-button"
                    >
                      💾 Guardar Dibujos ({drawingPaths.length})
                    </button>
                    <button
                      onClick={clearDrawings}
                      disabled={drawingPaths.length === 0}
                      className="clear-drawings-button"
                    >
                      🗑️ Limpiar Dibujos
                    </button>
                  </div>
                  
                  <div className="drawing-instructions">
                    <p>Haz clic y arrastra para dibujar. Puedes hacer múltiples dibujos antes de guardar.</p>
                  </div>
                  
                  {drawingPaths.length > 0 && (
                    <div className="drawings-list">
                      <h4>Dibujos realizados ({drawingPaths.length}):</h4>
                      {drawingPaths.map((path, index) => (
                        <div key={path.id} className="drawing-item">
                          <div 
                            className="color-preview"
                            style={{ backgroundColor: path.color }}
                          />
                          <span>Dibujo {index + 1} ({path.points.length} puntos)</span>
                          <button
                            onClick={() => removeDrawing(path.id)}
                            className="remove-drawing"
                          >
                            ✕
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {annotationType === 'marker' && (
                <div className="marker-instructions">
                  <p>Haz clic en la imagen para colocar un marcador</p>
                </div>
              )}
            </div>

            <div className="annotations-list">
              <h3>Anotaciones ({annotations.length})</h3>
              {annotations.map(annotation => (
                <div key={annotation.id} className="annotation-item">
                  <div className="annotation-content">
                    <span className="annotation-type">
                      {annotation.metadata?.annotation_type === 'text' && '📝'}
                      {annotation.metadata?.annotation_type === 'drawing' && '✏️'}
                      {annotation.metadata?.annotation_type === 'marker' && '🎯'}
                    </span>
                    <span className="annotation-text">
                      {annotation.title} - {new Date(annotation.created_at).toLocaleString()}
                    </span>
                  </div>
                  <button
                    onClick={() => deleteAnnotation(annotation.id)}
                    className="delete-annotation"
                  >
                    🗑️
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Diálogo de guardado */}
      {showSaveDialog && (
        <div className="save-dialog-overlay">
          <div className="save-dialog">
            <h3>Guardar Anotación con Dibujos</h3>
            <div className="dialog-content">
              <div className="input-group">
                <label>Título de la anotación:</label>
                <input
                  type="text"
                  value={annotationTitle}
                  onChange={(e) => setAnnotationTitle(e.target.value)}
                  placeholder="Ej: Marcación de tumores"
                  className="dialog-input"
                />
              </div>
              
              <div className="input-group">
                <label>Descripción:</label>
                <textarea
                  value={annotationDescription}
                  onChange={(e) => setAnnotationDescription(e.target.value)}
                  placeholder="Describe lo que has marcado..."
                  className="dialog-textarea"
                />
              </div>
              
              <div className="dialog-summary">
                <p>Se guardarán {drawingPaths.length} dibujos con un total de {
                  drawingPaths.reduce((sum, path) => sum + path.points.length, 0)
                } puntos.</p>
              </div>
            </div>
            
            <div className="dialog-actions">
              <button
                onClick={saveAllDrawings}
                disabled={!annotationTitle.trim()}
                className="confirm-save-button"
              >
                💾 Guardar Anotación
              </button>
              <button
                onClick={() => setShowSaveDialog(false)}
                className="cancel-button"
              >
                ❌ Cancelar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ImageAnnotation; 