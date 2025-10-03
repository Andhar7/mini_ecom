import React from 'react';
import { useAuth } from '../../context/AuthContext';
import { useCategories } from '../../hooks/useProducts';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import { Button } from '../../components/ui/Button';
import { TagIcon, PlusIcon } from '@heroicons/react/24/outline';
import { Navigate } from 'react-router-dom';

export const AdminCategories: React.FC = () => {
  const { user, isAuthenticated } = useAuth();
  const { data: categories, isLoading } = useCategories();

  if (!isAuthenticated || !user?.is_staff) {
    return <Navigate to="/" replace />;
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Category Management</h1>
          <p className="text-gray-600 mt-2">Organize your products into categories</p>
        </div>
        <Button>
          <PlusIcon className="w-4 h-4 mr-2" />
          Add Category
        </Button>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12">
          <LoadingSpinner size="lg" />
        </div>
      ) : (
        <>
          {/* Categories Grid */}
          {categories && categories.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {categories.map((category) => (
                <div key={category.id} className="bg-white rounded-lg shadow-md overflow-hidden">
                  {/* Category Image */}
                  <div className="aspect-w-16 aspect-h-9 bg-gray-200">
                    {category.image ? (
                      <img
                        src={category.image}
                        alt={category.name}
                        className="w-full h-48 object-cover"
                      />
                    ) : (
                      <div className="w-full h-48 flex items-center justify-center">
                        <TagIcon className="w-12 h-12 text-gray-400" />
                      </div>
                    )}
                  </div>

                  {/* Category Info */}
                  <div className="p-6">
                    <div className="flex items-start justify-between mb-2">
                      <h3 className="text-lg font-semibold text-gray-900">
                        {category.name}
                      </h3>
                      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                        category.is_active 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {category.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </div>

                    {category.description && (
                      <p className="text-gray-600 text-sm mb-3 line-clamp-2">
                        {category.description}
                      </p>
                    )}

                    <div className="flex items-center justify-between mb-4">
                      <div className="text-sm text-gray-500">
                        <span className="font-medium">{category.product_count}</span> products
                      </div>
                      <div className="text-sm text-gray-500">
                        {category.slug}
                      </div>
                    </div>

                    <div className="text-xs text-gray-400 mb-4">
                      Created: {new Date(category.created_at).toLocaleDateString()}
                      {category.updated_at !== category.created_at && (
                        <span className="block">
                          Updated: {new Date(category.updated_at).toLocaleDateString()}
                        </span>
                      )}
                    </div>

                    {/* Actions */}
                    <div className="flex space-x-2">
                      <Button size="sm" variant="outline" fullWidth>
                        Edit
                      </Button>
                      <Button size="sm" variant="danger" fullWidth>
                        Delete
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <TagIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <h2 className="text-2xl font-bold text-gray-900 mb-2">No Categories Found</h2>
              <p className="text-gray-600 mb-8">Start by creating your first category to organize products.</p>
              <Button>
                <PlusIcon className="w-4 h-4 mr-2" />
                Create Your First Category
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  );
};