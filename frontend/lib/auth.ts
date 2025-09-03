/**
 * Authentication utilities and API client
 */
import axios, { AxiosResponse } from 'axios';
import Cookies from 'js-cookie';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Types
export interface User {
  id: string;
  username: string;
  email: string;
  name: string;
  role: 'admin' | 'host' | 'producer' | 'viewer';
  is_active: boolean;
  is_verified: boolean;
  avatar_url?: string;
  created_at: string;
  last_login?: string;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface ApiError {
  detail: string;
  status_code?: number;
}

// Cookie names
const ACCESS_TOKEN_KEY = 'tms_access_token';
const REFRESH_TOKEN_KEY = 'tms_refresh_token';
const USER_KEY = 'tms_user';

// Axios instance with interceptors
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = getAccessToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = getRefreshToken();
        if (refreshToken) {
          const response = await refreshAccessToken(refreshToken);
          setTokens(response.access_token, response.refresh_token);
          setUser(response.user);
          
          // Retry original request with new token
          originalRequest.headers.Authorization = `Bearer ${response.access_token}`;
          return apiClient(originalRequest);
        }
      } catch (refreshError) {
        // Refresh failed, logout user
        logout();
        window.location.href = '/login';
      }
    }

    return Promise.reject(error);
  }
);

// Token management
export const getAccessToken = (): string | null => {
  return Cookies.get(ACCESS_TOKEN_KEY) || null;
};

export const getRefreshToken = (): string | null => {
  return Cookies.get(REFRESH_TOKEN_KEY) || null;
};

export const setTokens = (accessToken: string, refreshToken: string): void => {
  const cookieOptions = {
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'strict' as const,
  };

  Cookies.set(ACCESS_TOKEN_KEY, accessToken, {
    ...cookieOptions,
    expires: 1, // 1 day
  });

  Cookies.set(REFRESH_TOKEN_KEY, refreshToken, {
    ...cookieOptions,
    expires: 7, // 7 days
  });
};

export const clearTokens = (): void => {
  Cookies.remove(ACCESS_TOKEN_KEY);
  Cookies.remove(REFRESH_TOKEN_KEY);
  Cookies.remove(USER_KEY);
};

// User management
export const getUser = (): User | null => {
  const userStr = Cookies.get(USER_KEY);
  if (userStr) {
    try {
      return JSON.parse(userStr);
    } catch {
      return null;
    }
  }
  return null;
};

export const setUser = (user: User): void => {
  Cookies.set(USER_KEY, JSON.stringify(user), {
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'strict',
    expires: 7,
  });
};

export const clearUser = (): void => {
  Cookies.remove(USER_KEY);
};

// Authentication functions
export const login = async (credentials: LoginCredentials): Promise<AuthResponse> => {
  try {
    const response: AxiosResponse<AuthResponse> = await apiClient.post('/auth/login-json', credentials);
    
    const { access_token, refresh_token, user } = response.data;
    
    // Store tokens and user data
    setTokens(access_token, refresh_token);
    setUser(user);
    
    return response.data;
  } catch (error: any) {
    const apiError: ApiError = {
      detail: error.response?.data?.detail || 'Login failed',
      status_code: error.response?.status,
    };
    throw apiError;
  }
};

export const logout = async (): Promise<void> => {
  try {
    await apiClient.post('/auth/logout');
  } catch (error) {
    // Continue with logout even if API call fails
    console.warn('Logout API call failed:', error);
  } finally {
    clearTokens();
    clearUser();
  }
};

export const refreshAccessToken = async (refreshToken: string): Promise<AuthResponse> => {
  try {
    const response: AxiosResponse<AuthResponse> = await axios.post(
      `${API_BASE_URL}/auth/refresh`,
      { refresh_token: refreshToken },
      {
        headers: { 'Content-Type': 'application/json' },
      }
    );
    
    return response.data;
  } catch (error: any) {
    const apiError: ApiError = {
      detail: error.response?.data?.detail || 'Token refresh failed',
      status_code: error.response?.status,
    };
    throw apiError;
  }
};

export const getCurrentUser = async (): Promise<User> => {
  try {
    const response: AxiosResponse<User> = await apiClient.get('/auth/me');
    setUser(response.data);
    return response.data;
  } catch (error: any) {
    const apiError: ApiError = {
      detail: error.response?.data?.detail || 'Failed to get user info',
      status_code: error.response?.status,
    };
    throw apiError;
  }
};

// Authentication status
export const isAuthenticated = (): boolean => {
  const token = getAccessToken();
  const user = getUser();
  return !!(token && user);
};

export const hasRole = (requiredRole: User['role']): boolean => {
  const user = getUser();
  if (!user) return false;

  const roleHierarchy = {
    viewer: 1,
    producer: 2,
    host: 3,
    admin: 4,
  };

  const userLevel = roleHierarchy[user.role] || 0;
  const requiredLevel = roleHierarchy[requiredRole] || 0;

  return userLevel >= requiredLevel;
};

export const isAdmin = (): boolean => {
  return hasRole('admin');
};

// Export the configured axios instance for other API calls
export { apiClient };