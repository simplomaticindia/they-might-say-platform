import { ApiClient } from '@/lib/api-client'

// Mock fetch globally
global.fetch = jest.fn()

describe('ApiClient', () => {
  let apiClient: ApiClient
  const mockFetch = fetch as jest.MockedFunction<typeof fetch>

  beforeEach(() => {
    apiClient = new ApiClient('http://localhost:8000')
    mockFetch.mockClear()
  })

  describe('Authentication', () => {
    it('sets authorization header when token is provided', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ message: 'success' }),
      } as Response)

      apiClient.setAuthToken('test-token')
      await apiClient.get('/test')

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/test',
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': 'Bearer test-token'
          })
        })
      )
    })

    it('removes authorization header when token is cleared', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ message: 'success' }),
      } as Response)

      apiClient.setAuthToken('test-token')
      apiClient.clearAuthToken()
      await apiClient.get('/test')

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/test',
        expect.objectContaining({
          headers: expect.not.objectContaining({
            'Authorization': expect.any(String)
          })
        })
      )
    })
  })

  describe('HTTP Methods', () => {
    it('makes GET requests correctly', async () => {
      const mockResponse = { data: 'test' }
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      } as Response)

      const result = await apiClient.get('/test')

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/test',
        expect.objectContaining({
          method: 'GET'
        })
      )
      expect(result).toEqual(mockResponse)
    })

    it('makes POST requests with data', async () => {
      const mockResponse = { id: 1 }
      const postData = { name: 'test' }
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      } as Response)

      const result = await apiClient.post('/test', postData)

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/test',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(postData),
          headers: expect.objectContaining({
            'Content-Type': 'application/json'
          })
        })
      )
      expect(result).toEqual(mockResponse)
    })

    it('makes PUT requests correctly', async () => {
      const mockResponse = { updated: true }
      const putData = { name: 'updated' }
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      } as Response)

      const result = await apiClient.put('/test/1', putData)

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/test/1',
        expect.objectContaining({
          method: 'PUT',
          body: JSON.stringify(putData)
        })
      )
      expect(result).toEqual(mockResponse)
    })

    it('makes DELETE requests correctly', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({}),
      } as Response)

      await apiClient.delete('/test/1')

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/test/1',
        expect.objectContaining({
          method: 'DELETE'
        })
      )
    })
  })

  describe('File Upload', () => {
    it('uploads files correctly', async () => {
      const mockResponse = { fileId: 'abc123' }
      const mockFile = new File(['test content'], 'test.txt', { type: 'text/plain' })
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      } as Response)

      const result = await apiClient.uploadFile('/upload', mockFile)

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/upload',
        expect.objectContaining({
          method: 'POST',
          body: expect.any(FormData)
        })
      )
      expect(result).toEqual(mockResponse)
    })

    it('uploads files with additional data', async () => {
      const mockResponse = { fileId: 'abc123' }
      const mockFile = new File(['test content'], 'test.txt', { type: 'text/plain' })
      const additionalData = { description: 'Test file' }
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      } as Response)

      const result = await apiClient.uploadFile('/upload', mockFile, additionalData)

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/upload',
        expect.objectContaining({
          method: 'POST',
          body: expect.any(FormData)
        })
      )
      expect(result).toEqual(mockResponse)
    })
  })

  describe('Error Handling', () => {
    it('throws error for non-ok responses', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        statusText: 'Not Found',
        json: async () => ({ error: 'Resource not found' }),
      } as Response)

      await expect(apiClient.get('/nonexistent')).rejects.toThrow('HTTP error! status: 404')
    })

    it('handles network errors', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'))

      await expect(apiClient.get('/test')).rejects.toThrow('Network error')
    })

    it('handles JSON parsing errors', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => {
          throw new Error('Invalid JSON')
        },
      } as Response)

      await expect(apiClient.get('/test')).rejects.toThrow('Invalid JSON')
    })
  })

  describe('Query Parameters', () => {
    it('appends query parameters correctly', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: 'test' }),
      } as Response)

      await apiClient.get('/test', { page: 1, limit: 10 })

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/test?page=1&limit=10',
        expect.any(Object)
      )
    })

    it('handles empty query parameters', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: 'test' }),
      } as Response)

      await apiClient.get('/test', {})

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/test',
        expect.any(Object)
      )
    })
  })
})