```zsh
# First, import everything we need
from decimal import Decimal
from django.contrib.auth.models import User
from products.models import Product, Category, ProductImage

# Get a user
user = User.objects.first()
print(f"Using user: {user.username}")

# Create categories first
electronics = Category.objects.create(
    name="Electronics",
    description="Electronic devices and gadgets"
)

smartphones = Category.objects.create(
    name="Smartphones", 
    parent=electronics,
    description="Mobile phones and accessories"
)

print(f"✅ Created categories: {electronics.name} > {smartphones.name}")

# Now create the product
product = Product.objects.create(
    name="iPhone 15 Pro",
    price=Decimal('999.99'),
    compare_at_price=Decimal('1199.99'),
    cost_price=Decimal('600.00'),
    category=smartphones,
    stock_quantity=50,
    weight=Decimal('0.187'),
    is_featured=True,
    owner=user
)

print(f"✅ Product created: {product.name}")
print(f"📦 SKU: {product.sku}")
print(f"🔗 Slug: {product.slug}")
print(f"💰 Price: ${product.price}")
print(f"📊 Discount: {product.discount_percentage}%")
print(f"💵 Profit: ${product.profit_margin}")
print(f"📈 Profit %: {product.profit_percentage}%")
print(f"📦 In stock: {product.is_in_stock}")
print(f"🌟 Featured: {product.is_featured}")
print(f"📐 Weight: {product.weight}kg")

# First, let's check what categories already exist
existing_categories = Category.objects.all()
print("Existing categories:")
for cat in existing_categories:
    print(f"  - {cat.name} (slug: {cat.slug})")

# Use get_or_create to avoid duplicates
electronics, created = Category.objects.get_or_create(
    name="Electronics",
    defaults={
        'description': "Electronic devices and gadgets"
    }
)
if created:
    print(f"✅ Created category: {electronics.name}")
else:
    print(f"📁 Using existing category: {electronics.name}")

smartphones, created = Category.objects.get_or_create(
    name="Smartphones",
    defaults={
        'parent': electronics,
        'description': "Mobile phones and accessories"
    }
)
if created:
    print(f"✅ Created category: {smartphones.name}")
else:
    print(f"📱 Using existing category: {smartphones.name}")

print(f"✅ Categories ready: {electronics.name} > {smartphones.name}")

# Now create the product
product, created = Product.objects.get_or_create(
    name="iPhone 15 Pro",
    defaults={
        'price': Decimal('999.99'),
        'compare_at_price': Decimal('1199.99'),
        'cost_price': Decimal('600.00'),
        'category': smartphones,
        'stock_quantity': 50,
        'weight': Decimal('0.187'),
        'is_featured': True,
        'owner': user
    }
)

if created:
    print(f"✅ Product created: {product.name}")
else:
    print(f"📱 Using existing product: {product.name}")

print(f"📦 SKU: {product.sku}")
print(f"🔗 Slug: {product.slug}")
print(f"💰 Price: ${product.price}")
print(f"📊 Discount: {product.discount_percentage}%")
print(f"💵 Profit: ${product.profit_margin}")
print(f"📈 Profit %: {product.profit_percentage}%")
print(f"📦 In stock: {product.is_in_stock}")
print(f"🌟 Featured: {product.is_featured}")
print(f"📐 Weight: {product.weight}kg")

🧹 Alternative: Clean Slate Approach
If you want to start fresh, you can delete existing data first:
# Clean slate - delete existing data (CAREFUL!)
print("🧹 Cleaning existing data...")
Product.objects.all().delete()
Category.objects.all().delete()
print("✅ Cleaned up existing products and categories")

# Now create fresh categories
electronics = Category.objects.create(
    name="Electronics",
    description="Electronic devices and gadgets"
)

smartphones = Category.objects.create(
    name="Smartphones", 
    parent=electronics,
    description="Mobile phones and accessories"
)

print(f"✅ Created fresh categories: {electronics.name} > {smartphones.name}")

# Create the product
product = Product.objects.create(
    name="iPhone 15 Pro",
    price=Decimal('999.99'),
    compare_at_price=Decimal('1199.99'),
    cost_price=Decimal('600.00'),
    category=smartphones,
    stock_quantity=50,
    weight=Decimal('0.187'),
    is_featured=True,
    owner=user
)

print(f"✅ Product created: {product.name}")

🚀 Then Test All Features:

# Test category hierarchy
print(f"\n=== CATEGORY TESTING ===")
print(f"📁 Electronics: {electronics.name}")
print(f"📱 Smartphones: {smartphones.full_name}")
print(f"📊 Category level: {smartphones.level}")

# Test professional product properties
print(f"\n=== PRODUCT PROPERTIES ===")
print(f"💰 Regular price: ${product.price}")
print(f"💸 Compare price: ${product.compare_at_price}")
print(f"💵 Cost price: ${product.cost_price}")
print(f"📊 Discount: {product.discount_percentage}%")
print(f"💰 Profit margin: ${product.profit_margin}")
print(f"📈 Profit percentage: {product.profit_percentage}%")
print(f"📦 Stock: {product.stock_quantity}")
print(f"📉 Low stock: {product.is_low_stock}")
print(f"✅ In stock: {product.is_in_stock}")

# Test professional methods
print(f"\n=== TESTING METHODS ===")
print(f"👀 Views before: {product.view_count}")
product.increment_view_count()
print(f"👀 Views after: {product.view_count}")

# Test stock management
print(f"📦 Stock before sale: {product.stock_quantity}")
sale_success = product.reduce_stock(5)
print(f"💳 Sale successful: {sale_success}")
print(f"📦 Stock after sale: {product.stock_quantity}")

# Restock
product.increase_stock(10)
print(f"📦 Stock after restock: {product.stock_quantity}")

print(f"\n🎉 All professional product features working!")
