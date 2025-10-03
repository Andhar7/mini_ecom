#!/bin/bash

# Create superuser for API testing
echo "Creating superuser for API testing..."

# Create superuser with environment variables
export DJANGO_SUPERUSER_USERNAME=admin
export DJANGO_SUPERUSER_EMAIL=admin@example.com  
export DJANGO_SUPERUSER_PASSWORD=admin123

# Try to create superuser, ignore error if already exists
python manage.py createsuperuser --noinput --username admin --email admin@example.com 2>/dev/null || echo "Admin user already exists"

echo "Superuser created:"
echo "Username: admin"
echo "Password: admin123"
echo "Email: admin@example.com"
echo ""

# Now run a Django shell command to verify the admin user's email
echo "Verifying admin user's email..."
python manage.py shell -c "
from django.contrib.auth.models import User
from authentication.models import UserProfile

try:
    admin_user = User.objects.get(username='admin')
    profile, created = UserProfile.objects.get_or_create(user=admin_user)
    if not profile.email_verified:
        profile.verify_email()
        print('✅ Admin user email verified')
    else:
        print('✅ Admin user email was already verified')
except User.DoesNotExist:
    print('❌ Admin user not found')
except Exception as e:
    print(f'❌ Error: {e}')
"

echo ""
echo "You can now run the API tests with: ./test_api_endpoints.sh"