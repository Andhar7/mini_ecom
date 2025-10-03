from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from products.models import Category, Product, ProductImage


class Command(BaseCommand):
    help = (
        "Create and test product categories and products with all professional features"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--clean",
            action="store_true",
            help="Delete all existing products and categories before creating new ones",
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS("🚀 Starting Product & Category Testing...")
        )

        # Clean existing data if requested
        if options["clean"]:
            self.clean_existing_data()

        # Get or create a user for testing
        user = self.get_test_user()

        # Create categories
        electronics, smartphones = self.create_categories()

        # Create sample products
        products = self.create_sample_products(user, smartphones)

        # Test all professional features
        self.test_category_features(electronics, smartphones)
        self.test_product_features(products)
        self.test_manager_methods()
        self.test_analytics_features(products)

        self.stdout.write(
            self.style.SUCCESS(
                "\n🎉 All product and category tests completed successfully!"
            )
        )

    def clean_existing_data(self):
        """Clean existing products and categories."""
        self.stdout.write("🧹 Cleaning existing data...")

        product_count = Product.objects.count()
        category_count = Category.objects.count()

        Product.objects.all().delete()
        Category.objects.all().delete()

        self.stdout.write(
            f"   🗑️  Deleted {product_count} products and {category_count} categories"
        )

    def get_test_user(self):
        """Get or create a test user."""
        user = User.objects.first()
        if not user:
            user = User.objects.create_user(
                username="testuser", email="test@example.com", password="testpass123"
            )
            self.stdout.write("👤 Created test user: testuser")
        else:
            self.stdout.write(f"👤 Using existing user: {user.username}")
        return user

    def create_categories(self):
        """Create sample categories."""
        self.stdout.write("\n📁 Creating Categories...")

        # Use get_or_create to avoid duplicates
        electronics, created = Category.objects.get_or_create(
            name="Electronics",
            defaults={"description": "Electronic devices and gadgets"},
        )
        if created:
            self.stdout.write(f"   ✅ Created category: {electronics.name}")
        else:
            self.stdout.write(f"   📁 Using existing category: {electronics.name}")

        smartphones, created = Category.objects.get_or_create(
            name="Smartphones",
            defaults={
                "parent": electronics,
                "description": "Mobile phones and accessories",
            },
        )
        if created:
            self.stdout.write(f"   ✅ Created category: {smartphones.name}")
        else:
            self.stdout.write(f"   📱 Using existing category: {smartphones.name}")

        # Create additional categories
        laptops, created = Category.objects.get_or_create(
            name="Laptops",
            defaults={
                "parent": electronics,
                "description": "Laptops and portable computers",
            },
        )
        if created:
            self.stdout.write(f"   ✅ Created category: {laptops.name}")

        return electronics, smartphones

    def create_sample_products(self, user, smartphones):
        """Create sample products for testing."""
        self.stdout.write("\n🛍️ Creating Sample Products...")

        sample_products_data = [
            {
                "name": "iPhone 15 Pro",
                "price": Decimal("999.99"),
                "compare_at_price": Decimal("1199.99"),
                "cost_price": Decimal("600.00"),
                "stock_quantity": 50,
                "weight": Decimal("0.187"),
                "is_featured": True,
                "short_description": "Latest iPhone with Pro features",
                "description": "The most advanced iPhone ever with titanium design and A17 Pro chip.",
            },
            {
                "name": "Samsung Galaxy S24",
                "price": Decimal("899.99"),
                "compare_at_price": Decimal("999.99"),
                "cost_price": Decimal("500.00"),
                "stock_quantity": 30,
                "weight": Decimal("0.195"),
                "is_featured": True,
                "short_description": "Flagship Samsung smartphone",
                "description": "Premium Android smartphone with advanced camera system.",
            },
            {
                "name": "Google Pixel 8",
                "price": Decimal("699.99"),
                "cost_price": Decimal("400.00"),
                "stock_quantity": 25,
                "weight": Decimal("0.180"),
                "is_featured": False,
                "short_description": "Pure Android experience",
                "description": "Google's flagship phone with the best Android experience.",
            },
            {
                "name": "OnePlus 12",
                "price": Decimal("799.99"),
                "compare_at_price": Decimal("899.99"),
                "cost_price": Decimal("450.00"),
                "stock_quantity": 15,
                "weight": Decimal("0.190"),
                "is_featured": True,
                "short_description": "Never Settle flagship",
                "description": "High-performance smartphone with fast charging.",
            },
            {
                "name": "Xiaomi 14 Pro",
                "price": Decimal("649.99"),
                "cost_price": Decimal("350.00"),
                "stock_quantity": 0,  # Out of stock for testing
                "weight": Decimal("0.185"),
                "is_featured": False,
                "short_description": "Premium Xiaomi flagship",
                "description": "Feature-rich smartphone with excellent value.",
            },
        ]

        created_products = []
        for product_data in sample_products_data:
            product, created = Product.objects.get_or_create(
                name=product_data["name"],
                defaults={
                    **product_data,
                    "category": smartphones,
                    "owner": user,
                },
            )
            created_products.append(product)

            if created:
                self.stdout.write(
                    f"   ✅ Created: {product.name} - ${product.price} (SKU: {product.sku})"
                )
            else:
                self.stdout.write(
                    f"   📱 Using existing: {product.name} - ${product.price}"
                )

        return created_products

    def test_category_features(self, electronics, smartphones):
        """Test category professional features."""
        self.stdout.write("\n📊 Testing Category Features...")

        self.stdout.write(f"   📁 Electronics: {electronics.name}")
        self.stdout.write(f"   📱 Smartphones: {smartphones.full_name}")
        self.stdout.write(f"   📊 Category level: {smartphones.level}")
        self.stdout.write(f"   🔗 Electronics slug: {electronics.slug}")
        self.stdout.write(f"   🔗 Smartphones slug: {smartphones.slug}")

        # Test subcategories
        subcategories = electronics.subcategories.all()
        self.stdout.write(
            f"   📂 Electronics has {subcategories.count()} subcategories:"
        )
        for subcat in subcategories:
            self.stdout.write(f"      - {subcat.name}")

    def test_product_features(self, products):
        """Test product professional features."""
        self.stdout.write("\n🛍️ Testing Product Features...")

        for product in products:
            self.stdout.write(f"\n   📱 {product.name}:")
            self.stdout.write(f"      💰 Price: ${product.price}")
            self.stdout.write(f"      📦 SKU: {product.sku}")
            self.stdout.write(f"      🔗 Slug: {product.slug}")

            if product.discount_percentage:
                self.stdout.write(
                    f"      🔥 Discount: {product.discount_percentage}% off"
                )

            if product.profit_margin:
                self.stdout.write(
                    f"      💵 Profit: ${product.profit_margin} ({product.profit_percentage}%)"
                )

            self.stdout.write(f"      📦 Stock: {product.stock_quantity}")
            self.stdout.write(f"      ✅ In stock: {product.is_in_stock}")
            self.stdout.write(f"      📉 Low stock: {product.is_low_stock}")
            self.stdout.write(
                f"      🌟 Featured: {'Yes' if product.is_featured else 'No'}"
            )
            self.stdout.write(f"      👀 Views: {product.view_count}")

            if product.weight:
                self.stdout.write(f"      📐 Weight: {product.weight}kg")

    def test_manager_methods(self):
        """Test custom manager methods."""
        self.stdout.write("\n🛠️ Testing Manager Methods...")

        # Category manager methods
        active_categories = Category.objects.active_categories()
        self.stdout.write(f"   📁 Active categories: {active_categories.count()}")

        # Product manager methods
        active_products = Product.objects.active_products()
        featured_products = Product.objects.featured_products()
        in_stock_products = Product.objects.in_stock()
        out_of_stock_products = Product.objects.out_of_stock()

        self.stdout.write(f"   🔥 Active products: {active_products.count()}")
        self.stdout.write(f"   ⭐ Featured products: {featured_products.count()}")
        self.stdout.write(f"   📦 In stock products: {in_stock_products.count()}")
        self.stdout.write(
            f"   ❌ Out of stock products: {out_of_stock_products.count()}"
        )

        # Test price range filtering
        affordable = Product.objects.by_price_range(
            min_price=Decimal("500"), max_price=Decimal("800")
        )
        premium = Product.objects.by_price_range(min_price=Decimal("900"))

        self.stdout.write(
            f"   💰 Affordable products ($500-$800): {affordable.count()}"
        )
        self.stdout.write(f"   💎 Premium products ($900+): {premium.count()}")

        # Test popular products
        popular = Product.objects.popular_products(limit=3)
        self.stdout.write(f"   🔥 Top 3 popular products:")
        for i, product in enumerate(popular, 1):
            self.stdout.write(f"      {i}. {product.name} - {product.view_count} views")

    def test_analytics_features(self, products):
        """Test analytics and business features."""
        self.stdout.write("\n📈 Testing Analytics Features...")

        # Test view count increment
        first_product = products[0]
        self.stdout.write(f"   👀 Testing view tracking for {first_product.name}:")
        self.stdout.write(f"      Views before: {first_product.view_count}")
        first_product.increment_view_count()
        self.stdout.write(f"      Views after: {first_product.view_count}")

        # Test stock management
        if first_product.stock_quantity > 5:
            self.stdout.write(f"   📦 Testing stock management:")
            self.stdout.write(
                f"      Stock before sale: {first_product.stock_quantity}"
            )
            sale_success = first_product.reduce_stock(5)
            self.stdout.write(f"      Sale successful: {sale_success}")
            self.stdout.write(f"      Stock after sale: {first_product.stock_quantity}")

            # Restock
            first_product.increase_stock(3)
            self.stdout.write(
                f"      Stock after restock: {first_product.stock_quantity}"
            )

        # Calculate business metrics
        total_value = sum(
            p.price * p.stock_quantity for p in products if p.track_inventory
        )
        total_cost = sum(
            (p.cost_price or Decimal("0")) * p.stock_quantity
            for p in products
            if p.cost_price and p.track_inventory
        )

        self.stdout.write(f"   💰 Total inventory value: ${total_value:,.2f}")
        if total_cost > 0:
            self.stdout.write(f"   💵 Total inventory cost: ${total_cost:,.2f}")
            self.stdout.write(
                f"   📊 Potential profit: ${total_value - total_cost:,.2f}"
            )

        # Category statistics
        categories = Category.objects.active_categories()
        self.stdout.write(f"   📊 Category Statistics:")
        for category in categories:
            product_count = category.products.filter(status="active").count()
            if product_count > 0:
                self.stdout.write(f"      📁 {category.name}: {product_count} products")
