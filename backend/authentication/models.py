import uuid
from datetime import timedelta

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class EmailVerificationToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(
                hours=24
            )  # Token expires in 24 hours
        super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"Email verification for {self.user.username}"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    email_verified = models.BooleanField(default=False)
    email_verified_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Profile for {self.user.username}"
    
# What These Models Do
# EmailVerificationToken Model:

# Creates unique verification tokens for email confirmation
# Automatically sets expiration to 24 hours when saved
# Tracks whether the token has been used
# The is_expired() method checks if the current time is past the expiration
# UserProfile Model:

# Extends Django's built-in User model with email verification status
# Uses OneToOneField to create a 1:1 relationship with User
# Tracks when email was verified with a timestamp
# Key Django Concepts Here
# Foreign Key Relationships: ForeignKey (many EmailVerificationTokens per User) vs OneToOneField (one UserProfile per User)

# Model Methods: The save() method is overridden to automatically set expiration dates - this is a common Django pattern

# UUID Fields: Using uuid.uuid4 as the default creates cryptographically secure random tokens

# Timezone Awareness: timezone.now() respects Django's timezone settings, which is crucial for international applications

# Consider adding an index on the token field for faster lookups: