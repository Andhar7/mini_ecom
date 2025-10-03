import { useState, useEffect, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { productsApi, categoriesApi } from '../services/api';
import { Product, Category, ProductFilters, PaginationParams, ApiResponse } from '../types';
import toast from 'react-hot-toast';

// Products hook
export const useProducts = (filters?: ProductFilters & PaginationParams) => {
  return useQuery({
    queryKey: ['products', filters],
    queryFn: () => productsApi.getPublicProducts(filters),
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: false,
  });
};

// Single product hook
export const useProduct = (slug: string) => {
  return useQuery({
    queryKey: ['product', slug],
    queryFn: () => productsApi.getPublicProduct(slug),
    enabled: !!slug,
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
};

// Featured products hook
export const useFeaturedProducts = () => {
  return useQuery({
    queryKey: ['featured-products'],
    queryFn: () => productsApi.getFeaturedProducts(),
    staleTime: 15 * 60 * 1000, // 15 minutes
  });
};

// Search products hook
export const useSearchProducts = (query: string, filters?: ProductFilters) => {
  return useQuery({
    queryKey: ['search-products', query, filters],
    queryFn: () => productsApi.searchProducts(query, filters),
    enabled: !!query && query.length > 2,
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
};

// Categories hook
export const useCategories = () => {
  return useQuery({
    queryKey: ['categories'],
    queryFn: () => categoriesApi.getCategories(),
    staleTime: 30 * 60 * 1000, // 30 minutes
  });
};

// Admin products hook (requires authentication)
export const useAdminProducts = (filters?: ProductFilters & PaginationParams) => {
  return useQuery({
    queryKey: ['admin-products', filters],
    queryFn: () => productsApi.getAllProducts(filters),
    staleTime: 1 * 60 * 1000, // 1 minute for admin data
  });
};

// Product stats hook (admin)
export const useProductStats = () => {
  return useQuery({
    queryKey: ['product-stats'],
    queryFn: () => productsApi.getProductStats(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

// Low stock alerts hook (admin)
export const useLowStockAlerts = () => {
  return useQuery({
    queryKey: ['low-stock-alerts'],
    queryFn: () => productsApi.getLowStockAlerts(),
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
};

// Product mutations (admin)
export const useProductMutations = () => {
  const queryClient = useQueryClient();

  const createProduct = useMutation({
    mutationFn: (data: FormData) => productsApi.createProduct(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-products'] });
      queryClient.invalidateQueries({ queryKey: ['products'] });
      queryClient.invalidateQueries({ queryKey: ['product-stats'] });
      toast.success('Product created successfully!');
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to create product');
    }
  });

  const updateProduct = useMutation({
    mutationFn: ({ id, data }: { id: number; data: FormData }) => 
      productsApi.updateProduct(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-products'] });
      queryClient.invalidateQueries({ queryKey: ['products'] });
      queryClient.invalidateQueries({ queryKey: ['product'] });
      toast.success('Product updated successfully!');
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to update product');
    }
  });

  const deleteProduct = useMutation({
    mutationFn: (id: number) => productsApi.deleteProduct(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-products'] });
      queryClient.invalidateQueries({ queryKey: ['products'] });
      queryClient.invalidateQueries({ queryKey: ['product-stats'] });
      toast.success('Product deleted successfully!');
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to delete product');
    }
  });

  return {
    createProduct,
    updateProduct,
    deleteProduct,
  };
};

// Category mutations (admin)
export const useCategoryMutations = () => {
  const queryClient = useQueryClient();

  const createCategory = useMutation({
    mutationFn: (data: FormData) => categoriesApi.createCategory(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['categories'] });
      toast.success('Category created successfully!');
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to create category');
    }
  });

  const updateCategory = useMutation({
    mutationFn: ({ id, data }: { id: number; data: FormData }) => 
      categoriesApi.updateCategory(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['categories'] });
      toast.success('Category updated successfully!');
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to update category');
    }
  });

  const deleteCategory = useMutation({
    mutationFn: (id: number) => categoriesApi.deleteCategory(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['categories'] });
      toast.success('Category deleted successfully!');
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to delete category');
    }
  });

  return {
    createCategory,
    updateCategory,
    deleteCategory,
  };
};

// Product filters hook
export const useProductFilters = () => {
  const [filters, setFilters] = useState<ProductFilters>({});
  const [pagination, setPagination] = useState<PaginationParams>({
    page: 1,
    page_size: 12,
  });

  const updateFilter = useCallback((key: keyof ProductFilters, value: any) => {
    setFilters(prev => ({
      ...prev,
      [key]: value,
    }));
    setPagination(prev => ({ ...prev, page: 1 })); // Reset to first page
  }, []);

  const clearFilters = useCallback(() => {
    setFilters({});
    setPagination({ page: 1, page_size: 12 });
  }, []);

  const updatePagination = useCallback((page: number) => {
    setPagination(prev => ({ ...prev, page }));
  }, []);

  return {
    filters,
    pagination,
    updateFilter,
    clearFilters,
    updatePagination,
    allParams: { ...filters, ...pagination },
  };
};