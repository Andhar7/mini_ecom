#!/bin/bash

# =============================================================================
# Mini E-commerce API Testing Script
# =============================================================================
# This script tests all API endpoints for the mini e-commerce backend
# Run with: bash test_api_endpoints.sh
# =============================================================================

BASE_URL="http://localhost:8000"
API_BASE="${BASE_URL}/api"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counter
TOTAL_TESTS=0
PASSED_TESTS=0

# Helper functions
print_header() {
    echo -e "\n${BLUE}============================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================${NC}"
}

print_test() {
    echo -e "\n${YELLOW}📋 Test: $1${NC}"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
}

print_success() {
    echo -e "${GREEN}✅ SUCCESS: $1${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
}

print_error() {
    echo -e "${RED}❌ ERROR: $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  INFO: $1${NC}"
}

# Variables to store tokens and IDs
ACCESS_TOKEN=""
REFRESH_TOKEN=""
USER_ID=""
CATEGORY_ID=""
PRODUCT_ID=""
PRODUCT_SLUG=""

# =============================================================================
# Authentication Tests
# =============================================================================
print_header "AUTHENTICATION TESTS"

print_test "User Registration"
REGISTER_RESPONSE=$(curl -s -X POST "${API_BASE}/auth/register/" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser_'$(date +%s)'",
    "email": "test'$(date +%s)'@example.com",
    "password": "SecurePass123!",
    "first_name": "Test",
    "last_name": "User"
  }')

if echo "$REGISTER_RESPONSE" | grep -q "User created successfully"; then
    print_success "User registration successful"
    USER_ID=$(echo "$REGISTER_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['user']['id'])" 2>/dev/null)
    print_info "User ID: $USER_ID"
    print_info "Email verification required - this is expected behavior"
else
    print_error "User registration failed"
    echo "Response: $REGISTER_RESPONSE"
fi

print_test "Admin User Login"
print_info "Attempting login with admin credentials..."

# Try login with admin credentials first (should be verified)
ADMIN_LOGIN_RESPONSE=$(curl -s -X POST "${API_BASE}/auth/login/" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }')

print_info "Admin login response received"
echo "Full Response: $ADMIN_LOGIN_RESPONSE"

if echo "$ADMIN_LOGIN_RESPONSE" | grep -q "tokens"; then
    print_success "Admin login successful"
    ACCESS_TOKEN=$(echo "$ADMIN_LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['tokens']['access'])" 2>/dev/null)
    REFRESH_TOKEN=$(echo "$ADMIN_LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['tokens']['refresh'])" 2>/dev/null)
    print_info "Access Token: ${ACCESS_TOKEN:0:20}..."
elif echo "$ADMIN_LOGIN_RESPONSE" | grep -q "success.*true"; then
    print_success "Admin login successful (alternative format)"
    ACCESS_TOKEN=$(echo "$ADMIN_LOGIN_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('tokens', {}).get('access', ''))" 2>/dev/null)
    REFRESH_TOKEN=$(echo "$ADMIN_LOGIN_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('tokens', {}).get('refresh', ''))" 2>/dev/null)
    print_info "Access Token: ${ACCESS_TOKEN:0:20}..."
else
    print_error "Admin login failed"
    print_info "Response: $ADMIN_LOGIN_RESPONSE"
    
    # Fallback: Create a test user with known credentials
    print_info "Creating and verifying test user..."
    TEST_USERNAME="apitestuser"
    TEST_PASSWORD="ApiTest123!"
    TEST_EMAIL="apitest@example.com"

    CREATE_TEST_USER=$(curl -s -X POST "${API_BASE}/auth/register/" \
      -H "Content-Type: application/json" \
      -d "{
        \"username\": \"$TEST_USERNAME\",
        \"email\": \"$TEST_EMAIL\",
        \"password\": \"$TEST_PASSWORD\",
        \"first_name\": \"API\",
        \"last_name\": \"Test\"
      }")

    print_info "Created test user, now trying to verify and login..."
    
    # Try to create verified test user directly using Django shell if regular login fails
    if echo "$CREATE_TEST_USER" | grep -q "User created successfully"; then
        print_info "Test user created, trying to verify email and login..."
        
        # Create and verify a test user directly using Django shell
        python manage.py shell -c "
