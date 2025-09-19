// Configuración dinámica de URLs según el entorno
const getApiBaseUrl = () => {
  const runtimeOrigin = typeof window !== 'undefined' ? window.location.origin : '';
  
  // En producción, usar el ALB DNS si está configurado
  if (process.env.NODE_ENV === 'production' && process.env.REACT_APP_ALB_DNS) {
    return `http://${process.env.REACT_APP_ALB_DNS}`;
  }
  
  // En desarrollo o si no hay ALB configurado, usar variables de entorno o runtime origin
  return process.env.REACT_APP_API_URL || runtimeOrigin;
};

// En producción, todos los servicios están detrás del ALB con routing por paths
// En desarrollo, cada servicio tiene su propio puerto
const getAuthApiUrl = () => {
  // Si estamos en producción (no localhost), usar la URL actual
  if (typeof window !== 'undefined' && window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
    return `${window.location.protocol}//${window.location.host}/api/v1`;
  }
  // En desarrollo, usar localhost
  return 'http://localhost:8001/api/v1';
};

const getImageApiUrl = () => {
  // Si estamos en producción (no localhost), usar la URL actual
  if (typeof window !== 'undefined' && window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
    return `${window.location.protocol}//${window.location.host}/api/v1`;
  }
  // En desarrollo, usar localhost
  return 'http://localhost:8002/api/v1';
};

const getAnnotationApiUrl = () => {
  // Si estamos en producción (no localhost), usar la URL actual
  if (typeof window !== 'undefined' && window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
    return `${window.location.protocol}//${window.location.host}/api/v1`;
  }
  // En desarrollo, usar localhost
  return 'http://localhost:8003/api/v1';
};

// Colab proxy (desarrollo en 8004; en prod mismo host /api/v1)
const getColabApiUrl = () => {
  if (typeof window !== 'undefined' && window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
    return `${window.location.protocol}//${window.location.host}/api/v1/colab`; // detrás del ALB con routing
  }
  return 'http://localhost:8004';
};

const API_BASE_URL = getAuthApiUrl();
const IMAGE_API_BASE_URL = getImageApiUrl();
const ANNOTATION_API_BASE_URL = getAnnotationApiUrl();
const COLAB_API_BASE_URL = getColabApiUrl();

export interface UserRegisterRequest {
  email: string;
  username: string;
  password: string;
}

export interface UserLoginRequest {
  email: string;
  password: string;
}

export interface UserResponse {
  id: string;
  email: string;
  username: string;
  is_active: boolean;
  is_verified: boolean;
  role: string;
  created_at: string;
  last_login?: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface ImageResponse {
  id: string;
  filename: string;
  original_filename: string;
  file_size: number;
  mime_type: string;
  width?: number;
  height?: number;
  user_id: string;
  upload_date: string;
  processing_status: string;
  metadata: Record<string, any>;
  prediction?: any; // Datos de predicción del tumor
}

export interface ImageListResponse {
  images: ImageResponse[];
  total: number;
  skip: number;
  limit: number;
}

export interface ImageUploadResponse {
  message: string;
  image: ImageResponse;
  processing_status: string;
  error_code?: string;
  error_detail?: string;
  // Opcional cuando la respuesta viene directamente del proxy de Colab
  prediction?: TumorPredictionResult;
}

export interface AnnotationPoint {
  x: number;
  y: number;
}

export interface AnnotationShape {
  type: string;
  points: AnnotationPoint[];
  properties: Record<string, any>;
}

export interface AnnotationRequest {
  image_id: string;
  user_id: string;
  title: string;
  description: string;
  category: string;
  confidence?: number;
  status?: string;
  shapes: AnnotationShape[];
  metadata?: Record<string, any>;
}

export interface AnnotationResponse {
  id: string;
  image_id: string;
  user_id: string;
  title: string;
  description: string;
  category: string;
  confidence: number;
  status: string;
  shapes: AnnotationShape[];
  metadata: Record<string, any>;
  created_at: string;
  updated_at: string;
  reviewed_by?: string;
  reviewed_at?: string;
  review_notes?: string;
}

export interface AnnotationListResponse {
  annotations: AnnotationResponse[];
  total: number;
}


export interface TumorPredictionResult {
  es_tumor: boolean;
  clase_predicha: string;
  confianza: number;
  probabilidades: Record<string, number>;
  recomendacion: string;
}

// Determina si una etiqueta corresponde a tumor.
// Solo "notumor" se considera como NO tumor, todo lo demás es tumor.
const isTumorLabel = (label: string): boolean => {
  const norm = String(label || '')
    .toLowerCase()
    .trim();
  
  // Solo "notumor" se considera como NO tumor
  return norm !== 'notumor';
};

export interface ProcessingStatusResponse {
  image_id?: string;
  status: string;
  message?: string;
  prediction?: TumorPredictionResult;
  processing_started?: string;
  processing_completed?: string;
}

// Chat sobre imagen
export interface ChatMessageDTO {
  id?: string;
  image_id: string;
  user_id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export interface ChatHistoryResponse {
  messages: ChatMessageDTO[];
  total: number;
}

export interface ChatRequest {
  message: string;
}

export interface ChatResponseDTO {
  answer: string;
  message: ChatMessageDTO;
  history?: ChatMessageDTO[];
}

// Validación (jobs de subida)
export interface ValidationJobResponse {
  job_id: string;
  status: string;
  message: string;
}

export interface ValidationJobStatusResponse {
  job_id: string;
  status: string;
  message: string;
  image_id?: string;
  error?: string;
}

class ApiService {
  private baseUrl: string;
  private imageApiUrl: string;
  private annotationApiUrl: string;
  private colabApiUrl: string;

