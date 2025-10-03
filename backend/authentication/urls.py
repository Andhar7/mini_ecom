from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from . import views

# Professional URL namespace
app_name = "authentication"

urlpatterns = [
    # Authentication endpoints
    path("register/", views.register, name="register"),
    path("login/", views.login, name="login"),
    path("logout/", views.logout, name="logout"),  # Missing logout endpoint
    # User profile management
    path("profile/", views.user_profile, name="user_profile"),
    path(
        "profile/update/", views.update_profile, name="update_profile"
    ),  # Profile updates
    path(
        "profile/change-password/", views.change_password, name="change_password"
    ),  # Password change
    # Email verification
    path("verify-email/<uuid:token>/", views.verify_email, name="verify_email"),
    path(
        "resend-verification/",
        views.resend_verification_email,
        name="resend_verification",
    ),
    # Password reset (professional feature)
    path(
        "password-reset/", views.request_password_reset, name="request_password_reset"
    ),
    path(
        "password-reset/confirm/<uuid:token>/",
        views.confirm_password_reset,
        name="confirm_password_reset",
    ),
    # JWT token management
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path(
        "token/verify/", TokenVerifyView.as_view(), name="token_verify"
    ),  # Token validation
    # Account management
    path(
        "deactivate/", views.deactivate_account, name="deactivate_account"
    ),  # Account deactivation
    path("delete/", views.delete_account, name="delete_account"),  # GDPR compliance
]


# POST /auth/register/                    # User registration
# POST /auth/login/                       # User login
# POST /auth/logout/                      # User logout
# GET  /auth/profile/                     # Get user profile
# PUT  /auth/profile/update/              # Update profile
# POST /auth/profile/change-password/     # Change password
# GET  /auth/verify-email/<token>/        # Verify email
# POST /auth/resend-verification/         # Resend verification
# POST /auth/password-reset/              # Request password reset
# POST /auth/password-reset/confirm/<token>/ # Confirm reset
# POST /auth/token/refresh/               # Refresh JWT token
# POST /auth/token/verify/                # Verify JWT token
# POST /auth/deactivate/                  # Deactivate account
# DELETE /auth/delete/                    # Delete account
