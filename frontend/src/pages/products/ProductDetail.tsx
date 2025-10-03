import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { useProduct } from '../../hooks/useProducts';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import { Button } from '../../components/ui/Button';
import { ShoppingBagIcon, ArrowLeftIcon } from '@heroicons/react/24/outline';

export const ProductDetail: React.FC = () => {
  const { slug } = useParams<{ slug: string }>();
  const { data: product, isLoading, error } = useProduct(slug || '');

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="flex justify-center py-12">
          <LoadingSpinner size="lg" />
        </div>
      </div>
    );
  }

  if (error || !product) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="text-center py-12">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Product Not Found</h2>
          <p className="text-gray-600 mb-8">The product you're looking for doesn't exist.</p>
          <Link to="/products">
            <Button>
              <ArrowLeftIcon className="w-4 h-4 mr-2" />
              Back to Products
            </Button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Breadcrumb */}
      <nav className="mb-8">
        <ol className="flex items-center space-x-2 text-sm">
          <li><Link to="/" className="text-gray-500 hover:text-gray-900">Home</Link></li>
          <li className="text-gray-400">/</li>
          <li><Link to="/products" className="text-gray-500 hover:text-gray-900">Products</Link></li>
          <li className="text-gray-400">/</li>
          <li className="text-gray-900">{product.name}</li>
        </ol>
      </nav>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
        {/* Product Images */}
        <div className="space-y-4">
          <div className="aspect-square bg-gray-200 rounded-lg overflow-hidden">
            {product.display_image ? (
              <img
                src={product.display_image}
                alt={product.name}
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center">
                <ShoppingBagIcon className="w-24 h-24 text-gray-400" />
              </div>
            )}
          </div>
          
          {/* Additional Images */}
          {product.images && product.images.length > 0 && (
            <div className="grid grid-cols-4 gap-2">
              {product.images.map((img, index) => (
                <div key={img.id} className="aspect-square bg-gray-200 rounded-md overflow-hidden">
                  <img
                    src={img.image}
                    alt={img.alt_text || `Product image ${index + 1}`}
                    className="w-full h-full object-cover"
                  />
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Product Info */}
        <div className="space-y-6">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">{product.name}</h1>
            {product.category ? (
              <Link
                to={`/categories/${product.category.slug}`}
                className="text-primary-600 hover:text-primary-800 font-medium"
              >
                {product.category.full_name || product.category.name}
              </Link>
            ) : product.category_name ? (
              <span className="text-primary-600 font-medium">
                {product.category_name}
              </span>
            ) : null}
          </div>

          <div className="flex items-center space-x-4">
            <span className="text-4xl font-bold text-primary-600">${product.price}</span>
            {product.compare_at_price && (
              <div className="flex items-center space-x-2">
                <span className="text-lg text-gray-500 line-through">
                  ${product.compare_at_price}
                </span>
                {product.discount_percentage && (
                  <span className="px-2 py-1 bg-red-100 text-red-800 text-sm font-medium rounded-full">
                    {product.discount_percentage}% OFF
                  </span>
                )}
              </div>
            )}
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${
              product.is_in_stock || product.stock_quantity > 0 
                ? 'bg-green-100 text-green-800' 
                : 'bg-red-100 text-red-800'
            }`}>
              {product.is_in_stock || product.stock_quantity > 0 
                ? `${product.stock_quantity} in stock` 
                : 'Out of stock'
              }
            </span>
            {product.is_featured && (
              <span className="px-3 py-1 rounded-full text-sm font-medium bg-yellow-100 text-yellow-800">
                ⭐ Featured
              </span>
            )}
          </div>

          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Description</h3>
            <p className="text-gray-600 leading-relaxed">
              {product.description || product.short_description}
            </p>
          </div>

          {/* Add to Cart */}
          <div className="space-y-4">
            <Button
              size="lg"
              fullWidth
              disabled={!product.is_in_stock && product.stock_quantity === 0}
              className="py-4"
            >
              <ShoppingBagIcon className="w-5 h-5 mr-2" />
              {product.is_in_stock || product.stock_quantity > 0 ? 'Add to Cart' : 'Out of Stock'}
            </Button>
            
            <div className="grid grid-cols-2 gap-4">
              <Button variant="outline" size="lg">
                Add to Wishlist
              </Button>
              <Button variant="ghost" size="lg">
                Share
              </Button>
            </div>
          </div>

          {/* Product Details */}
          <div className="border-t pt-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Product Details</h3>
            <dl className="grid grid-cols-2 gap-4 text-sm">
              {product.category && (
                <div>
                  <dt className="font-medium text-gray-900">Category</dt>
                  <dd className="text-gray-600">{product.category.full_name || product.category.name}</dd>
                </div>
              )}
              <div>
                <dt className="font-medium text-gray-900">Stock</dt>
                <dd className="text-gray-600">{product.stock_quantity} units</dd>
              </div>
              {product.sku && (
                <div>
                  <dt className="font-medium text-gray-900">SKU</dt>
                  <dd className="text-gray-600">{product.sku}</dd>
                </div>
              )}
              <div>
                <dt className="font-medium text-gray-900">Status</dt>
                <dd className="text-gray-600 capitalize">{product.status}</dd>
              </div>
              <div>
                <dt className="font-medium text-gray-900">Added</dt>
                <dd className="text-gray-600">{new Date(product.created_at).toLocaleDateString()}</dd>
              </div>
              <div>
                <dt className="font-medium text-gray-900">Updated</dt>
                <dd className="text-gray-600">{new Date(product.updated_at).toLocaleDateString()}</dd>
              </div>
            </dl>
          </div>
        </div>
      </div>
    </div>
  );
};