  constructor() {
    this.baseUrl = API_BASE_URL;
    this.imageApiUrl = IMAGE_API_BASE_URL;
    this.annotationApiUrl = ANNOTATION_API_BASE_URL;
    this.colabApiUrl = COLAB_API_BASE_URL;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    useImageApi: boolean = false,
    useAnnotationApi: boolean = false
  ): Promise<T> {
    let baseUrl = this.baseUrl;
    if (useImageApi) {
      baseUrl = this.imageApiUrl;
    } else if (useAnnotationApi) {
      baseUrl = this.annotationApiUrl;
    }
    // Normalización defensiva para evitar doble "/api/v1"
    const trimmedBase = baseUrl.replace(/\/$/, '');
    let normalizedEndpoint = endpoint;
    if (normalizedEndpoint.startsWith('/api/v1/')) {
      normalizedEndpoint = normalizedEndpoint.replace(/^\/api\/v1\//, '/');
    }
    const url = `${trimmedBase}${normalizedEndpoint}`;
    
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  // Auth methods
  async registerUser(data: UserRegisterRequest): Promise<UserResponse> {
    return this.request<UserResponse>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async loginUser(data: UserLoginRequest): Promise<TokenResponse> {
    return this.request<TokenResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getCurrentUser(token: string): Promise<UserResponse> {
    return this.request<UserResponse>('/auth/me', {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
  }

  // Image methods
  async uploadImage(file: File, userId: string, customName?: string): Promise<ImageUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('user_id', userId);
    if (customName) {
      formData.append('custom_filename', customName);
    }

    // Llamada directa síncrona
    const url = `${this.imageApiUrl}/images/validate-upload`;
    const resp = await fetch(url, { method: 'POST', body: formData });
    if (!resp.ok) {
      const errorData = await resp.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP error! status: ${resp.status}`);
    }
    const raw = await resp.json();
    const data = raw as ImageUploadResponse;
    // Normalizar respuesta si viene del proxy de Colab (status/prediction/mean_score)
    if (!data.prediction && raw && typeof raw === 'object' && 'prediction' in raw && 'mean_score' in raw) {
      const predLabel = String(raw.prediction ?? '');
      const esTumor = isTumorLabel(predLabel);
      data.processing_status = 'completed';
      (data as any).prediction = {
        es_tumor: esTumor,
        clase_predicha: predLabel,
        confianza: Number(raw.mean_score ?? 0),
        probabilidades: {},
        recomendacion: ''
      } as TumorPredictionResult;
    }
    return data;
  }

  // Jobs de validación eliminados (flujo ahora síncrono)

  async getProcessingStatus(imageId: string): Promise<ProcessingStatusResponse> {
    const url = `${this.imageApiUrl}/images/${imageId}/processing-status`;
    
    try {
      const response = await fetch(url);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const raw = await response.json();
      // Si el backend/proxy devolvió directamente el formato de Colab, adaptarlo
      if (raw && typeof raw === 'object' && 'prediction' in raw && 'mean_score' in raw) {
        const predLabel = String(raw.prediction ?? '');
        const esTumor = isTumorLabel(predLabel);
        const normalized: ProcessingStatusResponse = {
          status: 'completed',
          prediction: {
            es_tumor: esTumor,
            clase_predicha: predLabel,
            confianza: Number(raw.mean_score ?? 0),
            probabilidades: {},
            recomendacion: ''
          }
        };
        return normalized;
      }
      return raw as ProcessingStatusResponse;
    } catch (error) {
      // Fallback: si no existe el endpoint (flujo sin Celery), intenta leer la imagen y mapear su predicción
      try {
        const img = await this.getImage(imageId);
        if ((img as any).prediction) {
          const p = (img as any).prediction;
          const normalized: ProcessingStatusResponse = {
            image_id: imageId,
            status: 'completed',
            prediction: {
              es_tumor: Boolean(p.es_tumor ?? isTumorLabel(String(p.clase_predicha ?? ''))),
              clase_predicha: String(p.clase_predicha ?? ''),
              confianza: Number(p.confianza ?? p.mean_score ?? 0),
              probabilidades: p.probabilidades ?? {},
              recomendacion: p.recomendacion ?? ''
            }
          };
          return normalized;
        }
      } catch (e2) {
        console.error('Fallback getImage failed:', e2);
      }
      console.error('Get processing status failed:', error);
      // Como último recurso, devolvemos estado completado sin detalles para no romper la UI
      return { status: 'completed', image_id: imageId };
    }
  }

  async getImages(userId?: string, skip: number = 0, limit: number = 100): Promise<ImageListResponse> {
    const params = new URLSearchParams();
    if (userId) params.append('user_id', userId);
    params.append('skip', skip.toString());
    params.append('limit', limit.toString());
    
    return this.request<ImageListResponse>(`/images/?${params.toString()}`, {}, true);
  }

  async getImage(imageId: string): Promise<ImageResponse> {
    return this.request<ImageResponse>(`/images/${imageId}`, {}, true);
  }

  async deleteImage(imageId: string): Promise<{ message: string; deleted: boolean }> {
    return this.request<{ message: string; deleted: boolean }>(`/images/${imageId}`, {
      method: 'DELETE',
    }, true);
  }

  getImageDownloadUrl(imageId: string): string {
    return `${this.imageApiUrl}/images/download/${imageId}`;
  }

  // Colab proxy prediction (reenvía al servicio 8004)
  async predictImageViaColab(imageId: string): Promise<ProcessingStatusResponse> {
    const downloadUrl = this.getImageDownloadUrl(imageId);
    const res = await fetch(downloadUrl);
    if (!res.ok) {
      throw new Error(`No se pudo descargar la imagen ${imageId}`);
    }
    const blob = await res.blob();
    const file = new File([blob], `${imageId}.jpg`, { type: blob.type || 'application/octet-stream' });
    const form = new FormData();
    form.append('image', file);
    const resp = await fetch(`${this.colabApiUrl}/predict`, { method: 'POST', body: form });
    if (!resp.ok) {
      const t = await resp.text();
      throw new Error(`Colab proxy error: ${resp.status} ${t}`);
    }
    const raw = await resp.json();
    const predLabel = String(raw.prediction ?? '');
    const esTumor = isTumorLabel(predLabel);
    return {
      image_id: imageId,
      status: 'completed',
      prediction: {
        es_tumor: esTumor,
        clase_predicha: predLabel,
        confianza: Number(raw.mean_score ?? 0),
        probabilidades: {},
        recomendacion: ''
      }
    } as ProcessingStatusResponse;
  }



  // Image Chat methods
  async getImageChatHistory(imageId: string, userId: string, limit: number = 50): Promise<ChatHistoryResponse> {
    const params = new URLSearchParams({ user_id: userId, limit: String(limit) });
    return this.request<ChatHistoryResponse>(`/images/${imageId}/chat?${params.toString()}` , {}, true);
  }

  async sendImageChatMessage(imageId: string, userId: string, message: string): Promise<ChatResponseDTO> {
    const params = new URLSearchParams({ user_id: userId });
    return this.request<ChatResponseDTO>(`/images/${imageId}/chat?${params.toString()}`, {
      method: 'POST',
      body: JSON.stringify({ message }),
    }, true);
  }

  // Annotation methods
  async getAnnotations(imageId: string): Promise<AnnotationListResponse> {
    return this.request<AnnotationListResponse>(`/annotations/?image_id=${imageId}`, {}, false, true);
  }

  async getAnnotationsByUser(userId: string): Promise<AnnotationListResponse> {
    return this.request<AnnotationListResponse>(`/annotations/?user_id=${userId}`, {}, false, true);
  }

  async createAnnotation(data: AnnotationRequest): Promise<AnnotationResponse> {
    const response = await this.request<{ message: string; annotation: AnnotationResponse }>(`/annotations/`, {
      method: 'POST',
      body: JSON.stringify(data),
    }, false, true);
    return response.annotation;
  }

  async updateAnnotation(annotationId: string, data: Partial<AnnotationRequest>): Promise<AnnotationResponse> {
    const response = await this.request<{ message: string; annotation: AnnotationResponse }>(`/annotations/${annotationId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }, false, true);
    return response.annotation;
  }

  async deleteAnnotation(annotationId: string): Promise<{ message: string; deleted: boolean }> {
    return this.request<{ message: string; deleted: boolean }>(`/annotations/${annotationId}`, {
      method: 'DELETE',
    }, false, true);
  }
}

export const apiService = new ApiService(); 