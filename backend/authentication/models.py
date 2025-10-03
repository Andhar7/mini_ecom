import uuid
from datetime import timedelta
from typing import Optional

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class EmailVerificationTokenManager(models.Manager):
    """Custom manager for EmailVerificationToken with utility methods."""

    def create_for_user(self, user: User) -> "EmailVerificationToken":
        """
        Create a new verification token for a user.
        Automatically handles token cleanup and creation.
        """
        # Clean up old unused tokens for this user
        self.filter(user=user, used=False).delete()

        # Create new token
        return self.create(user=user)

    def get_valid_token(self, token: str) -> Optional["EmailVerificationToken"]:
        """
        Get a valid (not used, not expired) token.
        Returns None if token is invalid.
        """
        try:
            token_obj = self.select_related("user").get(token=token, used=False)
            if not token_obj.is_expired():
                return token_obj
        except self.model.DoesNotExist:
            pass
        return None

    def cleanup_expired(self) -> int:
        """
        Remove expired tokens from database.
        Returns number of tokens deleted.
        """
        expired_tokens = self.filter(expires_at__lt=timezone.now())
        count = expired_tokens.count()
        expired_tokens.delete()
        return count


class EmailVerificationToken(models.Model):
    """
    Model for managing email verification tokens.

    Features:
    - Automatic expiration handling
    - Secure UUID-based tokens
    - Usage tracking
    - Database optimization with indexes
    """

    # Constants
    DEFAULT_EXPIRY_HOURS = 24

    # Fields
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="verification_tokens",
        verbose_name=_("User"),
        help_text=_("The user this verification token belongs to"),
    )
    token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        db_index=True,
        verbose_name=_("Token"),
        help_text=_("Unique verification token"),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created at"),
        help_text=_("When this token was created"),
    )
    expires_at = models.DateTimeField(
        verbose_name=_("Expires at"), help_text=_("When this token expires")
    )
    used = models.BooleanField(
        default=False,
        verbose_name=_("Used"),
        help_text=_("Whether this token has been used"),
    )
    used_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Used at"),
        help_text=_("When this token was used"),
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=_("IP Address"),
        help_text=_("IP address where token was created"),
    )

    # Custom manager
    objects = EmailVerificationTokenManager()

    class Meta:
        verbose_name = _("Email Verification Token")
        verbose_name_plural = _("Email Verification Tokens")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "used", "expires_at"]),
            models.Index(fields=["token"]),
            models.Index(fields=["expires_at"]),
        ]

    def save(self, *args, **kwargs):
        """Override save to set expiration time if not provided."""
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(
                hours=self.DEFAULT_EXPIRY_HOURS
            )
        super().save(*args, **kwargs)

    def clean(self):
        """Model validation."""
        if self.expires_at and self.expires_at <= timezone.now():
            raise ValidationError(_("Expiration time must be in the future"))

        if self.used_at and not self.used:
            raise ValidationError(
                _("Token cannot have used_at without being marked as used")
            )

    def is_expired(self) -> bool:
        """Check if token has expired."""
        return timezone.now() > self.expires_at

    def is_valid(self) -> bool:
        """Check if token is valid (not used and not expired)."""
        return not self.used and not self.is_expired()

    def mark_as_used(self, ip_address: Optional[str] = None) -> None:
        """Mark token as used with optional IP tracking."""
        self.used = True
        self.used_at = timezone.now()
        if ip_address:
            self.ip_address = ip_address
        self.save(update_fields=["used", "used_at", "ip_address"])

    def time_until_expiry(self) -> timedelta:
        """Get time remaining until expiry."""
        return self.expires_at - timezone.now()

    @property
    def is_recently_created(self) -> bool:
        """Check if token was created in the last 5 minutes."""
        return timezone.now() - self.created_at < timedelta(minutes=5)

    def __str__(self):
        status = "Used" if self.used else ("Expired" if self.is_expired() else "Active")
        return f"Email verification for {self.user.username} ({status})"