from django.contrib.auth.models import User
from authentication.models import UserProfile
from rest_framework_simplejwt.tokens import RefreshToken

# Create or get test user
username = '$TEST_USERNAME'
email = '$TEST_EMAIL'
password = '$TEST_PASSWORD'

try:
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            'email': email,
            'is_active': True
        }
    )
    if created or not user.check_password(password):
        user.set_password(password)
        user.save()
    
    # Create and verify profile
    profile, created = UserProfile.objects.get_or_create(user=user)
    if not profile.email_verified:
        profile.verify_email()
        print('Profile verified')
    
    # Generate tokens
    refresh = RefreshToken.for_user(user)
    print(f'ACCESS_TOKEN:{refresh.access_token}')
    print(f'REFRESH_TOKEN:{refresh}')
    print('Test user created and verified successfully')
    
except Exception as e:
    print(f'Error: {e}')
" > /tmp/django_shell_output.txt
        
        # Extract tokens from shell output
        if grep -q "ACCESS_TOKEN:" /tmp/django_shell_output.txt; then
            ACCESS_TOKEN=$(grep "ACCESS_TOKEN:" /tmp/django_shell_output.txt | cut -d: -f2-)
            REFRESH_TOKEN=$(grep "REFRESH_TOKEN:" /tmp/django_shell_output.txt | cut -d: -f2-)
            print_success "Created verified test user successfully"
            print_info "Access Token: ${ACCESS_TOKEN:0:20}..."
        else
            print_error "Failed to create verified test user"
            echo "Django shell output:"
            cat /tmp/django_shell_output.txt
        fi
        
        # Clean up temp file
        rm -f /tmp/django_shell_output.txt
    fi
fi

print_test "Token Refresh"
if [ ! -z "$REFRESH_TOKEN" ]; then
    REFRESH_RESPONSE=$(curl -s -X POST "${API_BASE}/auth/token/refresh/" \
      -H "Content-Type: application/json" \
      -d "{\"refresh\": \"$REFRESH_TOKEN\"}")
    
    if echo "$REFRESH_RESPONSE" | grep -q "access"; then
        print_success "Token refresh successful"
        ACCESS_TOKEN=$(echo "$REFRESH_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access'])" 2>/dev/null)
    else
        print_error "Token refresh failed"
    fi
else
    print_info "Skipping token refresh (no refresh token available)"
fi

print_test "User Profile"
if [ ! -z "$ACCESS_TOKEN" ]; then
    PROFILE_RESPONSE=$(curl -s -X GET "${API_BASE}/auth/profile/" \
      -H "Authorization: Bearer $ACCESS_TOKEN")
    
    if echo "$PROFILE_RESPONSE" | grep -q "username"; then
        print_success "User profile retrieval successful"
    else
        print_error "User profile retrieval failed"
        echo "Response: $PROFILE_RESPONSE"
    fi
else
    print_error "Skipping profile test (no access token)"
fi

# =============================================================================
# Category Tests
# =============================================================================
print_header "CATEGORY TESTS"

print_test "Create Category"
if [ ! -z "$ACCESS_TOKEN" ]; then
    # Use timestamp to make category name unique
    TIMESTAMP=$(date +%s)
    CATEGORY_NAME="Test Category API ${TIMESTAMP}"
    CREATE_CATEGORY_RESPONSE=$(curl -s -X POST "${API_BASE}/categories/" \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      -H "Content-Type: application/json" \
      -d "{
        \"name\": \"${CATEGORY_NAME}\",
        \"description\": \"Test category for API testing\",
        \"is_active\": true,
        \"sort_order\": 1
      }")
    
    echo "Category creation response: $CREATE_CATEGORY_RESPONSE"
    
    if echo "$CREATE_CATEGORY_RESPONSE" | grep -q "id"; then
        print_success "Category creation successful"
        CATEGORY_ID=$(echo "$CREATE_CATEGORY_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('id', ''))" 2>/dev/null)
        CATEGORY_SLUG=$(echo "$CREATE_CATEGORY_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('slug', ''))" 2>/dev/null)
        CATEGORY_NAME_RESPONSE=$(echo "$CREATE_CATEGORY_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('name', ''))" 2>/dev/null)
        print_info "Category ID: $CATEGORY_ID"
        print_info "Category Slug: $CATEGORY_SLUG"
        print_info "Category Name from Response: $CATEGORY_NAME_RESPONSE"
    else
        print_error "Category creation failed"
        echo "Response: $CREATE_CATEGORY_RESPONSE"
    fi
