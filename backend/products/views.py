from django.db import models
from django.db.models import Avg, Case, Count, F, IntegerField, Q, Sum, When
from django.shortcuts import get_object_or_404
from rest_framework import filters, generics, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import Category, Product, ProductImage
from .serializers import (
    CategorySerializer,
    ProductCreateSerializer,
    ProductDetailSerializer,
    ProductImageSerializer,
    ProductListSerializer,
    ProductStatsSerializer,
)


class StandardResultsSetPagination(PageNumberPagination):
    """Custom pagination class for consistent pagination across views."""

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Custom permission to only allow owners of an object to edit it."""

    def has_object_permission(self, request, view, obj):
        # Read permissions for any request (GET, HEAD, OPTIONS)
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions only to the owner
        return obj.owner == request.user


class ProductFilter:
    """Custom filter backend for advanced product filtering."""

    @staticmethod
    def filter_queryset(request, queryset):
        """Apply custom filters to the queryset."""

        # Category filter
        category_id = request.query_params.get("category")
        if category_id:
            try:
                category = Category.objects.get(id=category_id, is_active=True)
                # Include products from subcategories
                category_ids = [category.id]
                category_ids.extend(category.subcategories.values_list("id", flat=True))
                queryset = queryset.filter(category__id__in=category_ids)
            except Category.DoesNotExist:
                pass

        # Price range filter
        min_price = request.query_params.get("min_price")
        max_price = request.query_params.get("max_price")
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        # Stock filter
        stock_status = request.query_params.get("stock_status")
        if stock_status == "in_stock":
            queryset = queryset.filter(
                Q(track_inventory=False) | Q(stock_quantity__gt=0)
            )
        elif stock_status == "low_stock":
            queryset = queryset.filter(
                track_inventory=True,
                stock_quantity__gt=0,
                stock_quantity__lte=F("low_stock_threshold"),
            )
        elif stock_status == "out_of_stock":
            queryset = queryset.filter(track_inventory=True, stock_quantity=0)

        # Featured filter
        is_featured = request.query_params.get("featured")
        if is_featured == "true":
            queryset = queryset.filter(is_featured=True)
        elif is_featured == "false":
            queryset = queryset.filter(is_featured=False)

        # Status filter
        status_filter = request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Tags filter
        tags = request.query_params.get("tags")
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",")]
            tag_queries = Q()
            for tag in tag_list:
                tag_queries |= Q(tags__icontains=tag)
            queryset = queryset.filter(tag_queries)

        return queryset


class CategoryViewSet(ModelViewSet):
    """ViewSet for managing categories."""

    queryset = Category.objects.filter(is_active=True).prefetch_related("subcategories")
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "sort_order", "created_at"]
    ordering = ["sort_order", "name"]
    lookup_field = "slug"

    def get_queryset(self):
        """Filter categories based on user permissions."""
        queryset = super().get_queryset()

        # If authenticated, show all active categories
        # If not authenticated, show only categories with active products
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(products__status="active").distinct()

        # Filter by parent category
        parent_id = self.request.query_params.get("parent")
        if parent_id:
            if parent_id == "null" or parent_id == "0":
                queryset = queryset.filter(parent__isnull=True)
            else:
                queryset = queryset.filter(parent_id=parent_id)

        return queryset

    @action(detail=True, methods=["get"])
    def products(self, request, slug=None):
        """Get products for a specific category."""
        category = self.get_object()

        # Get products from this category and its subcategories
        category_ids = [category.id]
        category_ids.extend(category.subcategories.values_list("id", flat=True))

        products = (
            Product.objects.filter(category__id__in=category_ids, status="active")
            .select_related("category", "owner")
            .prefetch_related("images")
        )

        # Apply additional filters
        products = ProductFilter.filter_queryset(request, products)

        # Pagination
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(products, request)

        if page is not None:
            serializer = ProductListSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = ProductListSerializer(products, many=True)
        return Response(serializer.data)


class ProductViewSet(ModelViewSet):
    """Professional ViewSet for managing products."""

    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "description", "short_description", "tags", "sku"]
    ordering_fields = [
        "name",
        "price",
        "created_at",
        "updated_at",
        "view_count",
        "stock_quantity",
    ]
    ordering = ["-created_at"]
    pagination_class = StandardResultsSetPagination
    lookup_field = "slug"

    def get_queryset(self):
        """Get queryset based on user permissions and context."""
        user = self.request.user

        # Base queryset with optimizations
        queryset = Product.objects.select_related("category", "owner").prefetch_related(
            "images"
        )

        # Filter based on action
        if self.action == "list":
            # For list view, show user's own products
            queryset = queryset.filter(owner=user)
        elif self.action in ["retrieve", "update", "partial_update", "destroy"]:
            # For detail operations, filter by owner
            queryset = queryset.filter(owner=user)

        # Apply custom filters
        queryset = ProductFilter.filter_queryset(self.request, queryset)

        return queryset

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "list":
            return ProductListSerializer
        elif self.action == "create":
            return ProductCreateSerializer
        else:
            return ProductDetailSerializer

    def perform_create(self, serializer):
        """Associate product with authenticated user."""
        serializer.save(owner=self.request.user)

    def create(self, request, *args, **kwargs):
        """Create product and return detailed response."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save(owner=request.user)

        # Return detailed response with id and slug
        detail_serializer = ProductDetailSerializer(
            instance, context={"request": request}
        )
        headers = self.get_success_headers(detail_serializer.data)
        return Response(
            detail_serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def retrieve(self, request, *args, **kwargs):
        """Retrieve product and increment view count."""
        instance = self.get_object()

        # Increment view count (atomic operation)
        instance.increment_view_count()

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def duplicate(self, request, slug=None):
        """Create a duplicate of the product."""
        original = self.get_object()

        # Create duplicate
        duplicate_data = {
            "name": f"{original.name} (Copy)",
            "description": original.description,
            "short_description": original.short_description,
            "category_id": original.category.id if original.category else None,
            "tags": original.tags,
            "price": original.price,
            "compare_at_price": original.compare_at_price,
            "cost_price": original.cost_price,
            "stock_quantity": 0,  # Start with 0 stock
            "low_stock_threshold": original.low_stock_threshold,
            "track_inventory": original.track_inventory,
            "allow_backorder": original.allow_backorder,
            "weight": original.weight,
            "dimensions_length": original.dimensions_length,
            "dimensions_width": original.dimensions_width,
            "dimensions_height": original.dimensions_height,
            "is_digital": original.is_digital,
            "requires_shipping": original.requires_shipping,
            "status": Product.Status.DRAFT,  # Start as draft
        }

        serializer = ProductCreateSerializer(data=duplicate_data)
        if serializer.is_valid():
            duplicate = serializer.save(owner=request.user)
            response_serializer = ProductDetailSerializer(duplicate)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["patch"])
    def update_stock(self, request, slug=None):
        """Update product stock quantity."""
        product = self.get_object()

        try:
            new_quantity = int(request.data.get("stock_quantity", 0))
            if new_quantity < 0:
                return Response(
                    {"error": "Stock quantity cannot be negative"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            product.stock_quantity = new_quantity
            product.save(update_fields=["stock_quantity"])

            serializer = ProductDetailSerializer(product)
            return Response(serializer.data)

        except (ValueError, TypeError):
            return Response(
                {"error": "Invalid stock quantity"}, status=status.HTTP_400_BAD_REQUEST
            )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def product_stats(request):
    """Get comprehensive product statistics for the authenticated user."""

    user_products = Product.objects.filter(owner=request.user)

    stats = user_products.aggregate(
        total_products=Count("id"),
        active_products=Count(
            Case(When(status="active", then=1), output_field=IntegerField())
        ),
        featured_products=Count(
            Case(When(is_featured=True, then=1), output_field=IntegerField())
        ),
        out_of_stock=Count(
            Case(
                When(track_inventory=True, stock_quantity=0, then=1),
                output_field=IntegerField(),
            )
        ),
        low_stock=Count(
            Case(
                When(
                    track_inventory=True,
                    stock_quantity__gt=0,
                    stock_quantity__lte=F("low_stock_threshold"),
                    then=1,
                ),
                output_field=IntegerField(),
            )
        ),
        total_value=Sum("price") or 0,
        avg_price=Avg("price") or 0,
        total_views=Sum("view_count") or 0,
    )

    serializer = ProductStatsSerializer(stats)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def low_stock_alerts(request):
    """Get products that are running low on stock."""

    low_stock_products = Product.objects.filter(
        owner=request.user,
        track_inventory=True,
        stock_quantity__gt=0,
        stock_quantity__lte=F("low_stock_threshold"),
        status="active",
    ).select_related("category")

    serializer = ProductListSerializer(low_stock_products, many=True)
    return Response({"count": low_stock_products.count(), "products": serializer.data})


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def public_products(request):
    """Public endpoint for browsing active products."""

    products = (
        Product.objects.filter(status="active")
        .select_related("category", "owner")
        .prefetch_related("images")
    )

    # Apply filters
    products = ProductFilter.filter_queryset(request, products)

    # Sort by featured first, then by popularity (view count)
    sort_by = request.query_params.get("sort", "featured")
    if sort_by == "featured":
        products = products.order_by("-is_featured", "-view_count")
    elif sort_by == "price_low":
        products = products.order_by("price")
    elif sort_by == "price_high":
        products = products.order_by("-price")
    elif sort_by == "newest":
        products = products.order_by("-created_at")
    elif sort_by == "popular":
        products = products.order_by("-view_count")
    else:
        products = products.order_by("-created_at")

    # Pagination
    paginator = StandardResultsSetPagination()
    page = paginator.paginate_queryset(products, request)

    if page is not None:
        serializer = ProductListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    serializer = ProductListSerializer(products, many=True)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def public_product_detail(request, slug):
    """Public endpoint for viewing product details."""

    product = get_object_or_404(
        Product.objects.select_related("category", "owner").prefetch_related("images"),
        slug=slug,
        status="active",
    )

    # Increment view count
    product.increment_view_count()

    serializer = ProductDetailSerializer(product)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def featured_products(request):
    """Get featured products for homepage/promotions."""

    products = (
        Product.objects.filter(status="active", is_featured=True)
        .select_related("category", "owner")
        .prefetch_related("images")[:12]
    )

    serializer = ProductListSerializer(products, many=True)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def search_products(request):
    """Advanced product search endpoint."""

    query = request.query_params.get("q", "").strip()
    if not query:
        return Response(
            {"error": "Search query is required"}, status=status.HTTP_400_BAD_REQUEST
        )

    # Search in multiple fields
    products = (
        Product.objects.filter(
            Q(name__icontains=query)
            | Q(description__icontains=query)
            | Q(short_description__icontains=query)
            | Q(tags__icontains=query)
            | Q(category__name__icontains=query),
            status="active",
        )
        .select_related("category", "owner")
        .prefetch_related("images")
        .distinct()
    )

    # Apply additional filters
    products = ProductFilter.filter_queryset(request, products)

    # Order by relevance (you could implement a more sophisticated scoring system)
    products = products.order_by("-is_featured", "-view_count")

    # Pagination
    paginator = StandardResultsSetPagination()
    page = paginator.paginate_queryset(products, request)

    if page is not None:
        serializer = ProductListSerializer(page, many=True)
        response_data = paginator.get_paginated_response(serializer.data).data
        response_data["query"] = query
        return Response(response_data)

    serializer = ProductListSerializer(products, many=True)
    return Response(
        {"query": query, "count": products.count(), "results": serializer.data}
    )
