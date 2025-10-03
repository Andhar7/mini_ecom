import React from 'react';
import { Link } from 'react-router-dom';
import { useCategories } from '../../hooks/useProducts';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import { ShoppingBagIcon } from '@heroicons/react/24/outline';

export const Categories: React.FC = () => {
  const { data: categories, isLoading, error } = useCategories();

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
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Error Loading Categories</h2>
          <p className="text-gray-600">Please try again later.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">Shop by Category</h1>
        <p className="text-lg text-gray-600 max-w-2xl mx-auto">
          Explore our wide range of categories to find exactly what you're looking for.
        </p>
      </div>

      {/* Categories Grid */}
      {categories && categories.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {categories.map((category) => (
            <Link
              key={category.id}
              to={`/categories/${category.slug}`}
              className="group relative bg-white rounded-lg overflow-hidden shadow-md hover:shadow-lg transition-shadow duration-300"
            >
              {/* Category Image */}
              <div className="aspect-square bg-gray-200 group-hover:bg-gray-300 transition-colors duration-300">
                {category.image ? (
                  <img
                    src={category.image}
                    alt={category.name}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center">
                    <ShoppingBagIcon className="w-16 h-16 text-gray-400 group-hover:text-gray-500 transition-colors duration-300" />
                  </div>
                )}
              </div>

              {/* Category Info */}
              <div className="p-6">
                <h3 className="text-xl font-semibold text-gray-900 group-hover:text-primary-600 transition-colors duration-300 mb-2">
                  {category.name}
                </h3>
                
                {category.description && (
                  <p className="text-gray-600 text-sm mb-3 line-clamp-2">
                    {category.description}
                  </p>
                )}
                
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-500">
                    {category.product_count} {category.product_count === 1 ? 'product' : 'products'}
                  </span>
                  <span className="text-primary-600 font-medium group-hover:text-primary-700 transition-colors duration-300">
                    Browse →
                  </span>
                </div>
              </div>

              {/* Active indicator */}
              {category.is_active && (
                <div className="absolute top-3 right-3">
                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                    Active
                  </span>
                </div>
              )}
            </Link>
          ))}
        </div>
      ) : (
        <div className="text-center py-12">
          <ShoppingBagIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">No Categories Found</h2>
          <p className="text-gray-600">Categories will appear here once they are added.</p>
        </div>
      )}

      {/* Stats */}
      {categories && categories.length > 0 && (
        <div className="mt-16 bg-gray-100 rounded-lg p-8">
          <div className="text-center">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Browse Our Collection</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <div>
                <div className="text-3xl font-bold text-primary-600">{categories.length}</div>
                <div className="text-gray-600">Categories</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-primary-600">
                  {categories.reduce((total, cat) => total + cat.product_count, 0)}
                </div>
                <div className="text-gray-600">Total Products</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-primary-600">
                  {categories.filter(cat => cat.is_active).length}
                </div>
                <div className="text-gray-600">Active Categories</div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};