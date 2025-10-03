import React, { createContext, useContext, useReducer, useEffect } from 'react';
import { User, AuthTokens, AuthState } from '../types';
import { authApi, setAuthTokens } from '../services/api';
import toast from 'react-hot-toast';

// Auth Actions
type AuthAction =
  | { type: 'AUTH_LOADING'; payload: boolean }
  | { type: 'AUTH_SUCCESS'; payload: { user: User; tokens: AuthTokens } }
  | { type: 'AUTH_ERROR'; payload: string }
  | { type: 'AUTH_LOGOUT' }
  | { type: 'UPDATE_USER'; payload: User }
  | { type: 'CLEAR_ERROR' };

// Initial state
const initialState: AuthState = {
  user: null,
  tokens: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,
};

// Auth reducer
const authReducer = (state: AuthState, action: AuthAction): AuthState => {
  switch (action.type) {
    case 'AUTH_LOADING':
      return {
        ...state,
        isLoading: action.payload,
        error: null,
      };
    case 'AUTH_SUCCESS':
      return {
        ...state,
        user: action.payload.user,
        tokens: action.payload.tokens,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      };
    case 'AUTH_ERROR':
      return {
        ...state,
        user: null,
        tokens: null,
        isAuthenticated: false,
        isLoading: false,
        error: action.payload,
      };
    case 'AUTH_LOGOUT':
      return {
        ...initialState,
      };
    case 'UPDATE_USER':
      return {
        ...state,
        user: action.payload,
      };
    case 'CLEAR_ERROR':
      return {
        ...state,
        error: null,
      };
    default:
      return state;
  }
};

// Auth context
interface AuthContextType extends AuthState {
  login: (username: string, password: string) => Promise<void>;
  register: (userData: any) => Promise<void>;
  logout: () => Promise<void>;
  updateProfile: (data: any) => Promise<void>;
  changePassword: (data: any) => Promise<void>;
  clearError: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Auth provider
export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, dispatch] = useReducer(authReducer, initialState);

  // Initialize auth from localStorage
  useEffect(() => {
    const initAuth = async () => {
      const storedTokens = localStorage.getItem('authTokens');
      if (storedTokens) {
        try {
          const tokens = JSON.parse(storedTokens);
          dispatch({ type: 'AUTH_LOADING', payload: true });
          
          // Verify token and get user data
          const user = await authApi.getProfile();
          
          dispatch({
            type: 'AUTH_SUCCESS',
            payload: { user, tokens }
          });
          
          setAuthTokens(tokens);
        } catch (error) {
          console.error('Token verification failed:', error);
          localStorage.removeItem('authTokens');
          dispatch({ type: 'AUTH_LOGOUT' });
        }
      }
    };

    initAuth();
  }, []);

  // Login function
  const login = async (username: string, password: string) => {
    try {
      dispatch({ type: 'AUTH_LOADING', payload: true });
      
      const response = await authApi.login({ username, password });
      
      setAuthTokens(response.tokens);
      dispatch({
        type: 'AUTH_SUCCESS',
        payload: response
      });
      
      toast.success(`Welcome back, ${response.user.first_name || response.user.username}!`);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Login failed';
      dispatch({ type: 'AUTH_ERROR', payload: message });
      toast.error(message);
      throw error;
    }
  };

  // Register function
  const register = async (userData: any) => {
    try {
      dispatch({ type: 'AUTH_LOADING', payload: true });
      
      const response = await authApi.register(userData);
      
      setAuthTokens(response.tokens);
      dispatch({
        type: 'AUTH_SUCCESS',
        payload: response
      });
      
      toast.success('Registration successful! Welcome to our store!');
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Registration failed';
      dispatch({ type: 'AUTH_ERROR', payload: message });
      toast.error(message);
      throw error;
    }
  };

  // Logout function
  const logout = async () => {
    try {
      await authApi.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      dispatch({ type: 'AUTH_LOGOUT' });
      toast.success('Logged out successfully');
    }
  };

  // Update profile function
  const updateProfile = async (data: any) => {
    try {
      dispatch({ type: 'AUTH_LOADING', payload: true });
      
      const updatedUser = await authApi.updateProfile(data);
      
      dispatch({ type: 'UPDATE_USER', payload: updatedUser });
      dispatch({ type: 'AUTH_LOADING', payload: false });
      
      toast.success('Profile updated successfully!');
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Profile update failed';
      dispatch({ type: 'AUTH_ERROR', payload: message });
      toast.error(message);
      throw error;
    }
  };

  // Change password function
  const changePassword = async (data: any) => {
    try {
      dispatch({ type: 'AUTH_LOADING', payload: true });
      
      await authApi.changePassword(data);
      
      dispatch({ type: 'AUTH_LOADING', payload: false });
      toast.success('Password changed successfully!');
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Password change failed';
      dispatch({ type: 'AUTH_ERROR', payload: message });
      toast.error(message);
      throw error;
    }
  };

  // Refresh user data
  const refreshUser = async () => {
    try {
      if (state.isAuthenticated) {
        const user = await authApi.getProfile();
        dispatch({ type: 'UPDATE_USER', payload: user });
      }
    } catch (error) {
      console.error('Failed to refresh user data:', error);
    }
  };

  // Clear error function
  const clearError = () => {
    dispatch({ type: 'CLEAR_ERROR' });
  };

  const value: AuthContextType = {
    ...state,
    login,
    register,
    logout,
    updateProfile,
    changePassword,
    clearError,
    refreshUser,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

// Hook to use auth context
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};