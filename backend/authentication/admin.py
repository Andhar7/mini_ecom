from datetime import timedelta

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from .models import EmailVerificationToken, UserProfile


class EmailVerificationTokenInline(admin.TabularInline):
    """Inline admin for EmailVerificationToken."""

    model = EmailVerificationToken
    extra = 0
    readonly_fields = ("token", "created_at", "expires_at", "used_at", "ip_address")
    fields = ("token", "created_at", "expires_at", "used", "used_at", "ip_address")
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


class UserProfileInline(admin.StackedInline):
    """Inline admin for UserProfile."""

    model = UserProfile
    can_delete = False
    readonly_fields = (
        "created_at",
        "updated_at",
        "email_verified_at",
        "profile_completion_display",
    )
    fieldsets = (
        (_("Email Verification"), {"fields": ("email_verified", "email_verified_at")}),
        (
            _("Profile Information"),
            {"fields": ("phone_number", "birth_date", "avatar", "bio")},
        ),
        (
            _("System Information"),
            {
                "fields": ("profile_completion_display", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def profile_completion_display(self, obj):
        """Display profile completion percentage with visual indicator."""
        if obj:
            percentage = obj.profile_completion_percentage
            color = (
                "green" if percentage >= 80 else "orange" if percentage >= 50 else "red"
            )
            return format_html(
                '<div style="width: 100px; background-color: #f0f0f0; border-radius: 3px;">'
                '<div style="width: {}%; background-color: {}; height: 20px; border-radius: 3px; '
                'text-align: center; line-height: 20px; color: white; font-weight: bold;">'
                "{}%</div></div>",
                percentage,
                color,
                percentage,
            )
        return "-"

    profile_completion_display.short_description = _("Profile Completion")


@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
    """Professional admin interface for EmailVerificationToken."""

    list_display = [
        "user_link",
        "token_short",
        "status_display",
        "created_at",
        "expires_at",
        "time_until_expiry_display",
        "ip_address",
    ]
    list_filter = [
        "used",
        "created_at",
        "expires_at",
        ("user__is_active", admin.BooleanFieldListFilter),
        ("user__profile__email_verified", admin.BooleanFieldListFilter),
    ]
    search_fields = [
        "user__username",
        "user__email",
        "user__first_name",
        "user__last_name",
        "token",
    ]
    readonly_fields = [
        "token",
        "created_at",
        "expires_at",
        "used_at",
        "time_until_expiry_display",
        "is_expired_display",
        "is_valid_display",
    ]
    date_hierarchy = "created_at"
    ordering = ["-created_at"]

    fieldsets = (
        (_("Token Information"), {"fields": ("user", "token", "status_display")}),
        (
            _("Timing"),
            {"fields": ("created_at", "expires_at", "time_until_expiry_display")},
        ),
        (_("Usage"), {"fields": ("used", "used_at", "ip_address")}),
        (
            _("Status Checks"),
            {
                "fields": ("is_expired_display", "is_valid_display"),
                "classes": ("collapse",),
            },
        ),
    )

    actions = ["mark_as_used", "cleanup_expired_tokens", "extend_expiry"]

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related("user", "user__profile")

    def user_link(self, obj):
        """Display user as clickable link."""
        url = reverse("admin:auth_user_change", args=[obj.user.pk])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)

    user_link.short_description = _("User")
    user_link.admin_order_field = "user__username"

    def token_short(self, obj):
        """Display shortened token with copy functionality."""
        token_str = str(obj.token)
        short = f"{token_str[:8]}...{token_str[-8:]}"
        return format_html(
            '<span title="{}" style="font-family: monospace; cursor: help;">{}</span>',
            token_str,
            short,
        )

    token_short.short_description = _("Token")
    token_short.admin_order_field = "token"

    def status_display(self, obj):
        """Display token status with colored indicators."""
        if obj.used:
            return format_html(
                '<span style="color: #28a745; font-weight: bold;">✓ Used</span>'
            )
        elif obj.is_expired():
            return format_html(
                '<span style="color: #dc3545; font-weight: bold;">✗ Expired</span>'
            )
        else:
            return format_html(
                '<span style="color: #007bff; font-weight: bold;">● Active</span>'
            )

    status_display.short_description = _("Status")

    def time_until_expiry_display(self, obj):
        """Display time until expiry with color coding."""
        if obj.used:
            return format_html('<span style="color: #6c757d;">N/A (Used)</span>')

        time_left = obj.time_until_expiry()
        if time_left.total_seconds() <= 0:
            return format_html(
                '<span style="color: #dc3545; font-weight: bold;">Expired</span>'
            )

        # Color code based on time remaining
        total_seconds = time_left.total_seconds()
        if total_seconds < 3600:  # Less than 1 hour
            color = "#dc3545"  # Red
        elif total_seconds < 86400:  # Less than 24 hours
            color = "#ffc107"  # Yellow
        else:
            color = "#28a745"  # Green

        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            self._format_timedelta(time_left),
        )

    time_until_expiry_display.short_description = _("Time Until Expiry")

    def is_expired_display(self, obj):
        """Display expiration status."""
        expired = obj.is_expired()
        color = "#dc3545" if expired else "#28a745"
        text = "Yes" if expired else "No"
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>', color, text
        )

    is_expired_display.short_description = _("Is Expired")

    def is_valid_display(self, obj):
        """Display validity status."""
        valid = obj.is_valid()
        color = "#28a745" if valid else "#dc3545"
        text = "Yes" if valid else "No"
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>', color, text
        )

    is_valid_display.short_description = _("Is Valid")

    def _format_timedelta(self, td):
        """Format timedelta for display."""
        days = td.days
        hours, remainder = divmod(td.seconds, 3600)
        minutes, _ = divmod(remainder, 60)

        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"

    # Admin Actions
    def mark_as_used(self, request, queryset):
        """Mark selected tokens as used."""
        count = 0
        for token in queryset.filter(used=False):
            if not token.is_expired():
                token.mark_as_used()
                count += 1

        self.message_user(
            request,
            f"{count} token(s) marked as used.",
            level="SUCCESS" if count > 0 else "WARNING",
        )

    mark_as_used.short_description = _("Mark selected tokens as used")

    def cleanup_expired_tokens(self, request, queryset):
        """Delete expired tokens."""
        expired_count = queryset.filter(expires_at__lt=timezone.now()).count()
        deleted_count = queryset.filter(expires_at__lt=timezone.now()).delete()[0]

        self.message_user(
            request,
            f"{deleted_count} expired token(s) deleted.",
            level="SUCCESS" if deleted_count > 0 else "INFO",
        )

    cleanup_expired_tokens.short_description = _("Delete expired tokens")

    def extend_expiry(self, request, queryset):
        """Extend expiry of selected tokens by 24 hours."""
        count = 0
        for token in queryset.filter(used=False):
            token.expires_at = timezone.now() + timedelta(hours=24)
            token.save(update_fields=["expires_at"])
            count += 1

        self.message_user(
            request,
            f"{count} token(s) expiry extended by 24 hours.",
            level="SUCCESS" if count > 0 else "WARNING",
        )

    extend_expiry.short_description = _("Extend expiry by 24 hours")


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Professional admin interface for UserProfile."""

    list_display = [
        "user_link",
        "email_verified_display",
        "profile_completion_bar",
        "created_at",
        "updated_at",
        "verification_age_display",
    ]
    list_filter = [
        "email_verified",
        "created_at",
        "updated_at",
        ("birth_date", admin.DateFieldListFilter),
        ("user__is_active", admin.BooleanFieldListFilter),
        ("user__date_joined", admin.DateFieldListFilter),
    ]
    search_fields = [
        "user__username",
        "user__email",
        "user__first_name",
        "user__last_name",
        "phone_number",
        "bio",
    ]
    readonly_fields = [
        "created_at",
        "updated_at",
        "email_verified_at",
        "profile_completion_display",
        "verification_age_display",
        "user_info_display",
    ]
    date_hierarchy = "created_at"
    ordering = ["-created_at"]

    fieldsets = (
        (_("User Information"), {"fields": ("user", "user_info_display")}),
        (
            _("Email Verification"),
            {
                "fields": (
                    "email_verified",
                    "email_verified_at",
                    "verification_age_display",
                )
            },
        ),
        (
            _("Profile Details"),
            {"fields": ("phone_number", "birth_date", "avatar", "bio")},
        ),
        (
            _("System Information"),
            {
                "fields": ("profile_completion_display", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    actions = ["verify_emails", "unverify_emails", "send_verification_reminder"]

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related("user")

    def user_link(self, obj):
        """Display user as clickable link with additional info."""
        url = reverse("admin:auth_user_change", args=[obj.user.pk])
        active_badge = "✓" if obj.user.is_active else "✗"
        return format_html(
            '<a href="{}">{}</a> <span style="color: {};">{}</span>',
            url,
            obj.user.username,
            "#28a745" if obj.user.is_active else "#dc3545",
            active_badge,
        )

    user_link.short_description = _("User")
    user_link.admin_order_field = "user__username"

    def email_verified_display(self, obj):
        """Display email verification status with date."""
        if obj.email_verified:
            date_str = (
                obj.email_verified_at.strftime("%Y-%m-%d")
                if obj.email_verified_at
                else "Unknown"
            )
            return format_html(
                '<span style="color: #28a745; font-weight: bold;">✓</span> {}', date_str
            )
        else:
            return format_html(
                '<span style="color: #dc3545; font-weight: bold;">✗ Not Verified</span>'
            )

    email_verified_display.short_description = _("Email Verified")
    email_verified_display.admin_order_field = "email_verified"

    def profile_completion_bar(self, obj):
        """Display profile completion as a progress bar."""
        percentage = obj.profile_completion_percentage
        color = (
            "#28a745"
            if percentage >= 80
            else "#ffc107" if percentage >= 50 else "#dc3545"
        )

        return format_html(
            '<div style="width: 100px; background-color: #e9ecef; border-radius: 3px; overflow: hidden;">'
            '<div style="width: {}%; background-color: {}; height: 20px; text-align: center; '
            'line-height: 20px; color: white; font-size: 12px; font-weight: bold;">'
            "{}%</div></div>",
            percentage,
            color,
            percentage,
        )

    profile_completion_bar.short_description = _("Completion")

    def profile_completion_display(self, obj):
        """Detailed profile completion display."""
        percentage = obj.profile_completion_percentage
        color = (
            "#28a745"
            if percentage >= 80
            else "#ffc107" if percentage >= 50 else "#dc3545"
        )

        # Count completed fields
        fields_info = []
        if obj.user.first_name:
            fields_info.append("First Name")
        if obj.user.last_name:
            fields_info.append("Last Name")
        if obj.user.email:
            fields_info.append("Email")
        if obj.email_verified:
            fields_info.append("Email Verified")
        if obj.phone_number:
            fields_info.append("Phone")
        if obj.birth_date:
            fields_info.append("Birth Date")
        if obj.avatar:
            fields_info.append("Avatar")
        if obj.bio:
            fields_info.append("Bio")

        return format_html(
            '<div style="margin-bottom: 10px;">'
            '<div style="width: 200px; background-color: #e9ecef; border-radius: 3px; overflow: hidden;">'
            '<div style="width: {}%; background-color: {}; height: 25px; text-align: center; '
            'line-height: 25px; color: white; font-weight: bold;">{}%</div></div>'
            '<div style="margin-top: 5px; font-size: 12px;">Completed: {}</div>'
            "</div>",
            percentage,
            color,
            percentage,
            ", ".join(fields_info) if fields_info else "None",
        )

    profile_completion_display.short_description = _("Profile Completion Details")

    def verification_age_display(self, obj):
        """Display how long ago email was verified."""
        if not obj.email_verified or not obj.email_verified_at:
            return format_html('<span style="color: #6c757d;">Not verified</span>')

        age = obj.verification_age
        if age.days > 0:
            return format_html("{} days ago", age.days)
        elif age.seconds > 3600:
            hours = age.seconds // 3600
            return format_html("{} hours ago", hours)
        else:
            minutes = age.seconds // 60
            return format_html("{} minutes ago", minutes)

    verification_age_display.short_description = _("Verified")

    def user_info_display(self, obj):
        """Display comprehensive user information."""
        user = obj.user
        info_html = f"""
        <table style="width: 100%; font-size: 13px;">
            <tr><th style="text-align: left; padding: 2px;">Username:</th><td>{user.username}</td></tr>
            <tr><th style="text-align: left; padding: 2px;">Email:</th><td>{user.email or 'Not set'}</td></tr>
            <tr><th style="text-align: left; padding: 2px;">Name:</th><td>{user.get_full_name() or 'Not set'}</td></tr>
            <tr><th style="text-align: left; padding: 2px;">Status:</th><td>{'Active' if user.is_active else 'Inactive'}</td></tr>
            <tr><th style="text-align: left; padding: 2px;">Staff:</th><td>{'Yes' if user.is_staff else 'No'}</td></tr>
            <tr><th style="text-align: left; padding: 2px;">Joined:</th><td>{user.date_joined.strftime('%Y-%m-%d %H:%M')}</td></tr>
            <tr><th style="text-align: left; padding: 2px;">Last Login:</th><td>{user.last_login.strftime('%Y-%m-%d %H:%M') if user.last_login else 'Never'}</td></tr>
        </table>
        """
        return mark_safe(info_html)

    user_info_display.short_description = _("User Details")

    # Admin Actions
    def verify_emails(self, request, queryset):
        """Mark selected profiles as email verified."""
        count = 0
        for profile in queryset.filter(email_verified=False):
            profile.verify_email()
            count += 1

        self.message_user(
            request,
            f"{count} profile(s) marked as email verified.",
            level="SUCCESS" if count > 0 else "WARNING",
        )

    verify_emails.short_description = _("Mark emails as verified")

    def unverify_emails(self, request, queryset):
        """Mark selected profiles as email unverified."""
        count = 0
        for profile in queryset.filter(email_verified=True):
            profile.unverify_email()
            count += 1

        self.message_user(
            request,
            f"{count} profile(s) marked as email unverified.",
            level="SUCCESS" if count > 0 else "WARNING",
        )

    unverify_emails.short_description = _("Mark emails as unverified")

    def send_verification_reminder(self, request, queryset):
        """Send verification reminder (placeholder for future implementation)."""
        unverified_count = queryset.filter(email_verified=False).count()

        # TODO: Implement actual email sending logic
        self.message_user(
            request,
            f"Verification reminder would be sent to {unverified_count} user(s). "
            "(Feature not yet implemented)",
            level="INFO",
        )

    send_verification_reminder.short_description = _("Send verification reminder")


# Extend the default User admin to include our custom inlines
class CustomUserAdmin(BaseUserAdmin):
    """Enhanced User admin with authentication app inlines."""

    inlines = BaseUserAdmin.inlines + (UserProfileInline, EmailVerificationTokenInline)

    def get_queryset(self, request):
        """Optimize queryset with prefetch_related."""
        return (
            super()
            .get_queryset(request)
            .prefetch_related("profile", "verification_tokens")
        )


# Unregister the default User admin and register our custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