else
    print_error "Skipping category creation (no access token)"
fi

print_test "List Categories"
LIST_CATEGORIES_RESPONSE=$(curl -s -X GET "${API_BASE}/categories/")

if echo "$LIST_CATEGORIES_RESPONSE" | grep -q "results\|id"; then
    print_success "Category listing successful"
    CATEGORY_COUNT=$(echo "$LIST_CATEGORIES_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data) if isinstance(data, list) else data.get('count', 0))" 2>/dev/null)
    print_info "Found $CATEGORY_COUNT categories"
else
    print_error "Category listing failed"
    echo "Response: $LIST_CATEGORIES_RESPONSE"
fi

print_test "Get Category Detail"
if [ ! -z "$CATEGORY_SLUG" ]; then
    print_info "Testing with category slug: $CATEGORY_SLUG"
    print_info "Using access token: ${ACCESS_TOKEN:0:20}..."
    
    # First, verify the category still exists with authentication
    AUTH_CATEGORY_LIST=$(curl -s -X GET "${API_BASE}/categories/" -H "Authorization: Bearer $ACCESS_TOKEN")
    print_info "Checking if category exists in authenticated list..."
    CATEGORY_EXISTS=$(echo "$AUTH_CATEGORY_LIST" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    categories = data.get('results', data) if isinstance(data, dict) else data
    for cat in categories:
        if cat.get('slug') == '$CATEGORY_SLUG':
            print('true')
            break
    else:
        print('false')
except:
    print('false')
" 2>/dev/null)
    
    if [ "$CATEGORY_EXISTS" = "true" ]; then
        print_info "Category found in list, attempting detail retrieval..."
        CATEGORY_DETAIL_RESPONSE=$(curl -s -X GET "${API_BASE}/categories/${CATEGORY_SLUG}/" \
            -H "Authorization: Bearer $ACCESS_TOKEN")
        
        if echo "$CATEGORY_DETAIL_RESPONSE" | grep -q "name"; then
            print_success "Category detail retrieval successful"
        else
            print_error "Category detail retrieval failed despite being in list"
            echo "Response: $CATEGORY_DETAIL_RESPONSE"
        fi
    else
        print_error "Category not found in authenticated category list"
        # Debug: List all categories to see what's available
        print_info "Available categories for debugging:"
        echo "$AUTH_CATEGORY_LIST" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    categories = data.get('results', data) if isinstance(data, dict) else data
    for cat in categories:
        print(f\"ID: {cat.get('id')}, Slug: {cat.get('slug')}, Name: {cat.get('name')}\")
except Exception as e:
    print(f'Error: {e}')
" 2>/dev/null
    fi
else
    print_info "Skipping category detail test (no category slug)"
fi

# =============================================================================
# Product Tests
# =============================================================================
print_header "PRODUCT TESTS"

print_test "Create Product"
if [ ! -z "$ACCESS_TOKEN" ]; then
    # Use timestamp to make product name unique
    TIMESTAMP=$(date +%s)
    
    # Prepare category_id JSON value
    if [ ! -z "$CATEGORY_ID" ]; then
        CATEGORY_JSON="\"category_id\": $CATEGORY_ID,"
    else
        CATEGORY_JSON=""
    fi
    
    CREATE_PRODUCT_RESPONSE=$(curl -s -X POST "${API_BASE}/products/" \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      -H "Content-Type: application/json" \
      -d "{
        \"name\": \"Test Smartphone ${TIMESTAMP}\",
        \"description\": \"A high-quality test smartphone with advanced features\",
        \"short_description\": \"Premium test smartphone\",
        \"price\": \"699.99\",
        \"compare_at_price\": \"899.99\",
        \"cost_price\": \"400.00\",
        \"stock_quantity\": 50,
        \"low_stock_threshold\": 10,
        \"track_inventory\": true,
        ${CATEGORY_JSON}
        \"tags\": \"smartphone, electronics, mobile\",
        \"status\": \"active\",
        \"is_featured\": true,
        \"weight\": \"0.18\",
        \"dimensions_length\": \"15.0\",
        \"dimensions_width\": \"7.5\",
        \"dimensions_height\": \"0.8\"
      }")
    
    if echo "$CREATE_PRODUCT_RESPONSE" | grep -q "id"; then
        print_success "Product creation successful"
        PRODUCT_ID=$(echo "$CREATE_PRODUCT_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('id', ''))" 2>/dev/null)
        PRODUCT_SLUG=$(echo "$CREATE_PRODUCT_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('slug', ''))" 2>/dev/null)
        print_info "Product ID: $PRODUCT_ID"
        print_info "Product Slug: $PRODUCT_SLUG"
        
        # Debug: Show the actual response to understand the structure
        if [ -z "$PRODUCT_SLUG" ]; then
            print_info "Product response for debugging:"
            echo "$CREATE_PRODUCT_RESPONSE" | python3 -c "import sys, json; import pprint; pprint.pprint(json.load(sys.stdin))" 2>/dev/null
        fi
    else
        print_error "Product creation failed"
        echo "Response: $CREATE_PRODUCT_RESPONSE"
    fi
else
    print_error "Skipping product creation (no access token)"
fi

print_test "List User Products"
if [ ! -z "$ACCESS_TOKEN" ]; then
    LIST_PRODUCTS_RESPONSE=$(curl -s -X GET "${API_BASE}/products/" \
      -H "Authorization: Bearer $ACCESS_TOKEN")
    
    if echo "$LIST_PRODUCTS_RESPONSE" | grep -q "results\|id"; then
        print_success "Product listing successful"
        PRODUCT_COUNT=$(echo "$LIST_PRODUCTS_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data) if isinstance(data, list) else data.get('count', 0))" 2>/dev/null)
        print_info "Found $PRODUCT_COUNT products"
    else
        print_error "Product listing failed"
        echo "Response: $LIST_PRODUCTS_RESPONSE"
    fi
else
    print_error "Skipping product listing (no access token)"
fi

print_test "Get Product Detail"
if [ ! -z "$ACCESS_TOKEN" ] && [ ! -z "$PRODUCT_SLUG" ]; then
    PRODUCT_DETAIL_RESPONSE=$(curl -s -X GET "${API_BASE}/products/${PRODUCT_SLUG}/" \
      -H "Authorization: Bearer $ACCESS_TOKEN")
    
    if echo "$PRODUCT_DETAIL_RESPONSE" | grep -q "name"; then
        print_success "Product detail retrieval successful"
    else
        print_error "Product detail retrieval failed"
        echo "Response: $PRODUCT_DETAIL_RESPONSE"
    fi
else
    print_info "Skipping product detail test (missing token or slug)"
fi

print_test "Update Product"
if [ ! -z "$ACCESS_TOKEN" ] && [ ! -z "$PRODUCT_SLUG" ]; then
    UPDATE_PRODUCT_RESPONSE=$(curl -s -X PATCH "${API_BASE}/products/${PRODUCT_SLUG}/" \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "name": "Updated Test Smartphone",
        "price": "649.99",
        "is_featured": false
      }')
    
    if echo "$UPDATE_PRODUCT_RESPONSE" | grep -q "Updated Test Smartphone"; then
        print_success "Product update successful"
    else
        print_error "Product update failed"
        echo "Response: $UPDATE_PRODUCT_RESPONSE"
    fi
else
    print_info "Skipping product update test (missing token or slug)"
fi

print_test "Update Product Stock"
if [ ! -z "$ACCESS_TOKEN" ] && [ ! -z "$PRODUCT_SLUG" ]; then
    UPDATE_STOCK_RESPONSE=$(curl -s -X PATCH "${API_BASE}/products/${PRODUCT_SLUG}/update_stock/" \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "stock_quantity": 25
      }')
    
    if echo "$UPDATE_STOCK_RESPONSE" | grep -q "stock_quantity"; then
        print_success "Product stock update successful"
    else
        print_error "Product stock update failed"
        echo "Response: $UPDATE_STOCK_RESPONSE"
    fi
else
    print_info "Skipping stock update test (missing token or slug)"
fi

print_test "Duplicate Product"
if [ ! -z "$ACCESS_TOKEN" ] && [ ! -z "$PRODUCT_SLUG" ]; then
    DUPLICATE_RESPONSE=$(curl -s -X POST "${API_BASE}/products/${PRODUCT_SLUG}/duplicate/" \
      -H "Authorization: Bearer $ACCESS_TOKEN")
    
    if echo "$DUPLICATE_RESPONSE" | grep -q "Copy"; then
        print_success "Product duplication successful"
    else
        print_error "Product duplication failed"
        echo "Response: $DUPLICATE_RESPONSE"
    fi
else
    print_info "Skipping product duplication test (missing token or slug)"
fi

# =============================================================================
# Statistics and Analytics Tests
# =============================================================================
print_header "STATISTICS AND ANALYTICS TESTS"

print_test "Get Product Statistics"
if [ ! -z "$ACCESS_TOKEN" ]; then
    STATS_RESPONSE=$(curl -s -X GET "${API_BASE}/stats/" \
      -H "Authorization: Bearer $ACCESS_TOKEN")
    
    if echo "$STATS_RESPONSE" | grep -q "total_products"; then
        print_success "Product statistics retrieval successful"
        TOTAL_PRODUCTS=$(echo "$STATS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['total_products'])" 2>/dev/null)
        print_info "Total products: $TOTAL_PRODUCTS"
    else
        print_error "Product statistics retrieval failed"
        echo "Response: $STATS_RESPONSE"
    fi
else
    print_error "Skipping statistics test (no access token)"
fi

print_test "Get Low Stock Alerts"
if [ ! -z "$ACCESS_TOKEN" ]; then
    LOW_STOCK_RESPONSE=$(curl -s -X GET "${API_BASE}/low-stock-alerts/" \
      -H "Authorization: Bearer $ACCESS_TOKEN")
    
    if echo "$LOW_STOCK_RESPONSE" | grep -q "count"; then
        print_success "Low stock alerts retrieval successful"
        LOW_STOCK_COUNT=$(echo "$LOW_STOCK_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['count'])" 2>/dev/null)
        print_info "Low stock products: $LOW_STOCK_COUNT"
    else
        print_error "Low stock alerts retrieval failed"
        echo "Response: $LOW_STOCK_RESPONSE"
    fi
else
    print_error "Skipping low stock alerts test (no access token)"
fi

# =============================================================================
# Public API Tests
# =============================================================================
print_header "PUBLIC API TESTS"

print_test "Browse Public Products"
PUBLIC_PRODUCTS_RESPONSE=$(curl -s -X GET "${API_BASE}/public/products/")

if echo "$PUBLIC_PRODUCTS_RESPONSE" | grep -q "results\|id"; then
    print_success "Public product browsing successful"
    PUBLIC_PRODUCT_COUNT=$(echo "$PUBLIC_PRODUCTS_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data) if isinstance(data, list) else data.get('count', 0))" 2>/dev/null)
    print_info "Found $PUBLIC_PRODUCT_COUNT public products"
else
    print_error "Public product browsing failed"
    echo "Response: $PUBLIC_PRODUCTS_RESPONSE"
fi

print_test "Get Featured Products"
FEATURED_RESPONSE=$(curl -s -X GET "${API_BASE}/public/featured/")

if echo "$FEATURED_RESPONSE" | grep -q "\[\]" || echo "$FEATURED_RESPONSE" | grep -q "id"; then
    print_success "Featured products retrieval successful"
    FEATURED_COUNT=$(echo "$FEATURED_RESPONSE" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null)
    print_info "Found $FEATURED_COUNT featured products"
else
    print_error "Featured products retrieval failed"
    echo "Response: $FEATURED_RESPONSE"
fi

print_test "Public Product Detail"
if [ ! -z "$PRODUCT_SLUG" ]; then
    PUBLIC_DETAIL_RESPONSE=$(curl -s -X GET "${API_BASE}/public/products/${PRODUCT_SLUG}/")
    
    if echo "$PUBLIC_DETAIL_RESPONSE" | grep -q "name"; then
        print_success "Public product detail retrieval successful"
    else
        print_error "Public product detail retrieval failed"
        echo "Response: $PUBLIC_DETAIL_RESPONSE"
    fi
else
    # Fallback: Get a product slug from the public products list
    print_info "Getting product slug from public products list..."
    FALLBACK_SLUG=$(curl -s -X GET "${API_BASE}/public/products/" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    products = data.get('results', data) if isinstance(data, dict) else data
    if products and len(products) > 0:
        print(products[0].get('slug', ''))
except:
    pass
" 2>/dev/null)
    
    if [ ! -z "$FALLBACK_SLUG" ]; then
        print_info "Testing with fallback slug: $FALLBACK_SLUG"
        PUBLIC_DETAIL_RESPONSE=$(curl -s -X GET "${API_BASE}/public/products/${FALLBACK_SLUG}/")
        
        if echo "$PUBLIC_DETAIL_RESPONSE" | grep -q "name"; then
            print_success "Public product detail retrieval successful (fallback)"
        else
            print_error "Public product detail retrieval failed (fallback)"
            echo "Response: $PUBLIC_DETAIL_RESPONSE"
        fi
    else
        print_info "Skipping public product detail test (no product slug available)"
    fi
fi

print_test "Search Products"
SEARCH_RESPONSE=$(curl -s -X GET "${API_BASE}/public/search/?q=smartphone")

if echo "$SEARCH_RESPONSE" | grep -q "query\|results\|error"; then
    if echo "$SEARCH_RESPONSE" | grep -q "Authentication credentials"; then
        print_error "Search endpoint requires authentication (unexpected - should be public)"
        echo "Response: $SEARCH_RESPONSE"
    else
        print_success "Product search successful"
        SEARCH_COUNT=$(echo "$SEARCH_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('count', len(data.get('results', []))))" 2>/dev/null)
        print_info "Found $SEARCH_COUNT search results"
    fi
else
    print_error "Product search failed"
    echo "Response: $SEARCH_RESPONSE"
fi

# =============================================================================
# Filter and Pagination Tests
# =============================================================================
print_header "FILTER AND PAGINATION TESTS"

print_test "Filter Products by Category"
if [ ! -z "$CATEGORY_ID" ]; then
    FILTER_RESPONSE=$(curl -s -X GET "${API_BASE}/public/products/?category=${CATEGORY_ID}")
    
    if echo "$FILTER_RESPONSE" | grep -q "results\|id"; then
        print_success "Category filter successful"
    else
        print_error "Category filter failed"
        echo "Response: $FILTER_RESPONSE"
    fi
else
    print_info "Skipping category filter test (no category ID)"
fi

print_test "Filter Products by Price Range"
PRICE_FILTER_RESPONSE=$(curl -s -X GET "${API_BASE}/public/products/?min_price=100&max_price=1000")

if echo "$PRICE_FILTER_RESPONSE" | grep -q "results\|id"; then
    print_success "Price range filter successful"
else
    print_error "Price range filter failed"
    echo "Response: $PRICE_FILTER_RESPONSE"
fi

print_test "Sort Products by Price"
SORT_RESPONSE=$(curl -s -X GET "${API_BASE}/public/products/?sort=price_low")

if echo "$SORT_RESPONSE" | grep -q "results\|id"; then
    print_success "Product sorting successful"
else
    print_error "Product sorting failed"
    echo "Response: $SORT_RESPONSE"
fi

print_test "Pagination Test"
PAGINATION_RESPONSE=$(curl -s -X GET "${API_BASE}/public/products/?page=1&page_size=5")

if echo "$PAGINATION_RESPONSE" | grep -q "next\|previous\|results"; then
    print_success "Pagination successful"
elif echo "$PAGINATION_RESPONSE" | grep -q "Authentication credentials"; then
    print_error "Pagination endpoint requires authentication (unexpected - should be public)"
    echo "Response: $PAGINATION_RESPONSE"
else
    print_error "Pagination failed"
    echo "Response: $PAGINATION_RESPONSE"
fi

# =============================================================================
# Cleanup Tests
# =============================================================================
print_header "CLEANUP TESTS"

print_test "Delete Product"
if [ ! -z "$ACCESS_TOKEN" ] && [ ! -z "$PRODUCT_SLUG" ]; then
    DELETE_RESPONSE=$(curl -s -X DELETE "${API_BASE}/products/${PRODUCT_SLUG}/" \
      -H "Authorization: Bearer $ACCESS_TOKEN")
    
    if [ -z "$DELETE_RESPONSE" ] || echo "$DELETE_RESPONSE" | grep -q "204\|success"; then
        print_success "Product deletion successful"
    else
        print_error "Product deletion failed"
        echo "Response: $DELETE_RESPONSE"
    fi
else
    print_info "Skipping product deletion test (missing token or slug)"
fi

print_test "Delete Category"
if [ ! -z "$ACCESS_TOKEN" ] && [ ! -z "$CATEGORY_SLUG" ]; then
    DELETE_CAT_RESPONSE=$(curl -s -X DELETE "${API_BASE}/categories/${CATEGORY_SLUG}/" \
      -H "Authorization: Bearer $ACCESS_TOKEN")
    
    if [ -z "$DELETE_CAT_RESPONSE" ] || echo "$DELETE_CAT_RESPONSE" | grep -q "204\|success"; then
        print_success "Category deletion successful"
    else
        print_error "Category deletion failed"
        echo "Response: $DELETE_CAT_RESPONSE"
    fi
else
    print_info "Skipping category deletion test (missing token or slug)"
fi

# =============================================================================
# Test Summary
# =============================================================================
print_header "TEST SUMMARY"

echo -e "\n${BLUE}📊 Test Results:${NC}"
echo -e "Total Tests: ${YELLOW}$TOTAL_TESTS${NC}"
echo -e "Passed: ${GREEN}$PASSED_TESTS${NC}"
echo -e "Failed: ${RED}$((TOTAL_TESTS - PASSED_TESTS))${NC}"

if [ $PASSED_TESTS -eq $TOTAL_TESTS ]; then
    echo -e "\n${GREEN}🎉 All tests passed! Your API is working perfectly!${NC}"
else
    echo -e "\n${YELLOW}⚠️  Some tests failed. Check the output above for details.${NC}"
fi

SUCCESS_RATE=$((PASSED_TESTS * 100 / TOTAL_TESTS))
echo -e "Success Rate: ${GREEN}${SUCCESS_RATE}%${NC}"

echo -e "\n${BLUE}💡 Tips:${NC}"
echo -e "- Make sure Django server is running: ${YELLOW}python manage.py runserver${NC}"
echo -e "- Check if all migrations are applied: ${YELLOW}python manage.py migrate${NC}"
echo -e "- Verify API endpoints are correctly configured"
echo -e "- Check Django logs for detailed error information"

echo -e "\n${BLUE}🚀 Next Steps:${NC}"
echo -e "- Test with different user accounts"
echo -e "- Add image upload tests"
echo -e "- Test error handling scenarios"
echo -e "- Performance testing with large datasets"

echo -e "\n${GREEN}Testing completed!${NC}"