class UserProfileManager(models.Manager):
    """Custom manager for UserProfile with utility methods."""

    def verified_users(self):
        """Get all profiles with verified emails."""
        return self.filter(email_verified=True)

    def unverified_users(self):
        """Get all profiles with unverified emails."""
        return self.filter(email_verified=False)

    def recently_verified(self, days: int = 7):
        """Get profiles verified in the last N days."""
        since = timezone.now() - timedelta(days=days)
        return self.filter(email_verified=True, email_verified_at__gte=since)


class UserProfile(models.Model):
    """
    Extended user profile model.

    Features:
    - Email verification tracking
    - Timestamps for audit trail
    - Extensible for future profile fields
    - Database optimization
    """

    # Core fields
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name=_("User"),
        help_text=_("The user this profile belongs to"),
    )

    # Email verification
    email_verified = models.BooleanField(
        default=False,
        verbose_name=_("Email Verified"),
        help_text=_("Whether the user has verified their email address"),
    )
    email_verified_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Email Verified At"),
        help_text=_("When the email was verified"),
    )

    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At"),
        help_text=_("When this profile was created"),
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated At"),
        help_text=_("When this profile was last updated"),
    )

    # Future extensibility fields
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_("Phone Number"),
        help_text=_("User phone number"),
    )
    birth_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Birth Date"),
        help_text=_("User birth date"),
    )
    avatar = models.ImageField(
        upload_to="avatars/",
        null=True,
        blank=True,
        verbose_name=_("Avatar"),
        help_text=_("User profile picture"),
    )
    bio = models.TextField(
        max_length=500, blank=True, verbose_name=_("Bio"), help_text=_("User biography")
    )

    # Custom manager
    objects = UserProfileManager()

    class Meta:
        verbose_name = _("User Profile")
        verbose_name_plural = _("User Profiles")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["email_verified"]),
            models.Index(fields=["email_verified_at"]),
            models.Index(fields=["created_at"]),
        ]

    def clean(self):
        """Model validation."""
        if self.email_verified and not self.email_verified_at:
            raise ValidationError(
                _("Email verified date must be set if email is verified")
            )

        if not self.email_verified and self.email_verified_at:
            raise ValidationError(
                _("Email verified date should not be set if email is not verified")
            )

    def verify_email(self) -> None:
        """Mark email as verified with timestamp."""
        if not self.email_verified:
            self.email_verified = True
            self.email_verified_at = timezone.now()
            self.save(update_fields=["email_verified", "email_verified_at"])

    def unverify_email(self) -> None:
        """Mark email as unverified (admin use)."""
        if self.email_verified:
            self.email_verified = False
            self.email_verified_at = None
            self.save(update_fields=["email_verified", "email_verified_at"])

    @property
    def verification_age(self) -> Optional[timedelta]:
        """Get time since email was verified."""
        if self.email_verified_at:
            return timezone.now() - self.email_verified_at
        return None

    @property
    def is_recently_verified(self) -> bool:
        """Check if email was verified in the last 24 hours."""
        if self.verification_age:
            return self.verification_age < timedelta(days=1)
        return False

    @property
    def profile_completion_percentage(self) -> int:
        """Calculate profile completion percentage."""
        total_fields = 8  # Total optional fields
        completed_fields = 0

        if self.phone_number:
            completed_fields += 1
        if self.birth_date:
            completed_fields += 1
        if self.avatar:
            completed_fields += 1
        if self.bio:
            completed_fields += 1
        if self.email_verified:
            completed_fields += 1
        if self.user.first_name:
            completed_fields += 1
        if self.user.last_name:
            completed_fields += 1
        if self.user.email:
            completed_fields += 1

        return int((completed_fields / total_fields) * 100)

    def __str__(self):
        verification_status = "✓" if self.email_verified else "✗"
        return f"Profile for {self.user.username} {verification_status}"
