import axios, { AxiosResponse, AxiosError } from 'axios';
import toast from 'react-hot-toast';
import type { 
  AuthTokens, 
  User, 
  LoginRequest, 
  RegisterRequest, 
  UpdateProfileRequest,
  ChangePasswordRequest,
  PasswordResetRequest,
  PasswordResetConfirmRequest,
  Product,
  Category,
  ProductFilters,
  PaginationParams,
  ApiResponse,
  ProductStats
} from '../types';

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Token management
let authTokens: AuthTokens | null = null;

export const setAuthTokens = (tokens: AuthTokens | null) => {
  authTokens = tokens;
  if (tokens) {
    localStorage.setItem('authTokens', JSON.stringify(tokens));
    api.defaults.headers.common['Authorization'] = `Bearer ${tokens.access}`;
  } else {
    localStorage.removeItem('authTokens');
    delete api.defaults.headers.common['Authorization'];
  }
};

// Initialize tokens from localStorage
const storedTokens = localStorage.getItem('authTokens');
if (storedTokens) {
  try {
    const tokens = JSON.parse(storedTokens);
    setAuthTokens(tokens);
  } catch (error) {
    console.error('Error parsing stored tokens:', error);
    localStorage.removeItem('authTokens');
  }
}

// Request interceptor
api.interceptors.request.use(
  (config) => {
    if (authTokens?.access) {
      config.headers.Authorization = `Bearer ${authTokens.access}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for token refresh
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as any;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      if (authTokens?.refresh) {
        try {
          const response = await axios.post(`${API_BASE_URL}/auth/token/refresh/`, {
            refresh: authTokens.refresh
          });
          
          const newTokens = { ...authTokens, access: response.data.access };
          setAuthTokens(newTokens);
          
          return api(originalRequest);
        } catch (refreshError) {
          setAuthTokens(null);
          window.location.href = '/login';
        }
      }
    }
    
    return Promise.reject(error);
  }
);

// Error handler
const handleApiError = (error: AxiosError): never => {
  if (error.response?.data) {
    const errorData = error.response.data as any;
    const message = errorData.message || errorData.detail || 'An error occurred';
    throw new Error(message);
  }
  throw new Error(error.message || 'Network error');
};

// Auth API
export const authApi = {
  // Register new user
  register: async (data: RegisterRequest): Promise<{ user: User; tokens: AuthTokens }> => {
    try {
      const response: AxiosResponse = await api.post('/auth/register/', data);
      return response.data;
    } catch (error) {
      handleApiError(error as AxiosError);
    }
  },

  // Login user
  login: async (data: LoginRequest): Promise<{ user: User; tokens: AuthTokens }> => {
    try {
      const response: AxiosResponse = await api.post('/auth/login/', data);
      return response.data;
    } catch (error) {
      handleApiError(error as AxiosError);
    }
  },

  // Logout user
  logout: async (): Promise<void> => {
    try {
      if (authTokens?.refresh) {
        await api.post('/auth/logout/', { refresh_token: authTokens.refresh });
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      setAuthTokens(null);
    }
  },

  // Get user profile
  getProfile: async (): Promise<User> => {
    try {
      const response: AxiosResponse = await api.get('/auth/profile/');
      return response.data;
    } catch (error) {
      handleApiError(error as AxiosError);
    }
  },

  // Update user profile
  updateProfile: async (data: UpdateProfileRequest): Promise<User> => {
    try {
      const response: AxiosResponse = await api.put('/auth/profile/update/', data);
      return response.data;
    } catch (error) {
      handleApiError(error as AxiosError);
    }
  },

  // Change password
  changePassword: async (data: ChangePasswordRequest): Promise<void> => {
    try {
      await api.post('/auth/profile/change-password/', data);
    } catch (error) {
      handleApiError(error as AxiosError);
    }
  },

  // Request password reset
  requestPasswordReset: async (data: PasswordResetRequest): Promise<void> => {
    try {
      await api.post('/auth/password-reset/', data);
    } catch (error) {
      handleApiError(error as AxiosError);
    }
  },

  // Confirm password reset
  confirmPasswordReset: async (token: string, data: PasswordResetConfirmRequest): Promise<void> => {
    try {
      await api.post(`/auth/password-reset/confirm/${token}/`, data);
    } catch (error) {
      handleApiError(error as AxiosError);
    }
  },

  // Resend verification email
  resendVerification: async (): Promise<void> => {
    try {
      await api.post('/auth/resend-verification/');
    } catch (error) {
      handleApiError(error as AxiosError);
    }
  },

  // Verify email
  verifyEmail: async (token: string): Promise<void> => {
    try {
      await api.get(`/auth/verify-email/${token}/`);
    } catch (error) {
      handleApiError(error as AxiosError);
    }
  },

  // Deactivate account
  deactivateAccount: async (password: string, reason?: string): Promise<void> => {
    try {
      await api.post('/auth/deactivate/', { password, reason });
    } catch (error) {
      handleApiError(error as AxiosError);
    }
  },

  // Delete account
  deleteAccount: async (password: string, confirmation: string): Promise<void> => {
    try {
      await api.delete('/auth/delete/', { 
        data: { password, confirmation }
      });
    } catch (error) {
      handleApiError(error as AxiosError);
    }
  }
};

// Products API
export const productsApi = {
  // Get all products (public)
  getPublicProducts: async (params?: ProductFilters & PaginationParams): Promise<ApiResponse<Product>> => {
    try {
      const response: AxiosResponse = await api.get('/public/products/', { params });
      return response.data;
    } catch (error) {
      handleApiError(error as AxiosError);
    }
  },

  // Get product by slug (public)
  getPublicProduct: async (slug: string): Promise<Product> => {
    try {
      const response: AxiosResponse = await api.get(`/public/products/${slug}/`);
      return response.data;
    } catch (error) {
      handleApiError(error as AxiosError);
    }
  },

  // Get featured products (public)
  getFeaturedProducts: async (): Promise<Product[]> => {
    try {
      const response: AxiosResponse = await api.get('/public/featured/');
      return response.data;
    } catch (error) {
      handleApiError(error as AxiosError);
    }
  },

  // Search products (public)
  searchProducts: async (query: string, filters?: ProductFilters): Promise<ApiResponse<Product>> => {
    try {
      const params = { search: query, ...filters };
      const response: AxiosResponse = await api.get('/public/search/', { params });
      return response.data;
    } catch (error) {
      handleApiError(error as AxiosError);
    }
  },

  // Admin: Get all products
  getAllProducts: async (params?: ProductFilters & PaginationParams): Promise<ApiResponse<Product>> => {
    try {
      const response: AxiosResponse = await api.get('/products/', { params });
      return response.data;
    } catch (error) {
      handleApiError(error as AxiosError);
    }
  },

  // Admin: Get product by ID
  getProduct: async (id: number): Promise<Product> => {
    try {
      const response: AxiosResponse = await api.get(`/products/${id}/`);
      return response.data;
    } catch (error) {
      handleApiError(error as AxiosError);
    }
  },

  // Admin: Create product
  createProduct: async (data: FormData): Promise<Product> => {
    try {
      const response: AxiosResponse = await api.post('/products/', data, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      return response.data;
    } catch (error) {
      handleApiError(error as AxiosError);
    }
  },

  // Admin: Update product
  updateProduct: async (id: number, data: FormData): Promise<Product> => {
    try {
      const response: AxiosResponse = await api.put(`/products/${id}/`, data, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      return response.data;
    } catch (error) {
      handleApiError(error as AxiosError);
    }
  },

  // Admin: Delete product
  deleteProduct: async (id: number): Promise<void> => {
    try {
      await api.delete(`/products/${id}/`);
    } catch (error) {
      handleApiError(error as AxiosError);
    }
  },

  // Get product stats
  getProductStats: async (): Promise<ProductStats> => {
    try {
      const response: AxiosResponse = await api.get('/stats/');
      return response.data;
    } catch (error) {
      handleApiError(error as AxiosError);
    }
  },

  // Get low stock alerts
  getLowStockAlerts: async (): Promise<Product[]> => {
    try {
      const response: AxiosResponse = await api.get('/low-stock-alerts/');
      return response.data;
    } catch (error) {
      handleApiError(error as AxiosError);
    }
  }
};

// Categories API
export const categoriesApi = {
  // Get all categories (public)
  getCategories: async (): Promise<Category[]> => {
    try {
      const response: AxiosResponse = await api.get('/categories/');
      return response.data.results || response.data;
    } catch (error) {
      handleApiError(error as AxiosError);
    }
  },

  // Get category by ID
  getCategory: async (id: number): Promise<Category> => {
    try {
      const response: AxiosResponse = await api.get(`/categories/${id}/`);
      return response.data;
    } catch (error) {
      handleApiError(error as AxiosError);
    }
  },

  // Admin: Create category
  createCategory: async (data: FormData): Promise<Category> => {
    try {
      const response: AxiosResponse = await api.post('/categories/', data, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      return response.data;
    } catch (error) {
      handleApiError(error as AxiosError);
    }
  },

  // Admin: Update category
  updateCategory: async (id: number, data: FormData): Promise<Category> => {
    try {
      const response: AxiosResponse = await api.put(`/categories/${id}/`, data, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      return response.data;
    } catch (error) {
      handleApiError(error as AxiosError);
    }
  },

  // Admin: Delete category
  deleteCategory: async (id: number): Promise<void> => {
    try {
      await api.delete(`/categories/${id}/`);
    } catch (error) {
      handleApiError(error as AxiosError);
    }
  }
};

export default api;