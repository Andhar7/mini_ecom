import uuid
from decimal import Decimal
from typing import Optional

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _


class CategoryManager(models.Manager):
    """Custom manager for Category with utility methods."""

    def active_categories(self):
        """Get all active categories."""
        return self.filter(is_active=True)

    def get_by_slug(self, slug: str):
        """Get category by slug."""
        try:
            return self.get(slug=slug, is_active=True)
        except self.model.DoesNotExist:
            return None


class Category(models.Model):
    """
    Product category model for organizing products.

    Features:
    - Hierarchical categories (parent/child)
    - SEO-friendly slugs
    - Active/inactive status
    - Professional metadata
    """

    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_("Category Name"),
        help_text=_("The name of the product category"),
    )
    slug = models.SlugField(
        max_length=120,
        unique=True,
        blank=True,
        verbose_name=_("URL Slug"),
        help_text=_("SEO-friendly URL slug (auto-generated from name)"),
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Description"),
        help_text=_("Category description for SEO and user information"),
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="subcategories",
        verbose_name=_("Parent Category"),
        help_text=_("Parent category for hierarchical structure"),
    )
    image = models.ImageField(
        upload_to="categories/",
        null=True,
        blank=True,
        verbose_name=_("Category Image"),
        help_text=_("Category banner or icon image"),
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active"),
        help_text=_("Whether this category is active and visible"),
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Sort Order"),
        help_text=_("Order for displaying categories"),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = CategoryManager()

    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")
        ordering = ["sort_order", "name"]
        indexes = [
            models.Index(fields=["is_active", "sort_order"]),
            models.Index(fields=["slug"]),
            models.Index(fields=["parent"]),
        ]

    def clean(self):
        """Model validation."""
        if self.parent == self:
            raise ValidationError(_("Category cannot be its own parent"))

        # Check for circular references
        if self.parent:
            current = self.parent
            while current:
                if current == self:
                    raise ValidationError(
                        _("Circular reference detected in category hierarchy")
                    )
                current = current.parent

    def save(self, *args, **kwargs):
        """Override save to auto-generate slug."""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def full_name(self) -> str:
        """Get full category path name."""
        if self.parent:
            return f"{self.parent.full_name} > {self.name}"
        return self.name

    @property
    def level(self) -> int:
        """Get category depth level."""
        level = 0
        current = self.parent
        while current:
            level += 1
            current = current.parent
        return level

    def get_absolute_url(self):
        """Get category URL."""
        return reverse("category_detail", kwargs={"slug": self.slug})

    def __str__(self):
        return self.full_name


class ProductManager(models.Manager):
    """Custom manager for Product with utility methods."""

    def active_products(self):
        """Get all active products."""
        return self.filter(status="active", stock_quantity__gt=0)

    def featured_products(self):
        """Get featured products."""
        return self.filter(status="active", is_featured=True)

    def in_stock(self):
        """Get products that are in stock."""
        return self.filter(status="active", stock_quantity__gt=0)

    def out_of_stock(self):
        """Get products that are out of stock."""
        return self.filter(status="active", stock_quantity=0)

    def by_category(self, category):
        """Get products by category."""
        return self.filter(category=category, status="active")

    def by_price_range(self, min_price: Decimal = None, max_price: Decimal = None):
        """Get products within price range."""
        queryset = self.filter(status="active")
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        return queryset

    def popular_products(self, limit: int = 10):
        """Get popular products based on views."""
        return self.filter(status="active").order_by("-view_count")[:limit]


class Product(models.Model):
    """
    Professional e-commerce product model.

    Features:
    - Comprehensive product information
    - SEO optimization with slugs and meta fields
    - Inventory management
    - Professional pricing with discounts
    - Image management
    - Analytics tracking
    - Status management
    """

    # Product Status Choices
    class Status(models.TextChoices):
        DRAFT = "draft", _("Draft")
        ACTIVE = "active", _("Active")
        INACTIVE = "inactive", _("Inactive")
        DISCONTINUED = "discontinued", _("Discontinued")

    # Core Information
    name = models.CharField(
        max_length=200,
        verbose_name=_("Product Name"),
        help_text=_("The name of the product"),
    )
    slug = models.SlugField(
        max_length=220,
        unique=True,
        blank=True,
        verbose_name=_("URL Slug"),
        help_text=_("SEO-friendly URL slug (auto-generated from name)"),
    )
    sku = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        verbose_name=_("SKU"),
        help_text=_("Stock Keeping Unit - unique product identifier"),
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Description"),
        help_text=_("Detailed product description"),
    )
    short_description = models.CharField(
        max_length=300,
        blank=True,
        verbose_name=_("Short Description"),
        help_text=_("Brief product summary for listings"),
    )

    # Categorization
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
        verbose_name=_("Category"),
        help_text=_("Product category"),
    )
    tags = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=_("Tags"),
        help_text=_("Comma-separated tags for search and filtering"),
    )

    # Pricing
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name=_("Price"),
        help_text=_("Product price in the default currency"),
    )
    compare_at_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name=_("Compare At Price"),
        help_text=_("Original price for showing discounts"),
    )
    cost_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name=_("Cost Price"),
        help_text=_("Cost price for profit calculations (internal use)"),
    )

    # Inventory
    stock_quantity = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Stock Quantity"),
        help_text=_("Number of items in stock"),
    )
    low_stock_threshold = models.PositiveIntegerField(
        default=5,
        verbose_name=_("Low Stock Threshold"),
        help_text=_("Alert when stock falls below this number"),
    )
    track_inventory = models.BooleanField(
        default=True,
        verbose_name=_("Track Inventory"),
        help_text=_("Whether to track inventory for this product"),
    )
    allow_backorder = models.BooleanField(
        default=False,
        verbose_name=_("Allow Backorder"),
        help_text=_("Allow orders when out of stock"),
    )

    # Physical Properties
    weight = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name=_("Weight (kg)"),
        help_text=_("Product weight in kilograms"),
    )
    dimensions_length = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name=_("Length (cm)"),
        help_text=_("Product length in centimeters"),
    )
    dimensions_width = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name=_("Width (cm)"),
        help_text=_("Product width in centimeters"),
    )
    dimensions_height = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name=_("Height (cm)"),
        help_text=_("Product height in centimeters"),
    )

    # Images
    featured_image = models.ImageField(
        upload_to="products/",
        null=True,
        blank=True,
        verbose_name=_("Featured Image"),
        help_text=_("Main product image"),
    )
    image_url = models.URLField(
        blank=True,
        null=True,
        verbose_name=_("Image URL"),
        help_text=_("External image URL (fallback if no featured image)"),
    )

    # SEO
    meta_title = models.CharField(
        max_length=70,
        blank=True,
        verbose_name=_("Meta Title"),
        help_text=_("SEO meta title (leave blank to use product name)"),
    )
    meta_description = models.CharField(
        max_length=160,
        blank=True,
        verbose_name=_("Meta Description"),
        help_text=_("SEO meta description"),
    )

    # Status and Features
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        verbose_name=_("Status"),
        help_text=_("Product status"),
    )
    is_featured = models.BooleanField(
        default=False,
        verbose_name=_("Featured"),
        help_text=_("Mark as featured product"),
    )
    is_digital = models.BooleanField(
        default=False,
        verbose_name=_("Digital Product"),
        help_text=_("Whether this is a digital product (no shipping)"),
    )
    requires_shipping = models.BooleanField(
        default=True,
        verbose_name=_("Requires Shipping"),
        help_text=_("Whether this product requires shipping"),
    )

    # Analytics
    view_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_("View Count"),
        help_text=_("Number of times this product was viewed"),
    )

    # Relationships
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="products",
        verbose_name=_("Owner"),
        help_text=_("The user who owns this product"),
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Published At"),
        help_text=_("When the product was first published"),
    )

    objects = ProductManager()

    class Meta:
        verbose_name = _("Product")
        verbose_name_plural = _("Products")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "is_featured"]),
            models.Index(fields=["category", "status"]),
            models.Index(fields=["slug"]),
            models.Index(fields=["sku"]),
            models.Index(fields=["price"]),
            models.Index(fields=["stock_quantity"]),
            models.Index(fields=["view_count"]),
            models.Index(fields=["created_at"]),
        ]

    def clean(self):
        """Model validation."""
        if self.compare_at_price and self.compare_at_price <= self.price:
            raise ValidationError(
                _("Compare at price must be higher than regular price")
            )

        if self.cost_price and self.cost_price > self.price:
            raise ValidationError(_("Cost price should not exceed selling price"))

        if not self.track_inventory and self.stock_quantity > 0:
            raise ValidationError(
                _("Stock quantity should be 0 when inventory tracking is disabled")
            )

    def save(self, *args, **kwargs):
        """Override save to handle auto-generation and publishing."""
        # Auto-generate slug
        if not self.slug:
            self.slug = slugify(self.name)

        # Auto-generate SKU
        if not self.sku:
            self.sku = f"PRD-{uuid.uuid4().hex[:8].upper()}"

        # Set published_at when first published
        if self.status == self.Status.ACTIVE and not self.published_at:
            self.published_at = timezone.now()

        # Set meta_title if empty
        if not self.meta_title:
            self.meta_title = self.name[:70]

        super().save(*args, **kwargs)

    # Properties and utility methods
    @property
    def is_active(self) -> bool:
        """Check if product is active."""
        return self.status == self.Status.ACTIVE

    @property
    def is_in_stock(self) -> bool:
        """Check if product is in stock."""
        if not self.track_inventory:
            return True
        return self.stock_quantity > 0 or self.allow_backorder

    @property
    def is_low_stock(self) -> bool:
        """Check if product is low in stock."""
        if not self.track_inventory:
            return False
        return 0 < self.stock_quantity <= self.low_stock_threshold

    @property
    def is_out_of_stock(self) -> bool:
        """Check if product is out of stock."""
        if not self.track_inventory:
            return False
        return self.stock_quantity == 0

    @property
    def discount_percentage(self) -> Optional[int]:
        """Calculate discount percentage."""
        if self.compare_at_price and self.compare_at_price > self.price:
            discount = (self.compare_at_price - self.price) / self.compare_at_price
            return int(discount * 100)
        return None

    @property
    def profit_margin(self) -> Optional[Decimal]:
        """Calculate profit margin."""
        if self.cost_price:
            return self.price - self.cost_price
        return None

    @property
    def profit_percentage(self) -> Optional[int]:
        """Calculate profit margin percentage."""
        if self.cost_price and self.cost_price > 0:
            profit = (self.price - self.cost_price) / self.cost_price
            return int(profit * 100)
        return None

    @property
    def display_image(self) -> str:
        """Get display image URL."""
        if self.featured_image:
            return self.featured_image.url
        elif self.image_url:
            return self.image_url
        return "https://picsum.photos/seed/apitest/300/200"  # Fallback

    @property
    def dimensions(self) -> Optional[str]:
        """Get formatted dimensions string."""
        if all([self.dimensions_length, self.dimensions_width, self.dimensions_height]):
            return f"{self.dimensions_length} × {self.dimensions_width} × {self.dimensions_height} cm"
        return None

    def get_absolute_url(self):
        """Get product URL."""
        return reverse("product_detail", kwargs={"slug": self.slug})

    def increment_view_count(self):
        """Increment view count atomically."""
        Product.objects.filter(pk=self.pk).update(view_count=models.F("view_count") + 1)
        self.refresh_from_db(fields=["view_count"])

    def reduce_stock(self, quantity: int) -> bool:
        """Reduce stock quantity safely."""
        if not self.track_inventory:
            return True

        if self.stock_quantity >= quantity:
            self.stock_quantity -= quantity
            self.save(update_fields=["stock_quantity"])
            return True
        return False

    def increase_stock(self, quantity: int):
        """Increase stock quantity."""
        if self.track_inventory:
            self.stock_quantity += quantity
            self.save(update_fields=["stock_quantity"])

    def __str__(self):
        return f"{self.name} ({self.sku})"


class ProductImage(models.Model):
    """
    Additional product images model.

    Allows multiple images per product for galleries.
    """

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name=_("Product"),
    )
    image = models.ImageField(upload_to="products/gallery/", verbose_name=_("Image"))
    alt_text = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("Alt Text"),
        help_text=_("Alternative text for accessibility"),
    )
    sort_order = models.PositiveIntegerField(default=0, verbose_name=_("Sort Order"))
    is_active = models.BooleanField(default=True, verbose_name=_("Active"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Product Image")
        verbose_name_plural = _("Product Images")
        ordering = ["sort_order", "created_at"]
        indexes = [
            models.Index(fields=["product", "is_active", "sort_order"]),
        ]

    def __str__(self):
        return f"Image for {self.product.name}"
