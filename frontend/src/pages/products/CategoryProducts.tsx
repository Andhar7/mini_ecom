import React, { useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useProducts, useCategories, useProductFilters } from '../../hooks/useProducts';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import { Button } from '../../components/ui/Button';
import { ShoppingBagIcon, ArrowLeftIcon } from '@heroicons/react/24/outline';

export const CategoryProducts: React.FC = () => {
  const { slug } = useParams<{ slug: string }>();
  const { data: categories } = useCategories();
  const {
    filters,
    pagination,
    updateFilter,
    updatePagination,
    allParams
  } = useProductFilters();

  // Find the current category
  const currentCategory = categories?.find(cat => cat.slug === slug);

  // Set category filter when component mounts or slug changes
  useEffect(() => {
    if (slug && categories) {
      const categoryFromSlug = categories.find(cat => cat.slug === slug);
      if (categoryFromSlug && categoryFromSlug.id !== filters.category) {
        updateFilter('category', categoryFromSlug.id);
      }
    }
  }, [slug, categories, filters.category, updateFilter]);

  const { data: productsData, isLoading, error } = useProducts(allParams);

  if (!slug) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="text-center py-12">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Invalid Category</h2>
          <Link to="/categories">
            <Button>
              <ArrowLeftIcon className="w-4 h-4 mr-2" />
              Back to Categories
            </Button>
          </Link>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="flex justify-center py-12">
          <LoadingSpinner size="lg" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="text-center py-12">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Error Loading Products</h2>
          <p className="text-gray-600 mb-8">Please try again later.</p>
          <Link to="/categories">
            <Button>
              <ArrowLeftIcon className="w-4 h-4 mr-2" />
              Back to Categories
            </Button>
          </Link>
        </div>
      </div>
    );
  }

  const products = productsData?.results || [];
  const totalProducts = productsData?.count || 0;

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Breadcrumb */}
      <nav className="mb-8">
        <ol className="flex items-center space-x-2 text-sm">
          <li><Link to="/" className="text-gray-500 hover:text-gray-900">Home</Link></li>
          <li className="text-gray-400">/</li>
          <li><Link to="/categories" className="text-gray-500 hover:text-gray-900">Categories</Link></li>
          <li className="text-gray-400">/</li>
          <li className="text-gray-900">{currentCategory?.name || slug}</li>
        </ol>
      </nav>

      {/* Category Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              {currentCategory?.name || slug}
            </h1>
            {currentCategory?.description && (
              <p className="text-lg text-gray-600 mt-2">{currentCategory.description}</p>
            )}
          </div>
          <Link to="/categories">
            <Button variant="outline">
              <ArrowLeftIcon className="w-4 h-4 mr-2" />
              All Categories
            </Button>
          </Link>
        </div>
        
        <div className="text-sm text-gray-500">
          {totalProducts} {totalProducts === 1 ? 'product' : 'products'} found
        </div>
      </div>

      {/* Products Grid */}
      {products.length > 0 ? (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6 mb-8">
            {products.map((product) => (
              <div
                key={product.id}
                className="group bg-white rounded-lg overflow-hidden shadow-md hover:shadow-lg transition-shadow duration-300"
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
                  </div>
                  
                  <div className="p-4">
                    <h3 className="font-semibold text-gray-900 group-hover:text-primary-600 transition-colors duration-300 mb-2">
                      {product.name}
                    </h3>
                    <p className="text-sm text-gray-500 mb-3 line-clamp-2">
                      {product.short_description || product.description}
                    </p>
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-lg font-bold text-primary-600">
                        ${product.price}
                      </span>
                      <span className={`text-xs px-2 py-1 rounded-full ${
                        product.is_in_stock || product.stock_quantity > 0 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {product.is_in_stock || product.stock_quantity > 0 ? 'In Stock' : 'Out of Stock'}
                      </span>
                    </div>
                    {product.is_featured && (
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800 mb-2">
                        ⭐ Featured
                      </span>
                    )}
                  </div>
                </Link>
                
                <div className="px-4 pb-4">
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
          {productsData && productsData.count && productsData.count > (pagination.page_size || 12) && (
            <div className="flex justify-center space-x-2">
              <Button
                variant="outline"
                disabled={!productsData.previous}
                onClick={() => updatePagination((pagination.page || 1) - 1)}
              >
                Previous
              </Button>
              <span className="flex items-center px-4 py-2 text-sm text-gray-700">
                Page {pagination.page || 1}
              </span>
              <Button
                variant="outline"
                disabled={!productsData.next}
                onClick={() => updatePagination((pagination.page || 1) + 1)}
              >
                Next
              </Button>
            </div>
          )}
        </>
      ) : (
        <div className="text-center py-12">
          <ShoppingBagIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">No Products Found</h2>
          <p className="text-gray-600 mb-8">
            There are no products in this category yet.
          </p>
          <Link to="/categories">
            <Button>
              <ArrowLeftIcon className="w-4 h-4 mr-2" />
              Browse Other Categories
            </Button>
          </Link>
        </div>
      )}
    </div>
  );
};