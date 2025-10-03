import React, { useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useProducts, useCategories, useProductFilters } from '../../hooks/useProducts';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import { 
  MagnifyingGlassIcon, 
  FunnelIcon, 
  ShoppingBagIcon,
  StarIcon,
  AdjustmentsHorizontalIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';
import { cn } from '../../utils/cn';

export const ProductList: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [showFilters, setShowFilters] = useState(false);
  const [searchQuery, setSearchQuery] = useState(searchParams.get('search') || '');
  
  const {
    filters,
    pagination,
    updateFilter,
    clearFilters,
    updatePagination,
    allParams
  } = useProductFilters();

  // Initialize filters from URL params
  React.useEffect(() => {
    const category = searchParams.get('category');
    const search = searchParams.get('search');
    const minPrice = searchParams.get('min_price');
    const maxPrice = searchParams.get('max_price');
    const featured = searchParams.get('featured');
    const ordering = searchParams.get('ordering');

    if (category && category !== filters.category) updateFilter('category', category);
    if (search && search !== filters.search) updateFilter('search', search);
    if (minPrice && Number(minPrice) !== filters.min_price) updateFilter('min_price', Number(minPrice));
    if (maxPrice && Number(maxPrice) !== filters.max_price) updateFilter('max_price', Number(maxPrice));
    if (featured && featured !== String(filters.is_featured)) updateFilter('is_featured', featured === 'true');
    if (ordering && ordering !== filters.ordering) updateFilter('ordering', ordering);
  }, [searchParams]);

  const { data: productsData, isLoading: loadingProducts, error } = useProducts(allParams);
  const { data: categories, isLoading: loadingCategories } = useCategories();

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    updateFilter('search', searchQuery);
    setSearchParams({ ...Object.fromEntries(searchParams), search: searchQuery });
  };

  const handleFilterChange = (key: string, value: any) => {
    updateFilter(key as any, value);
    const newParams = new URLSearchParams(searchParams);
    if (value) {
      newParams.set(key, String(value));
    } else {
      newParams.delete(key);
    }
    setSearchParams(newParams);
  };

  const handleClearFilters = () => {
    clearFilters();
    setSearchQuery('');
    setSearchParams({});
  };

  const sortOptions = [
    { value: 'name', label: 'Name (A-Z)' },
    { value: '-name', label: 'Name (Z-A)' },
    { value: 'price', label: 'Price (Low to High)' },
    { value: '-price', label: 'Price (High to Low)' },
    { value: '-created_at', label: 'Newest First' },
    { value: 'created_at', label: 'Oldest First' },
  ];

  const products = productsData?.results || [];
  const totalCount = productsData?.count || 0;
  const hasNextPage = !!productsData?.next;
  const hasPreviousPage = !!productsData?.previous;

  if (loadingProducts && !products.length) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex justify-center items-center h-64">
          <LoadingSpinner size="lg" />
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">Products</h1>
        
        {/* Search and Filter Bar */}
        <div className="flex flex-col lg:flex-row gap-4 items-start lg:items-center justify-between">
          <form onSubmit={handleSearch} className="flex-1 max-w-lg">
            <div className="relative">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search products..."
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
          </form>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowFilters(!showFilters)}
              className="lg:hidden"
            >
              <FunnelIcon className="w-4 h-4 mr-2" />
              Filters
            </Button>
            
            <select
              value={filters.ordering || ''}
              onChange={(e) => handleFilterChange('ordering', e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-primary-500 focus:border-primary-500"
            >
              <option value="">Sort by</option>
              {sortOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Active Filters */}
        {(filters.category || filters.search || filters.min_price || filters.max_price || filters.is_featured) && (
          <div className="mt-4 flex flex-wrap items-center gap-2">
            <span className="text-sm text-gray-500">Active filters:</span>
            {filters.category && (
              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-primary-100 text-primary-800">
                Category: {filters.category}
                <button
                  onClick={() => handleFilterChange('category', '')}
                  className="ml-1 text-primary-600 hover:text-primary-800"
                >
                  <XMarkIcon className="w-3 h-3" />
                </button>
              </span>
            )}
            {filters.search && (
              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-primary-100 text-primary-800">
                Search: {filters.search}
                <button
                  onClick={() => {
                    handleFilterChange('search', '');
                    setSearchQuery('');
                  }}
                  className="ml-1 text-primary-600 hover:text-primary-800"
                >
                  <XMarkIcon className="w-3 h-3" />
                </button>
              </span>
            )}
            {(filters.min_price || filters.max_price) && (
              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-primary-100 text-primary-800">
                Price: ${filters.min_price || 0} - ${filters.max_price || '∞'}
                <button
                  onClick={() => {
                    handleFilterChange('min_price', '');
                    handleFilterChange('max_price', '');
                  }}
                  className="ml-1 text-primary-600 hover:text-primary-800"
                >
                  <XMarkIcon className="w-3 h-3" />
                </button>
              </span>
            )}
            <Button
              variant="ghost"
              size="sm"
              onClick={handleClearFilters}
              className="text-xs"
            >
              Clear all
            </Button>
          </div>
        )}
      </div>

      <div className="lg:grid lg:grid-cols-4 lg:gap-8">
        {/* Filters Sidebar */}
        <div className={cn(
          "lg:col-span-1",
          showFilters ? "block" : "hidden lg:block"
        )}>
          <div className="bg-white rounded-lg shadow-sm border p-6 sticky top-20">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-gray-900">Filters</h3>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleClearFilters}
                className="text-sm"
              >
                Clear all
              </Button>
            </div>

            <div className="space-y-6">
              {/* Categories */}
              <div>
                <h4 className="text-sm font-medium text-gray-900 mb-3">Category</h4>
                {loadingCategories ? (
                  <LoadingSpinner size="sm" />
                ) : (
                  <div className="space-y-2">
                    <label className="flex items-center">
                      <input
                        type="radio"
                        name="category"
                        value=""
                        checked={!filters.category}
                        onChange={() => handleFilterChange('category', '')}
                        className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300"
                      />
                      <span className="ml-2 text-sm text-gray-600">All Categories</span>
                    </label>
                    {categories?.map((category) => (
                      <label key={category.id} className="flex items-center">
                        <input
                          type="radio"
                          name="category"
                          value={category.slug}
                          checked={filters.category === category.slug}
                          onChange={() => handleFilterChange('category', category.slug)}
                          className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300"
                        />
                        <span className="ml-2 text-sm text-gray-600">
                          {category.name} ({category.product_count})
                        </span>
                      </label>
                    ))}
                  </div>
                )}
              </div>

              {/* Price Range */}
              <div>
                <h4 className="text-sm font-medium text-gray-900 mb-3">Price Range</h4>
                <div className="grid grid-cols-2 gap-2">
                  <Input
                    type="number"
                    placeholder="Min"
                    value={filters.min_price || ''}
                    onChange={(e) => handleFilterChange('min_price', e.target.value ? Number(e.target.value) : '')}
                    className="text-sm"
                  />
                  <Input
                    type="number"
                    placeholder="Max"
                    value={filters.max_price || ''}
                    onChange={(e) => handleFilterChange('max_price', e.target.value ? Number(e.target.value) : '')}
                    className="text-sm"
                  />
                </div>
              </div>

              {/* Other Filters */}
              <div>
                <h4 className="text-sm font-medium text-gray-900 mb-3">Filters</h4>
                <div className="space-y-2">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={filters.is_featured || false}
                      onChange={(e) => handleFilterChange('is_featured', e.target.checked)}
                      className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                    />
                    <span className="ml-2 text-sm text-gray-600">Featured Products</span>
                  </label>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={filters.in_stock || false}
                      onChange={(e) => handleFilterChange('in_stock', e.target.checked)}
                      className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                    />
                    <span className="ml-2 text-sm text-gray-600">In Stock Only</span>
                  </label>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Products Grid */}
        <div className="lg:col-span-3">
          {/* Results Info */}
          <div className="flex items-center justify-between mb-6">
            <p className="text-sm text-gray-500">
              Showing {products.length} of {totalCount} products
            </p>
          </div>

          {error && (
            <div className="text-center py-12">
              <p className="text-gray-500">Error loading products. Please try again.</p>
            </div>
          )}

          {!loadingProducts && products.length === 0 && (
            <div className="text-center py-12">
              <ShoppingBagIcon className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No products found</h3>
              <p className="mt-1 text-sm text-gray-500">
                Try adjusting your search or filter criteria.
              </p>
            </div>
          )}

          {/* Products Grid */}
          {products.length > 0 && (
            <>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                {products.map((product) => (
                  <div
                    key={product.id}
                    className="group bg-white rounded-lg overflow-hidden shadow-sm hover:shadow-md transition-shadow duration-300 border"
                  >
                    <Link to={`/products/${product.slug}`}>
                      <div className="aspect-square bg-gray-200 overflow-hidden">
                        {product.display_image ? (
                          <img
                            src={product.display_image}
                            alt={product.name}
                            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                          />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center">
                            <ShoppingBagIcon className="w-12 h-12 text-gray-400" />
                          </div>
                        )}
                        {product.is_featured && (
                          <div className="absolute top-2 left-2 bg-yellow-400 text-yellow-900 px-2 py-1 rounded-full text-xs font-medium">
                            Featured
                          </div>
                        )}
                        {(!product.is_in_stock || product.stock_quantity === 0) && (
                          <div className="absolute top-2 right-2 bg-red-500 text-white px-2 py-1 rounded-full text-xs font-medium">
                            Out of Stock
                          </div>
                        )}
                      </div>
                    </Link>
                    
                    <div className="p-4">
                      <Link to={`/products/${product.slug}`}>
                        <h3 className="font-semibold text-gray-900 group-hover:text-primary-600 transition-colors duration-300 mb-2">
                          {product.name}
                        </h3>
                      </Link>
                      <p className="text-sm text-gray-500 mb-3 line-clamp-2">
                        {product.short_description || product.description}
                      </p>
                      
                      <div className="flex items-center justify-between mb-3">
                        <span className="text-lg font-bold text-primary-600">
                          ${product.price}
                        </span>
                        <div className="flex items-center text-sm text-gray-500">
                          <StarIcon className="w-4 h-4 text-yellow-400 fill-current" />
                          <span className="ml-1">
                            {product.average_rating || 0} ({product.review_count || 0})
                          </span>
                        </div>
                      </div>
                      
                      <Button 
                        fullWidth 
                        size="sm"
                        disabled={!product.is_in_stock && product.stock_quantity === 0}
                      >
                        {product.is_in_stock || product.stock_quantity > 0 ? 'Add to Cart' : 'Out of Stock'}
                      </Button>
                    </div>
                  </div>
                ))}
              </div>

              {/* Pagination */}
              {(hasNextPage || hasPreviousPage) && (
                <div className="mt-12 flex items-center justify-center space-x-4">
                  <Button
                    variant="outline"
                    disabled={!hasPreviousPage || loadingProducts}
                    onClick={() => updatePagination(pagination.page! - 1)}
                  >
                    Previous
                  </Button>
                  <span className="text-sm text-gray-500">
                    Page {pagination.page}
                  </span>
                  <Button
                    variant="outline"
                    disabled={!hasNextPage || loadingProducts}
                    onClick={() => updatePagination(pagination.page! + 1)}
                  >
                    Next
                  </Button>
                </div>
              )}
            </>
          )}

          {loadingProducts && products.length > 0 && (
            <div className="flex justify-center py-8">
              <LoadingSpinner />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};