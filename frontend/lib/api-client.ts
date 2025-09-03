import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'
import { getAccessToken, logout } from './auth'

class ApiClient {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // Request interceptor to add auth token
    this.client.interceptors.request.use(
      (config) => {
        const token = getAccessToken()
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
        return config
      },
      (error) => {
        return Promise.reject(error)
      }
    )

    // Response interceptor to handle auth errors
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        if (error.response?.status === 401) {
          // Token expired or invalid
          await logout()
          window.location.href = '/login'
        }
        return Promise.reject(error)
      }
    )
  }

  async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.get(url, config)
  }

  async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.post(url, data, config)
  }

  async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.put(url, data, config)
  }

  async patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.patch(url, data, config)
  }

  async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.delete(url, config)
  }

  // Convenience methods for common operations
  async uploadFile(url: string, file: File, onUploadProgress?: (progress: number) => void): Promise<AxiosResponse> {
    const formData = new FormData()
    formData.append('file', file)

    return this.client.post(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onUploadProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onUploadProgress(progress)
        }
      },
    })
  }

  async uploadFiles(url: string, files: File[], metadata?: any, onUploadProgress?: (progress: number) => void): Promise<AxiosResponse> {
    const formData = new FormData()
    
    files.forEach((file, index) => {
      formData.append(`files`, file)
    })

    if (metadata) {
      formData.append('metadata', JSON.stringify(metadata))
    }

    return this.client.post(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onUploadProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onUploadProgress(progress)
        }
      },
    })
  }

  // Streaming support for real-time responses
  async getStream(url: string, config?: AxiosRequestConfig): Promise<ReadableStream> {
    const response = await this.client.get(url, {
      ...config,
      responseType: 'stream',
    })
    return response.data
  }

  // WebSocket connection helper
  createWebSocket(path: string): WebSocket {
    const token = getAccessToken()
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'
    const url = `${wsUrl}${path}${token ? `?token=${token}` : ''}`
    return new WebSocket(url)
  }

  // Health check
  async healthCheck(): Promise<boolean> {
    try {
      await this.client.get('/health')
      return true
    } catch {
      return false
    }
  }

  // Get client instance for advanced usage
  getClient(): AxiosInstance {
    return this.client
  }
}

// Export singleton instance
export const apiClient = new ApiClient()

// Export types for convenience
export type { AxiosResponse, AxiosRequestConfig } from 'axios'