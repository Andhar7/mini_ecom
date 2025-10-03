from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

# Create router for ViewSets
router = DefaultRouter()
router.register(r"categories", views.CategoryViewSet, basename="category")
router.register(r"products", views.ProductViewSet, basename="product")

urlpatterns = [
    # ViewSet URLs
    path("", include(router.urls)),
    # Additional API endpoints
    path("stats/", views.product_stats, name="product-stats"),
    path("low-stock-alerts/", views.low_stock_alerts, name="low-stock-alerts"),
    # Public endpoints (no authentication required)
    path("public/products/", views.public_products, name="public-products"),
    path(
        "public/products/<slug:slug>/",
        views.public_product_detail,
        name="public-product-detail",
    ),
    path("public/featured/", views.featured_products, name="featured-products"),
    path("public/search/", views.search_products, name="search-products"),
]
