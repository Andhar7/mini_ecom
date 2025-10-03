from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Category, Product, ProductImage


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category model."""

    full_name = serializers.ReadOnlyField()
    level = serializers.ReadOnlyField()
    product_count = serializers.SerializerMethodField()
    subcategories = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "parent",
            "image",
            "is_active",
            "sort_order",
            "created_at",
            "updated_at",
            "full_name",
            "level",
            "product_count",
            "subcategories",
        ]
        read_only_fields = ["slug", "created_at", "updated_at"]

    def get_product_count(self, obj):
        """Get count of active products in this category."""
        return obj.products.filter(status="active").count()

    def get_subcategories(self, obj):
        """Get active subcategories."""
        subcategories = obj.subcategories.filter(is_active=True)
        return CategorySerializer(subcategories, many=True, context=self.context).data


class ProductImageSerializer(serializers.ModelSerializer):
    """Serializer for ProductImage model."""

    class Meta:
        model = ProductImage
        fields = ["id", "image", "alt_text", "sort_order", "is_active", "created_at"]
        read_only_fields = ["created_at"]


class ProductListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for product lists."""

    category_name = serializers.CharField(source="category.name", read_only=True)
    owner_username = serializers.CharField(source="owner.username", read_only=True)
    discount_percentage = serializers.ReadOnlyField()
    is_in_stock = serializers.ReadOnlyField()
    is_low_stock = serializers.ReadOnlyField()
    display_image = serializers.ReadOnlyField()

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "sku",
            "short_description",
            "price",
            "compare_at_price",
            "discount_percentage",
            "stock_quantity",
            "is_featured",
            "status",
            "display_image",
            "view_count",
            "created_at",
            "updated_at",
            "category_name",
            "owner_username",
            "is_in_stock",
            "is_low_stock",
        ]


class ProductDetailSerializer(serializers.ModelSerializer):
    """Comprehensive serializer for product details."""

    category = CategorySerializer(read_only=True)
    category_id = serializers.IntegerField(
        write_only=True, required=False, allow_null=True
    )
    owner = serializers.StringRelatedField(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)

    # Computed fields
    discount_percentage = serializers.ReadOnlyField()
    profit_margin = serializers.ReadOnlyField()
    profit_percentage = serializers.ReadOnlyField()
    is_in_stock = serializers.ReadOnlyField()
    is_low_stock = serializers.ReadOnlyField()
    is_out_of_stock = serializers.ReadOnlyField()
    display_image = serializers.ReadOnlyField()
    dimensions = serializers.ReadOnlyField()

    # Tag handling
    tags_list = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "sku",
            "description",
            "short_description",
            "category",
            "category_id",
            "tags",
            "tags_list",
            "price",
            "compare_at_price",
            "cost_price",
            "stock_quantity",
            "low_stock_threshold",
            "track_inventory",
            "allow_backorder",
            "weight",
            "dimensions_length",
            "dimensions_width",
            "dimensions_height",
            "dimensions",
            "featured_image",
            "image_url",
            "display_image",
            "meta_title",
            "meta_description",
            "status",
            "is_featured",
            "is_digital",
            "requires_shipping",
            "view_count",
            "owner",
            "created_at",
            "updated_at",
            "published_at",
            "images",
            "discount_percentage",
            "profit_margin",
            "profit_percentage",
            "is_in_stock",
            "is_low_stock",
            "is_out_of_stock",
        ]
        read_only_fields = [
            "slug",
            "sku",
            "view_count",
            "created_at",
            "updated_at",
            "published_at",
        ]

    def get_tags_list(self, obj):
        """Convert comma-separated tags to list."""
        if obj.tags:
            return [tag.strip() for tag in obj.tags.split(",") if tag.strip()]
        return []

    def validate_category_id(self, value):
        """Validate category exists and is active."""
        if value is not None:
            try:
                category = Category.objects.get(id=value, is_active=True)
            except Category.DoesNotExist:
                raise serializers.ValidationError("Category not found or inactive.")
        return value

    def validate(self, attrs):
        """Cross-field validation."""
        compare_at_price = attrs.get("compare_at_price")
        price = attrs.get("price")
        cost_price = attrs.get("cost_price")

        # If updating, get current values for fields not being updated
        if self.instance:
            compare_at_price = compare_at_price or self.instance.compare_at_price
            price = price or self.instance.price
            cost_price = cost_price or self.instance.cost_price

        if compare_at_price and price and compare_at_price <= price:
            raise serializers.ValidationError(
                {
                    "compare_at_price": "Compare at price must be higher than regular price."
                }
            )

        if cost_price and price and cost_price > price:
            raise serializers.ValidationError(
                {"cost_price": "Cost price should not exceed selling price."}
            )

        return attrs

    def update(self, instance, validated_data):
        """Custom update to handle category assignment."""
        category_id = validated_data.pop("category_id", None)
        if category_id is not None:
            if category_id:
                instance.category = Category.objects.get(id=category_id)
            else:
                instance.category = None

        return super().update(instance, validated_data)


class ProductCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating products with required fields only."""

    category_id = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = Product
        fields = [
            "name",
            "description",
            "short_description",
            "category_id",
            "tags",
            "price",
            "compare_at_price",
            "cost_price",
            "stock_quantity",
            "low_stock_threshold",
            "track_inventory",
            "allow_backorder",
            "weight",
            "dimensions_length",
            "dimensions_width",
            "dimensions_height",
            "featured_image",
            "image_url",
            "meta_title",
            "meta_description",
            "status",
            "is_featured",
            "is_digital",
            "requires_shipping",
        ]

    def validate_category_id(self, value):
        """Validate category exists and is active."""
        if value is not None:
            try:
                Category.objects.get(id=value, is_active=True)
            except Category.DoesNotExist:
                raise serializers.ValidationError("Category not found or inactive.")
        return value

    def create(self, validated_data):
        """Custom create to handle category assignment."""
        category_id = validated_data.pop("category_id", None)
        product = Product.objects.create(**validated_data)

        if category_id:
            product.category = Category.objects.get(id=category_id)
            product.save()

        return product


class ProductStatsSerializer(serializers.Serializer):
    """Serializer for product statistics."""

    total_products = serializers.IntegerField()
    active_products = serializers.IntegerField()
    featured_products = serializers.IntegerField()
    out_of_stock = serializers.IntegerField()
    low_stock = serializers.IntegerField()
    total_value = serializers.DecimalField(max_digits=15, decimal_places=2)
    avg_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_views = serializers.IntegerField()
