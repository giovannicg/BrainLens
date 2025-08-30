import React, { useEffect, useState, useRef } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { apiService, ChatMessageDTO, ChatHistoryResponse, ImageResponse, ImageListResponse } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import './ImageChat.css';

const ImageChat: React.FC = () => {
  const { imageId } = useParams<{ imageId: string }>();
  const { user } = useAuth();
  const navigate = useNavigate();
  
  // Estados para el chat actual
  const [history, setHistory] = useState<ChatMessageDTO[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [image, setImage] = useState<ImageResponse | null>(null);
  const [loadingHistory, setLoadingHistory] = useState<boolean>(true);
  const [error, setError] = useState<string>('');
  
  // Estados para la lista de imágenes
  const [images, setImages] = useState<ImageResponse[]>([]);
  const [loadingImages, setLoadingImages] = useState<boolean>(true);
  const [selectedImageId, setSelectedImageId] = useState<string | null>(imageId || null);
  
  const listRef = useRef<HTMLDivElement>(null);
  const imagesListRef = useRef<HTMLDivElement>(null);
  
  const suggestions = [
    '¿Qué observas en esta imagen?',
    'Describe la región con mayor anomalía.',
    '¿Hay indicios de tumor? ¿Cuál y por qué?',
    'Resume los hallazgos más relevantes.',
  ];

  // Cargar lista de imágenes del usuario
  const loadImages = async () => {
    if (!user) return;
    try {
      setLoadingImages(true);
      const response: ImageListResponse = await apiService.getImages(user.id, 0, 100);
      setImages(response.images);
    } catch (e) {
      console.error('Error cargando imágenes:', e);
    } finally {
      setLoadingImages(false);
    }
  };

  // Cargar historial de chat para una imagen específica
  const loadHistory = async (imgId: string) => {
    if (!imgId || !user) return;
    try {
      setLoadingHistory(true);
      setError('');
      const [data, img]: [ChatHistoryResponse, ImageResponse] = await Promise.all([
        apiService.getImageChatHistory(imgId, user.id, 50),
        apiService.getImage(imgId),
      ]);
      setHistory(data.messages);
      setImage(img);
      setSelectedImageId(imgId);
      scrollToBottom();
    } catch (e) {
      console.error('Error cargando historial/imagen:', e);
      setError('No se pudo cargar el historial o la imagen.');
    } finally {
      setLoadingHistory(false);
    }
  };

  // Cambiar a una imagen diferente
  const selectImage = (imgId: string) => {
    if (imgId === selectedImageId) return;
    setInput(''); // Limpiar input al cambiar imagen
    setSelectedImageId(imgId); // Actualizar inmediatamente el estado
    loadHistory(imgId);
    navigate(`/chat/${imgId}`);
  };

  useEffect(() => {
    loadImages();
  }, [user?.id]);

  useEffect(() => {
    if (imageId && imageId !== selectedImageId) {
      loadHistory(imageId);
    }
  }, [imageId, user?.id]);

  const scrollToBottom = () => {
    requestAnimationFrame(() => listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: 'smooth' }));
  };

  const onSend = async () => {
    if (!input.trim() || !selectedImageId || !user) return;
    const text = input.trim();
    setInput('');
    setLoading(true);
    setError('');
    
    // Optimista: agregar el mensaje del usuario primero
    const now = new Date().toISOString();
    const userMsg: ChatMessageDTO = { 
      image_id: selectedImageId, 
      user_id: user.id, 
      role: 'user', 
      content: text, 
      timestamp: now 
    };
    setHistory((h: ChatMessageDTO[]) => [...h, userMsg]);
    
    try {
      const resp = await apiService.sendImageChatMessage(selectedImageId, user.id, text);
      setHistory((h: ChatMessageDTO[]) => [...h, resp.message]);
      scrollToBottom();
    } catch (e) {
      console.error('Error enviando mensaje:', e);
      setError('No se pudo enviar el mensaje.');
    } finally {
      setLoading(false);
    }
  };

  const onKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSend();
    }
  };

  const formatDate = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleDateString('es-ES', { 
      day: '2-digit', 
      month: '2-digit', 
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="image-chat-page">
      <div className="chat-header">
        <div>
          <h2>Chat sobre imagen</h2>
          {image && (
            <div className="chat-subtitle">
              <span>{image.original_filename}</span>
              {image.width && image.height && (
                <span className="dot">•</span>
              )}
              {image.width && image.height && (
                <span>{image.width}×{image.height}</span>
              )}
            </div>
          )}
        </div>
        <div className="chat-actions">
          <Link to="/images" className="btn-secondary">← Volver</Link>
        </div>
      </div>

      <div className="chat-content">
        {/* Panel lateral con lista de imágenes */}
        <div className="images-sidebar">
          <div className="sidebar-header">
            <h3>Mis Imágenes</h3>
            <span className="image-count">{images.length} imágenes</span>
          </div>
          
          <div className="images-list" ref={imagesListRef}>
            {loadingImages ? (
              <div className="loading-images">Cargando imágenes...</div>
            ) : images.length === 0 ? (
              <div className="no-images">
                <p>No tienes imágenes subidas</p>
                <Link to="/upload" className="btn-primary">Subir imagen</Link>
              </div>
            ) : (
              images.map((img) => {
                const isSelected = img.id === selectedImageId;
                const hasChat = img.processing_status === 'completed';
                
                return (
                  <div
                    key={img.id}
                    className={`image-item ${isSelected ? 'selected' : ''} ${hasChat ? 'has-chat' : ''}`}
                    onClick={() => selectImage(img.id)}
                  >
                    <div className="image-thumbnail">
                      {(() => {
                        const mime = img.mime_type || '';
                        const canPreview = mime.startsWith('image/') && mime !== 'application/dicom';
                        return canPreview ? (
                          <img
                            src={apiService.getImageDownloadUrl(img.id)}
                            alt={img.original_filename}
                            onError={(e) => {
                              const target = e.currentTarget as HTMLImageElement;
                              target.style.display = 'none';
                              const placeholder = target.nextElementSibling as HTMLElement | null;
                              if (placeholder) placeholder.style.display = 'block';
                            }}
                          />
                        ) : (
                          <div className="image-placeholder-small">📄</div>
                        );
                      })()}
                      <div className="image-placeholder-small" style={{ display: 'none' }}>📄</div>
                    </div>
                    
                    <div className="image-info">
                      <div className="image-name">{img.original_filename}</div>
                      <div className="image-meta">
                        {img.width && img.height && (
                          <span className="image-dimensions">{img.width}×{img.height}</span>
                        )}
                        {img.upload_date && (
                          <span className="image-date">{formatDate(img.upload_date)}</span>
                        )}
                      </div>
                      {hasChat && (
                        <div className="chat-indicator">💬</div>
                      )}
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Panel principal del chat */}
        <div className="chat-main-panel">
          <div className="image-panel">
            {image ? (
              (() => {
                const mime = image.mime_type || '';
                const canPreview = mime.startsWith('image/') && mime !== 'application/dicom';
                return canPreview ? (
                  <img
                    className="image-preview"
                    src={apiService.getImageDownloadUrl(image.id)}
                    alt={image.original_filename}
                    onError={(e) => {
                      const target = e.currentTarget as HTMLImageElement;
                      target.style.display = 'none';
                      const placeholder = target.nextElementSibling as HTMLElement | null;
                      if (placeholder) placeholder.style.display = 'block';
                    }}
                  />
                ) : (
                  <div className="image-placeholder">Sin vista previa</div>
                );
              })()
            ) : (
              <div className="image-placeholder">Selecciona una imagen para comenzar</div>
            )}
            <div className="image-placeholder" style={{ display: 'none' }}>Sin vista previa</div>
          </div>

          <div className="conversation-panel">
            {error && (
              <div className="error-banner">{error}</div>
            )}
            
            {!selectedImageId ? (
              <div className="no-image-selected">
                <p>Selecciona una imagen del panel lateral para comenzar a chatear</p>
              </div>
            ) : (
              <>
                {history.length === 0 && !loadingHistory && (
                  <div className="suggestions">
                    {suggestions.map((s, i) => (
                      <button
                        key={i}
                        className="suggestion"
                        onClick={() => setInput(s)}
                      >
                        {s}
                      </button>
                    ))}
                  </div>
                )}
                
                <div className="messages" ref={listRef}>
                  {loadingHistory && history.length === 0 ? (
                    <div className="messages-loading">Cargando conversación...</div>
                  ) : history.length === 0 ? (
                    <div className="messages-empty">Empieza preguntando algo sobre la imagen.</div>
                  ) : (
                    history.map((m, idx) => (
                      <div key={idx} className={`message-row ${m.role}`}>
                        <div className="avatar">{m.role === 'user' ? '🧑' : '🤖'}</div>
                        <div className={`bubble ${m.role}`}>
                          <div className="bubble-meta">
                            {m.role === 'user' ? 'Tú' : 'Asistente'}
                            {m.timestamp && (
                              <span className="message-time">{formatDate(m.timestamp)}</span>
                            )}
                          </div>
                          <div className="bubble-text">{m.content}</div>
                        </div>
                      </div>
                    ))
                  )}
                  {loading && (
                    <div className="message-row assistant">
                      <div className="avatar">🤖</div>
                      <div className="bubble assistant typing">
                        <span className="dot-1">•</span>
                        <span className="dot-2">•</span>
                        <span className="dot-3">•</span>
                      </div>
                    </div>
                  )}
                </div>

                <div className="composer">
                  <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={onKeyDown}
                    placeholder="Escribe tu pregunta sobre la imagen..."
                    disabled={loading}
                  />
                  <button onClick={onSend} disabled={loading || !input.trim()}>
                    {loading ? 'Enviando...' : 'Enviar'}
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ImageChat;


