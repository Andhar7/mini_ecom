// API Response Types
export interface ApiResponse<T> {
  results?: T[];
  count?: number;
  next?: string | null;
  previous?: string | null;
  data?: T;
  message?: string;
  status?: 'success' | 'error';
}

// Auth Types
export interface User {
  id: number;
  username: string;
  email: string;
  first_name?: string;
  last_name?: string;
  phone?: string;
  bio?: string;
  birth_date?: string;
  is_verified: boolean;
  is_staff: boolean;
  is_active: boolean;
  date_joined: string;
  profile_completion_percentage: number;
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  confirm_password: string;
  first_name?: string;
  last_name?: string;
}

export interface UpdateProfileRequest {
  first_name?: string;
  last_name?: string;
  phone?: string;
  bio?: string;
  birth_date?: string;
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
  confirm_new_password: string;
}

export interface PasswordResetRequest {
  email: string;
}

export interface PasswordResetConfirmRequest {
  new_password: string;
  confirm_password: string;
}

// Product Types (Updated to match backend API)
export interface Category {
  id: number;
  name: string;
  slug: string;
  description?: string;
  parent?: number | null;
  image?: string | null;
  is_active: boolean;
  sort_order: number;
  created_at: string;
  updated_at: string;
  full_name: string;
  level: number;
  product_count: number;
  subcategories: Category[];
}

export interface Product {
  id: number;
  name: string;
  slug: string;
  sku: string;
  short_description: string;
  price: string;
  compare_at_price?: string;
  discount_percentage?: number;
  stock_quantity: number;
  is_featured: boolean;
  status: 'active' | 'inactive' | 'draft';
  display_image?: string;
  view_count: number;
  created_at: string;
  updated_at: string;
  category_name?: string;
  owner_username: string;
  is_in_stock: boolean;
  is_low_stock: boolean;
  // Legacy fields for compatibility
  description?: string;
  image?: string;
  category?: { name: string; slug: string };
  is_active?: boolean;
  images?: ProductImage[];
  average_rating?: number;
  review_count?: number;
}

export interface ProductImage {
  id: number;
  image: string;
  alt_text?: string;
  is_primary: boolean;
  created_at: string;
}

export interface ProductStats {
  total_products: number;
  active_products: number;
  low_stock_products: number;
  featured_products: number;
  total_categories: number;
  average_price: string;
}

// Filter and Search Types (Updated to match backend API)
export interface ProductFilters {
  category?: number;       // Use category ID for backend filtering
  category_name?: string;  // Keep for display purposes
  min_price?: number;
  max_price?: number;
  is_featured?: boolean;
  in_stock?: boolean;
  search?: string;
  ordering?: 'name' | '-name' | 'price' | '-price' | 'created_at' | '-created_at';
}

export interface PaginationParams {
  page?: number;
  page_size?: number;
}

// UI State Types
export interface LoadingState {
  isLoading: boolean;
  error: string | null;
}

export interface AuthState extends LoadingState {
  user: User | null;
  tokens: AuthTokens | null;
  isAuthenticated: boolean;
}

// Form Types
export interface FormField {
  value: string;
  error?: string;
  touched: boolean;
}

// Admin Types
export interface AdminStats {
  users_count: number;
  products_count: number;
  categories_count: number;
  orders_count: number;
}

// Notification Types
export interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message: string;
  duration?: number;
}