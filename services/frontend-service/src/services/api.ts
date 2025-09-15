const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8001';
const IMAGE_API_BASE_URL = process.env.REACT_APP_IMAGE_API_URL || 'http://localhost:8002';

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

  constructor() {
    this.baseUrl = API_BASE_URL;
    this.imageApiUrl = IMAGE_API_BASE_URL;
    this.annotationApiUrl = process.env.REACT_APP_ANNOTATION_API_URL || 'http://localhost:8003';
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
    const url = `${baseUrl}${endpoint}`;
    
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
    const url = `${this.imageApiUrl}/api/v1/images/validate-upload`;
    const resp = await fetch(url, { method: 'POST', body: formData });
    if (!resp.ok) {
      const errorData = await resp.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP error! status: ${resp.status}`);
    }
    const data = (await resp.json()) as ImageUploadResponse;
    return data;
  }

  // Jobs de validación eliminados (flujo ahora síncrono)

  async getProcessingStatus(imageId: string): Promise<ProcessingStatusResponse> {
    const url = `${this.imageApiUrl}/api/v1/images/${imageId}/processing-status`;
    
    try {
      const response = await fetch(url);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Get processing status failed:', error);
      throw error;
    }
  }

  async getImages(userId?: string, skip: number = 0, limit: number = 100): Promise<ImageListResponse> {
    const params = new URLSearchParams();
    if (userId) params.append('user_id', userId);
    params.append('skip', skip.toString());
    params.append('limit', limit.toString());
    
    return this.request<ImageListResponse>(`/api/v1/images/?${params.toString()}`, {}, true);
  }

  async getImage(imageId: string): Promise<ImageResponse> {
    return this.request<ImageResponse>(`/api/v1/images/${imageId}`, {}, true);
  }

  async deleteImage(imageId: string): Promise<{ message: string; deleted: boolean }> {
    return this.request<{ message: string; deleted: boolean }>(`/api/v1/images/${imageId}`, {
      method: 'DELETE',
    }, true);
  }

  getImageDownloadUrl(imageId: string): string {
    return `${this.imageApiUrl}/api/v1/images/download/${imageId}`;
  }

  // Image Chat methods
  async getImageChatHistory(imageId: string, userId: string, limit: number = 50): Promise<ChatHistoryResponse> {
    const params = new URLSearchParams({ user_id: userId, limit: String(limit) });
    return this.request<ChatHistoryResponse>(`/api/v1/images/${imageId}/chat?${params.toString()}` , {}, true);
  }

  async sendImageChatMessage(imageId: string, userId: string, message: string): Promise<ChatResponseDTO> {
    const params = new URLSearchParams({ user_id: userId });
    return this.request<ChatResponseDTO>(`/api/v1/images/${imageId}/chat?${params.toString()}`, {
      method: 'POST',
      body: JSON.stringify({ message }),
    }, true);
  }

  // Annotation methods
  async getAnnotations(imageId: string): Promise<AnnotationListResponse> {
    return this.request<AnnotationListResponse>(`/api/v1/annotations/?image_id=${imageId}`, {}, false, true);
  }

  async getAnnotationsByUser(userId: string): Promise<AnnotationListResponse> {
    return this.request<AnnotationListResponse>(`/api/v1/annotations/?user_id=${userId}`, {}, false, true);
  }

  async createAnnotation(data: AnnotationRequest): Promise<AnnotationResponse> {
    const response = await this.request<{ message: string; annotation: AnnotationResponse }>('/api/v1/annotations/', {
      method: 'POST',
      body: JSON.stringify(data),
    }, false, true);
    return response.annotation;
  }

  async updateAnnotation(annotationId: string, data: Partial<AnnotationRequest>): Promise<AnnotationResponse> {
    const response = await this.request<{ message: string; annotation: AnnotationResponse }>(`/api/v1/annotations/${annotationId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }, false, true);
    return response.annotation;
  }

  async deleteAnnotation(annotationId: string): Promise<{ message: string; deleted: boolean }> {
    return this.request<{ message: string; deleted: boolean }>(`/api/v1/annotations/${annotationId}`, {
      method: 'DELETE',
    }, false, true);
  }
}

export const apiService = new ApiService(); 