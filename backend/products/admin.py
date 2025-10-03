from decimal import Decimal

from django.contrib import admin
from django.db.models import Avg, Count, Q, Sum
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from .models import Category, Product, ProductImage


class ProductImageInline(admin.TabularInline):
    """Inline admin for ProductImage."""

    model = ProductImage
    extra = 1
    readonly_fields = ("image_preview", "created_at")
    fields = (
        "image",
        "image_preview",
        "alt_text",
        "sort_order",
        "is_active",
        "created_at",
    )
    ordering = ["sort_order"]

    def image_preview(self, obj):
        """Display image preview."""
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 100px; max-height: 100px; border-radius: 5px;" />',
                obj.image.url,
            )
        return "-"

    image_preview.short_description = _("Preview")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Professional admin interface for Category."""

    list_display = [
        "name_with_level",
        "slug",
        "status_display",
        "product_count",
        "sort_order",
        "created_at",
        "updated_at",
    ]
    list_filter = [
        "is_active",
        "created_at",
        "updated_at",
        ("parent", admin.RelatedOnlyFieldListFilter),
    ]
    search_fields = ["name", "description", "slug"]
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = [
        "created_at",
        "updated_at",
        "product_count_display",
        "category_tree_display",
        "full_name_display",
        "level_display",
    ]
    ordering = ["sort_order", "name"]

    fieldsets = (
        (_("Basic Information"), {"fields": ("name", "slug", "description")}),
        (
            _("Hierarchy"),
            {
                "fields": (
                    "parent",
                    "category_tree_display",
                    "full_name_display",
                    "level_display",
                )
            },
        ),
        (_("Media"), {"fields": ("image",)}),
        (_("Settings"), {"fields": ("is_active", "sort_order")}),
        (
            _("Statistics"),
            {"fields": ("product_count_display",), "classes": ("collapse",)},
        ),
        (
            _("System Information"),
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    actions = ["activate_categories", "deactivate_categories", "reset_sort_order"]

    def get_queryset(self, request):
        """Optimize queryset with annotations."""
        return (
            super()
            .get_queryset(request)
            .annotate(product_count=Count("products"))
            .select_related("parent")
        )

    def name_with_level(self, obj):
        """Display category name with visual hierarchy level."""
        level_indicator = "├─ " * obj.level if obj.level > 0 else ""
        active_badge = "✓" if obj.is_active else "✗"
        color = "#28a745" if obj.is_active else "#dc3545"

        return format_html(
            '<span style="font-family: monospace;">{}</span>{} '
            '<span style="color: {}; font-weight: bold;">{}</span>',
            level_indicator,
            obj.name,
            color,
            active_badge,
        )

    name_with_level.short_description = _("Category")
    name_with_level.admin_order_field = "name"

    def status_display(self, obj):
        """Display category status with color coding."""
        if obj.is_active:
            return format_html(
                '<span style="color: #28a745; font-weight: bold;">● Active</span>'
            )
        else:
            return format_html(
                '<span style="color: #dc3545; font-weight: bold;">● Inactive</span>'
            )

    status_display.short_description = _("Status")
    status_display.admin_order_field = "is_active"

    def product_count(self, obj):
        """Display product count with link."""
        count = getattr(obj, "product_count", 0)
        if count > 0:
            url = (
                reverse("admin:products_product_changelist")
                + f"?category__id__exact={obj.id}"
            )
            return format_html('<a href="{}">{} products</a>', url, count)
        return "0 products"

    product_count.short_description = _("Products")
    product_count.admin_order_field = "product_count"

    def product_count_display(self, obj):
        """Detailed product count display."""
        if obj.pk:
            total = obj.products.count()
            active = obj.products.filter(status="active").count()
            inactive = total - active

            return format_html(
                '<div style="font-size: 13px;">'
                "<strong>Total:</strong> {} products<br>"
                '<span style="color: #28a745;">Active:</span> {}<br>'
                '<span style="color: #dc3545;">Inactive:</span> {}</div>',
                total,
                active,
                inactive,
            )
        return "No products yet"

    product_count_display.short_description = _("Product Statistics")

    def category_tree_display(self, obj):
        """Display category hierarchy tree."""
        if obj.parent:
            tree_path = []
            current = obj.parent
            while current:
                tree_path.append(current.name)
                current = current.parent
            tree_path.reverse()
            tree_path.append(f"<strong>{obj.name}</strong>")

            return format_html(" → ".join(tree_path))
        return format_html("<strong>{}</strong> (Root Category)", obj.name)

    category_tree_display.short_description = _("Category Tree")

    def full_name_display(self, obj):
        """Display full category path."""
        return obj.full_name

    full_name_display.short_description = _("Full Path")

    def level_display(self, obj):
        """Display category level."""
        level = obj.level
        level_names = ["Root", "Level 1", "Level 2", "Level 3", "Level 4+"]
        level_name = level_names[min(level, 4)]

        color = ["#007bff", "#28a745", "#ffc107", "#fd7e14", "#dc3545"][min(level, 4)]
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>', color, level_name
        )

    level_display.short_description = _("Level")

    # Admin Actions
    def activate_categories(self, request, queryset):
        """Activate selected categories."""
        updated = queryset.update(is_active=True)
        self.message_user(
            request, f"{updated} category(ies) activated.", level="SUCCESS"
        )

    activate_categories.short_description = _("Activate selected categories")

    def deactivate_categories(self, request, queryset):
        """Deactivate selected categories."""
        updated = queryset.update(is_active=False)
        self.message_user(
            request, f"{updated} category(ies) deactivated.", level="SUCCESS"
        )

    deactivate_categories.short_description = _("Deactivate selected categories")

    def reset_sort_order(self, request, queryset):
        """Reset sort order to 0."""
        updated = queryset.update(sort_order=0)
        self.message_user(
            request, f"{updated} category(ies) sort order reset.", level="SUCCESS"
        )

    reset_sort_order.short_description = _("Reset sort order")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Professional admin interface for Product."""

    list_display = [
        "name_with_image",
        "sku",
        "category",
        "price_display",
        "stock_status",
        "status_display",
        "featured_display",
        "view_count",
        "created_at",
    ]
    list_filter = [
        "status",
        "is_featured",
        "is_digital",
        "requires_shipping",
        "track_inventory",
        "allow_backorder",
        ("category", admin.RelatedOnlyFieldListFilter),
        ("owner", admin.RelatedOnlyFieldListFilter),
        "created_at",
        "updated_at",
        "published_at",
        "price",
        "stock_quantity",
    ]
    search_fields = [
        "name",
        "sku",
        "description",
        "short_description",
        "tags",
        "meta_title",
        "meta_description",
    ]
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = [
        "sku",
        "created_at",
        "updated_at",
        "published_at",
        "view_count",
        "profit_display",
        "discount_display",
        "stock_status_display",
        "dimensions_display",
        "image_preview",
    ]
    date_hierarchy = "created_at"
    ordering = ["-created_at"]

    fieldsets = (
        (
            _("Basic Information"),
            {"fields": ("name", "slug", "sku", "description", "short_description")},
        ),
        (_("Categorization"), {"fields": ("category", "tags")}),
        (
            _("Pricing"),
            {
                "fields": (
                    "price",
                    "compare_at_price",
                    "cost_price",
                    "profit_display",
                    "discount_display",
                )
            },
        ),
        (
            _("Inventory"),
            {
                "fields": (
                    "stock_quantity",
                    "low_stock_threshold",
                    "track_inventory",
                    "allow_backorder",
                    "stock_status_display",
                )
            },
        ),
        (
            _("Physical Properties"),
            {
                "fields": (
                    "weight",
                    "dimensions_length",
                    "dimensions_width",
                    "dimensions_height",
                    "dimensions_display",
                ),
                "classes": ("collapse",),
            },
        ),
        (_("Media"), {"fields": ("featured_image", "image_preview", "image_url")}),
        (
            _("SEO"),
            {"fields": ("meta_title", "meta_description"), "classes": ("collapse",)},
        ),
        (
            _("Settings"),
            {
                "fields": (
                    "status",
                    "is_featured",
                    "is_digital",
                    "requires_shipping",
                    "owner",
                )
            },
        ),
        (_("Analytics"), {"fields": ("view_count",), "classes": ("collapse",)}),
        (
            _("System Information"),
            {
                "fields": ("created_at", "updated_at", "published_at"),
                "classes": ("collapse",),
            },
        ),
    )

    inlines = [ProductImageInline]
    actions = [
        "mark_as_featured",
        "unmark_as_featured",
        "activate_products",
        "deactivate_products",
        "reset_view_count",
        "update_stock_alert",
    ]

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return (
            super()
            .get_queryset(request)
            .select_related("category", "owner")
            .prefetch_related("images")
        )

    def name_with_image(self, obj):
        """Display product name with thumbnail image."""
        image_html = ""
        if obj.featured_image:
            image_html = format_html(
                '<img src="{}" style="width: 40px; height: 40px; object-fit: cover; '
                'border-radius: 5px; margin-right: 10px;" />',
                obj.featured_image.url,
            )
        elif obj.image_url:
            image_html = format_html(
                '<img src="{}" style="width: 40px; height: 40px; object-fit: cover; '
                'border-radius: 5px; margin-right: 10px;" />',
                obj.image_url,
            )

        return format_html(
            '<div style="display: flex; align-items: center;">{}{}</div>',
            image_html,
            obj.name,
        )

    name_with_image.short_description = _("Product")
    name_with_image.admin_order_field = "name"

    def price_display(self, obj):
        """Display price with discount information."""
        price_html = f"<strong>${obj.price}</strong>"

        if obj.compare_at_price and obj.compare_at_price > obj.price:
            discount_pct = obj.discount_percentage
            price_html += format_html(
                '<br><span style="text-decoration: line-through; color: #6c757d; font-size: 12px;">'
                '${}</span> <span style="color: #dc3545; font-size: 12px; font-weight: bold;">'
                "(-{}%)</span>",
                obj.compare_at_price,
                discount_pct,
            )

        return format_html(price_html)

    price_display.short_description = _("Price")
    price_display.admin_order_field = "price"

    def stock_status(self, obj):
        """Display stock status with color coding."""
        if not obj.track_inventory:
            return format_html('<span style="color: #6c757d;">No tracking</span>')

        if obj.is_out_of_stock:
            color = "#dc3545"
            text = f"Out of stock"
            if obj.allow_backorder:
                text += " (Backorder OK)"
        elif obj.is_low_stock:
            color = "#ffc107"
            text = f"Low stock ({obj.stock_quantity})"
        else:
            color = "#28a745"
            text = f"In stock ({obj.stock_quantity})"

        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>', color, text
        )

    stock_status.short_description = _("Stock")
    stock_status.admin_order_field = "stock_quantity"

    def status_display(self, obj):
        """Display product status with color coding."""
        status_colors = {
            "draft": "#6c757d",
            "active": "#28a745",
            "inactive": "#ffc107",
            "discontinued": "#dc3545",
        }
        color = status_colors.get(obj.status, "#6c757d")
        return format_html(
            '<span style="color: {}; font-weight: bold;">● {}</span>',
            color,
            obj.get_status_display(),
        )

    status_display.short_description = _("Status")
    status_display.admin_order_field = "status"

    def featured_display(self, obj):
        """Display featured status."""
        if obj.is_featured:
            return format_html(
                '<span style="color: #ffc107; font-size: 16px;">★</span>'
            )
        return "-"

    featured_display.short_description = _("Featured")
    featured_display.admin_order_field = "is_featured"

    def profit_display(self, obj):
        """Display profit information."""
        if obj.cost_price:
            profit = obj.profit_margin
            profit_pct = obj.profit_percentage
            color = "#28a745" if profit > 0 else "#dc3545"

            return format_html(
                '<span style="color: {}; font-weight: bold;">${}</span><br>'
                '<span style="color: {}; font-size: 12px;">({}%)</span>',
                color,
                profit,
                color,
                profit_pct,
            )
        return "No cost price set"

    profit_display.short_description = _("Profit")

    def discount_display(self, obj):
        """Display discount information."""
        if obj.discount_percentage:
            return format_html(
                '<span style="color: #dc3545; font-weight: bold;">{}% OFF</span><br>'
                '<span style="font-size: 12px;">Save ${}</span>',
                obj.discount_percentage,
                obj.compare_at_price - obj.price,
            )
        return "No discount"

    discount_display.short_description = _("Discount")

    def stock_status_display(self, obj):
        """Detailed stock status display."""
        if not obj.track_inventory:
            return format_html(
                '<span style="color: #6c757d;">Inventory tracking disabled</span>'
            )

        status_info = f"<strong>Current Stock:</strong> {obj.stock_quantity}<br>"
        status_info += (
            f"<strong>Low Stock Threshold:</strong> {obj.low_stock_threshold}<br>"
        )

        if obj.is_out_of_stock:
            status_info += (
                '<span style="color: #dc3545;">Status: Out of Stock</span><br>'
            )
            if obj.allow_backorder:
                status_info += (
                    '<span style="color: #ffc107;">Backorders: Allowed</span>'
                )
        elif obj.is_low_stock:
            status_info += '<span style="color: #ffc107;">Status: Low Stock</span>'
        else:
            status_info += '<span style="color: #28a745;">Status: In Stock</span>'

        return format_html(status_info)

    stock_status_display.short_description = _("Stock Details")

    def dimensions_display(self, obj):
        """Display product dimensions."""
        if obj.dimensions:
            weight_info = f" (Weight: {obj.weight} kg)" if obj.weight else ""
            return f"{obj.dimensions}{weight_info}"
        elif obj.weight:
            return f"Weight: {obj.weight} kg"
        return "No dimensions set"

    dimensions_display.short_description = _("Dimensions")

    def image_preview(self, obj):
        """Display image preview."""
        if obj.featured_image:
            return format_html(
                '<img src="{}" style="max-width: 200px; max-height: 200px; border-radius: 5px;" />',
                obj.featured_image.url,
            )
        elif obj.image_url:
            return format_html(
                '<img src="{}" style="max-width: 200px; max-height: 200px; border-radius: 5px;" />',
                obj.image_url,
            )
        return "No image"

    image_preview.short_description = _("Image Preview")

    # Admin Actions
    def mark_as_featured(self, request, queryset):
        """Mark selected products as featured."""
        updated = queryset.update(is_featured=True)
        self.message_user(
            request, f"{updated} product(s) marked as featured.", level="SUCCESS"
        )

    mark_as_featured.short_description = _("Mark as featured")

    def unmark_as_featured(self, request, queryset):
        """Unmark selected products as featured."""
        updated = queryset.update(is_featured=False)
        self.message_user(
            request, f"{updated} product(s) unmarked as featured.", level="SUCCESS"
        )

    unmark_as_featured.short_description = _("Unmark as featured")

    def activate_products(self, request, queryset):
        """Activate selected products."""
        updated_count = 0
        for product in queryset:
            if product.status != Product.Status.ACTIVE:
                product.status = Product.Status.ACTIVE
                if not product.published_at:
                    product.published_at = timezone.now()
                product.save()
                updated_count += 1

        self.message_user(
            request, f"{updated_count} product(s) activated.", level="SUCCESS"
        )

    activate_products.short_description = _("Activate selected products")

    def deactivate_products(self, request, queryset):
        """Deactivate selected products."""
        updated = queryset.update(status=Product.Status.INACTIVE)
        self.message_user(
            request, f"{updated} product(s) deactivated.", level="SUCCESS"
        )

    deactivate_products.short_description = _("Deactivate selected products")

    def reset_view_count(self, request, queryset):
        """Reset view count to 0."""
        updated = queryset.update(view_count=0)
        self.message_user(
            request, f"{updated} product(s) view count reset.", level="SUCCESS"
        )

    reset_view_count.short_description = _("Reset view count")

    def update_stock_alert(self, request, queryset):
        """Update low stock threshold for selected products."""
        # This could be enhanced to show a form for setting the threshold
        updated = queryset.update(low_stock_threshold=5)
        self.message_user(
            request,
            f"{updated} product(s) low stock threshold updated to 5.",
            level="SUCCESS",
        )

    update_stock_alert.short_description = _("Update stock alert threshold")


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    """Professional admin interface for ProductImage."""

    list_display = [
        "image_preview",
        "product_link",
        "alt_text",
        "sort_order",
        "status_display",
        "created_at",
    ]
    list_filter = [
        "is_active",
        "created_at",
        ("product", admin.RelatedOnlyFieldListFilter),
    ]
    search_fields = ["product__name", "alt_text"]
    readonly_fields = ["created_at", "image_preview"]
    ordering = ["product", "sort_order", "created_at"]

    fieldsets = (
        (
            _("Image Information"),
            {"fields": ("product", "image", "image_preview", "alt_text")},
        ),
        (_("Settings"), {"fields": ("sort_order", "is_active")}),
        (
            _("System Information"),
            {"fields": ("created_at",), "classes": ("collapse",)},
        ),
    )

    actions = ["activate_images", "deactivate_images", "reset_sort_order"]

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related("product")

    def image_preview(self, obj):
        """Display image preview."""
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 80px; height: 80px; object-fit: cover; '
                'border-radius: 5px;" />',
                obj.image.url,
            )
        return "No image"

    image_preview.short_description = _("Preview")

    def product_link(self, obj):
        """Display product as clickable link."""
        url = reverse("admin:products_product_change", args=[obj.product.pk])
        return format_html('<a href="{}">{}</a>', url, obj.product.name)

    product_link.short_description = _("Product")
    product_link.admin_order_field = "product__name"

    def status_display(self, obj):
        """Display status with color coding."""
        if obj.is_active:
            return format_html(
                '<span style="color: #28a745; font-weight: bold;">● Active</span>'
            )
        else:
            return format_html(
                '<span style="color: #dc3545; font-weight: bold;">● Inactive</span>'
            )

    status_display.short_description = _("Status")
    status_display.admin_order_field = "is_active"

    # Admin Actions
    def activate_images(self, request, queryset):
        """Activate selected images."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} image(s) activated.", level="SUCCESS")

    activate_images.short_description = _("Activate selected images")

    def deactivate_images(self, request, queryset):
        """Deactivate selected images."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} image(s) deactivated.", level="SUCCESS")

    deactivate_images.short_description = _("Deactivate selected images")

    def reset_sort_order(self, request, queryset):
        """Reset sort order to 0."""
        updated = queryset.update(sort_order=0)
        self.message_user(
            request, f"{updated} image(s) sort order reset.", level="SUCCESS"
        )

    reset_sort_order.short_description = _("Reset sort order")
