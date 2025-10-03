from authentication.models import EmailVerificationToken, UserProfile
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create sample data for testing authentication models"

    def handle(self, *args, **options):
        self.stdout.write("Creating sample data...")

        # Create sample users
        users_data = [
            {
                "username": "Andrej Kling",
                "email": "andrej@example.com",
                "first_name": "Andrej",
                "last_name": "Kling",
            },
            {
                "username": "john_doe",
                "email": "john@example.com",
                "first_name": "John",
                "last_name": "Doe",
            },
            {
                "username": "jane_smith",
                "email": "jane@example.com",
                "first_name": "Jane",
                "last_name": "Smith",
            },
            {
                "username": "bob_wilson",
                "email": "bob@example.com",
                "first_name": "Bob",
                "last_name": "Wilson",
            },
        ]

        created_users = []
        for user_data in users_data:
            user, created = User.objects.get_or_create(
                username=user_data["username"],
                defaults={
                    "email": user_data["email"],
                    "first_name": user_data["first_name"],
                    "last_name": user_data["last_name"],
                    "is_active": True,
                },
            )
            if created:
                user.set_password("testpass123")
                user.save()
                created_users.append(user)
                self.stdout.write(f"✅ Created user: {user.username}")
            else:
                self.stdout.write(f"⚠️  User already exists: {user.username}")

        # Create profiles and verify some emails
        for i, user in enumerate(User.objects.all()):
            profile, created = UserProfile.objects.get_or_create(user=user)
            if created:
                self.stdout.write(f"✅ Created profile for: {user.username}")

            # Verify email for some users
            if i % 2 == 0 and not profile.email_verified:  # Every other user
                profile.verify_email()
                self.stdout.write(f"✅ Verified email for: {user.username}")

            # Add some sample profile data
            if i == 0 and not profile.phone_number:
                profile.phone_number = "+1234567890"
                profile.bio = "Sample bio for user profile testing"
                profile.save()
                self.stdout.write(f"✅ Added profile data for: {user.username}")

        # Create some verification tokens
        token_count = 0
        for user in User.objects.all()[:2]:
            try:
                token = EmailVerificationToken.objects.create_for_user(user)
                token_count += 1
                self.stdout.write(f"✅ Created token for: {user.username}")
            except Exception as e:
                self.stdout.write(f"❌ Failed to create token for {user.username}: {e}")

        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f"\n🎉 Sample data creation completed!\n"
                f"📊 Summary:\n"
                f"   Users: {User.objects.count()}\n"
                f"   Profiles: {UserProfile.objects.count()}\n"
                f"   Verified users: {UserProfile.objects.verified_users().count()}\n"
                f"   Verification tokens: {EmailVerificationToken.objects.count()}\n"
            )
        )


# python manage.py create_sample_data

# mkdir -p authentication/management/commands
# touch authentication/management/__init__.py
# touch authentication/management/commands/__init__.py
# touch authentication/management/commands/create_sample_data.py


# authentication/
# ├── management/           # Directory
# │   ├── __init__.py      # File (makes it a Python package)
# │   └── commands/        # Directory
# │       ├── __init__.py  # File (makes it a Python package)
# │       └── create_sample_data.py  # File (your custom command)
# ├── models.py
# ├── views.py
# └── ...
