import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useProductStats } from '../../hooks/useProducts';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import { Button } from '../../components/ui/Button';
import { 
  ShoppingBagIcon, 
  TagIcon, 
  ChartBarIcon,
  ExclamationTriangleIcon 
} from '@heroicons/react/24/outline';
import { Navigate } from 'react-router-dom';

export const AdminDashboard: React.FC = () => {
  const { user, isAuthenticated } = useAuth();
  const { data: stats, isLoading } = useProductStats();

  if (!isAuthenticated || !user?.is_staff) {
    return <Navigate to="/" replace />;
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Admin Dashboard</h1>
        <p className="text-gray-600 mt-2">Manage your e-commerce store</p>
      </div>

      {/* Stats Cards */}
      {isLoading ? (
        <div className="flex justify-center py-12">
          <LoadingSpinner size="lg" />
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white p-6 rounded-lg shadow-md">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Products</p>
                <p className="text-3xl font-bold text-gray-900">{stats?.total_products || 0}</p>
              </div>
              <ShoppingBagIcon className="w-12 h-12 text-primary-600" />
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-md">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Active Products</p>
                <p className="text-3xl font-bold text-green-600">{stats?.active_products || 0}</p>
              </div>
              <ChartBarIcon className="w-12 h-12 text-green-600" />
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-md">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Categories</p>
                <p className="text-3xl font-bold text-blue-600">{stats?.total_categories || 0}</p>
              </div>
              <TagIcon className="w-12 h-12 text-blue-600" />
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-md">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Low Stock</p>
                <p className="text-3xl font-bold text-red-600">{stats?.low_stock_products || 0}</p>
              </div>
              <ExclamationTriangleIcon className="w-12 h-12 text-red-600" />
            </div>
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Product Management</h3>
          <p className="text-gray-600 mb-4">Add, edit, and manage your products</p>
          <Link to="/admin/products">
            <Button fullWidth>
              <ShoppingBagIcon className="w-4 h-4 mr-2" />
              Manage Products
            </Button>
          </Link>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Category Management</h3>
          <p className="text-gray-600 mb-4">Organize your products into categories</p>
          <Link to="/admin/categories">
            <Button fullWidth>
              <TagIcon className="w-4 h-4 mr-2" />
              Manage Categories
            </Button>
          </Link>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Analytics</h3>
          <p className="text-gray-600 mb-4">View store performance and statistics</p>
          <Button fullWidth variant="outline" disabled>
            <ChartBarIcon className="w-4 h-4 mr-2" />
            Coming Soon
          </Button>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Store Overview</h2>
        
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className="font-medium text-gray-900 mb-2">Product Statistics</h3>
              <ul className="space-y-2 text-sm">
                <li className="flex justify-between">
                  <span className="text-gray-600">Total Products:</span>
                  <span className="font-medium">{stats.total_products}</span>
                </li>
                <li className="flex justify-between">
                  <span className="text-gray-600">Active Products:</span>
                  <span className="font-medium text-green-600">{stats.active_products}</span>
                </li>
                <li className="flex justify-between">
                  <span className="text-gray-600">Featured Products:</span>
                  <span className="font-medium text-yellow-600">{stats.featured_products}</span>
                </li>
                <li className="flex justify-between">
                  <span className="text-gray-600">Low Stock Products:</span>
                  <span className="font-medium text-red-600">{stats.low_stock_products}</span>
                </li>
              </ul>
            </div>

            <div>
              <h3 className="font-medium text-gray-900 mb-2">System Information</h3>
              <ul className="space-y-2 text-sm">
                <li className="flex justify-between">
                  <span className="text-gray-600">Total Categories:</span>
                  <span className="font-medium">{stats.total_categories}</span>
                </li>
                <li className="flex justify-between">
                  <span className="text-gray-600">Average Price:</span>
                  <span className="font-medium">${stats.average_price}</span>
                </li>
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};