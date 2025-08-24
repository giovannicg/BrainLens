import React, { useEffect, useState, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import { apiService, ChatMessageDTO, ChatHistoryResponse, ImageResponse } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import './ImageChat.css';

const ImageChat: React.FC = () => {
  const { imageId } = useParams<{ imageId: string }>();
  const { user } = useAuth();
  const [history, setHistory] = useState<ChatMessageDTO[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const listRef = useRef<HTMLDivElement>(null);
  const [image, setImage] = useState<ImageResponse | null>(null);
  const [loadingHistory, setLoadingHistory] = useState<boolean>(true);
  const [error, setError] = useState<string>('');
  const suggestions = [
    '¿Qué observas en esta imagen?',
    'Describe la región con mayor anomalía.',
    '¿Hay indicios de tumor? ¿Cuál y por qué?',
    'Resume los hallazgos más relevantes.',
  ];

  const loadHistory = async () => {
    if (!imageId || !user) return;
    try {
      setLoadingHistory(true);
      const [data, img]: [ChatHistoryResponse, ImageResponse] = await Promise.all([
        apiService.getImageChatHistory(imageId, user.id, 50),
        apiService.getImage(imageId),
      ]);
      setHistory(data.messages);
      setImage(img);
      scrollToBottom();
    } catch (e) {
      console.error('Error cargando historial/imagen:', e);
      setError('No se pudo cargar el historial o la imagen.');
    } finally {
      setLoadingHistory(false);
    }
  };

  useEffect(() => {
    loadHistory();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [imageId, user?.id]);

  const scrollToBottom = () => {
    requestAnimationFrame(() => listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: 'smooth' }));
  };

  const onSend = async () => {
    if (!input.trim() || !imageId || !user) return;
    const text = input.trim();
    setInput('');
    setLoading(true);
    // Optimista: agregar el mensaje del usuario primero
    const now = new Date().toISOString();
    const userMsg: ChatMessageDTO = { image_id: imageId, user_id: user.id, role: 'user', content: text, timestamp: now };
    setHistory((h) => [...h, userMsg]);
    try {
      const resp = await apiService.sendImageChatMessage(imageId, user.id, text);
      setHistory((h) => [...h, resp.message]);
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
            <div className="image-placeholder">Sin vista previa</div>
          )}
          <div className="image-placeholder" style={{ display: 'none' }}>Sin vista previa</div>
        </div>

        <div className="conversation-panel">
          {error && (
            <div className="error-banner">{error}</div>
          )}
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
                    <div className="bubble-meta">{m.role === 'user' ? 'Tú' : 'Asistente'}</div>
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
            />
            <button onClick={onSend} disabled={loading || !input.trim()}>
              {loading ? 'Enviando...' : 'Enviar'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ImageChat;


