import logging

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .models import EmailVerificationToken, UserProfile
from .utils import send_verification_email

logger = logging.getLogger(__name__)


@api_view(["POST"])  # User registration endpoint
@permission_classes([AllowAny])
def register(request):
    try:
        # Extract and validate input data
        username = request.data.get(
            "username", ""
        ).strip()  # .strip() removes leading/trailing spaces
        email = (
            request.data.get("email", "").strip().lower()
        )  # .lower() makes email case-insensitive
        password = request.data.get(
            "password", ""
        )  # Passwords are case-sensitive, so no .lower() or .strip()

        # Basic field validation
        if not username or not email or not password:
            return Response(
                {"error": "Username, email and password are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Username validation
        if len(username) < 3:
            return Response(
                {"error": "Username must be at least 3 characters long"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(username) > 30:
            return Response(
                {"error": "Username must be no more than 30 characters long"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Email validation
        try:
            validate_email(email)  # Raises ValidationError if email is not valid
        except ValidationError:
            return Response(
                {"error": "Please enter a valid email address"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if user already exists (case-insensitive for email)
        if User.objects.filter(
            username__iexact=username
        ).exists():  # username__iexact allows case-insensitive username checks
            return Response(
                {"error": "Username already exists"}, status=status.HTTP_400_BAD_REQUEST
            )

        if User.objects.filter(email__iexact=email).exists():
            return Response(
                {"error": "Email already exists"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Validate password
        try:
            validate_password(password)  # Raises ValidationError if password is weak
        except ValidationError as e:
            return Response(
                {"error": list(e.messages)}, status=status.HTTP_400_BAD_REQUEST
            )

        # Create user and profile in a transaction
        try:
            # Why atomic?
            # To ensure that either both User and UserProfile are created, or neither is, maintaining database integrity
            with transaction.atomic():
                # Create user (inactive until email is verified)
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    is_active=False,  # User will be activated after email verification
                )

                # Create user profile
                UserProfile.objects.create(user=user)

                # Send verification email
                email_sent = send_verification_email(user)

                if not email_sent:
                    logger.warning(f"Failed to send verification email to {email}")
                    # If email failed to send, still create user but notify
                    return Response(
                        {
                            "message": "User created successfully, but verification email failed to send. Please contact support.",
                            "user": {
                                "id": user.id,
                                "username": user.username,
                                "email": user.email,
                                "email_verified": False,
                            },
                            "email_verification_required": True,
                        },
                        status=status.HTTP_201_CREATED,
                    )

            logger.info(f"User {username} registered successfully")
            return Response(
                {
                    "message": "User created successfully. Please check your email for verification link.",
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "email_verified": False,
                    },
                    "email_verification_required": True,
                },
                status=status.HTTP_201_CREATED,
            )

        except IntegrityError as e:
            logger.error(f"Database integrity error during registration: {str(e)}")
            return Response(
                {"error": "User with this username or email already exists"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    except ValidationError as e:
        logger.error(f"Validation error during registration: {str(e)}")
        return Response(
            {"error": "Invalid data provided"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        logger.error(f"Unexpected error during registration: {str(e)}")
        return Response(
            {"error": "Something went wrong. Please try again later."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    """
    Authenticate user and return JWT tokens.

    Validates credentials, checks email verification status,
    and returns access/refresh tokens for authenticated users.
    """
    try:
        # Extract and normalize input data
        username = request.data.get("username", "").strip()
        password = request.data.get("password", "")  # Don't strip passwords

        # Input validation
        if not username or not password:
            return Response(
                {"success": False, "error": "Username and password are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate username length to prevent malicious input
        if len(username) > 150:  # Django's default username max_length
            return Response(
                {
                    "success": False,
                    "error": "Invalid credentials",  # Don't reveal specific validation details
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Authenticate user (this handles password hashing comparison)
        user = authenticate(request, username=username, password=password)

        if user is None:
            # Log failed login attempt for security monitoring
            logger.warning(
                f"Failed login attempt for username: {username} from IP: {request.META.get('REMOTE_ADDR')}"
            )
            return Response(
                {"success": False, "error": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Check if user account is active
        if not user.is_active:
            logger.warning(f"Login attempt for inactive user: {username}")
            return Response(
                {
                    "success": False,
                    "error": "Account is deactivated. Please contact support.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # Get or create user profile (defensive programming)
        profile, created = UserProfile.objects.get_or_create(user=user)

        if created:
            logger.warning(
                f"Created missing UserProfile for user {user.id} during login"
            )

        # Check email verification status
        if not profile.email_verified:
            logger.info(f"Login blocked for unverified user: {username}")
            return Response(
                {
                    "success": False,
                    "error": "Please verify your email address before logging in",
                    "email_verification_required": True,
                    "user_id": user.id,  # Frontend might need this for resend verification
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        # Update last login timestamp
        user.last_login = timezone.now()
        user.save(update_fields=["last_login"])

        # Log successful login
        logger.info(
            f"Successful login for user: {username} from IP: {request.META.get('REMOTE_ADDR')}"
        )

        return Response(
            {
                "success": True,
                "message": "Login successful",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "email_verified": profile.email_verified,
                    "last_login": user.last_login,
                    "date_joined": user.date_joined,
                    "is_active": user.is_active,
                },
                "profile": {
                    "email_verified_at": profile.email_verified_at,
                },
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                    "expires_in": refresh.access_token.lifetime.total_seconds(),  # Token expiry info
                },
            },
            status=status.HTTP_200_OK,
        )

    except ValidationError as e:
        logger.error(f"Validation error during login: {str(e)}")
        return Response(
            {"success": False, "error": "Invalid data provided"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    except Exception as e:
        # Log the error with context for debugging
        logger.error(
            f"Unexpected error during login for username '{username}': {str(e)}",
            exc_info=True,
        )
        return Response(
            {
                "success": False,
                "error": "Something went wrong. Please try again later.",
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([AllowAny])
def verify_email(request, token):
    """
    Verify user email address using verification token.

    Args:
        token (str): UUID verification token from email link

    Returns:
        Success: User data with verification status
        Error: Appropriate error message and status
    """
    try:
        # Input validation - ensure token is UUID format
        if not token:
            logger.warning("Email verification attempted with empty token")
            return Response(
                {"success": False, "error": "Invalid verification token"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate UUID format to prevent malicious input
        try:
            import uuid

            uuid.UUID(str(token))  # This will raise ValueError if not valid UUID
        except ValueError:
            logger.warning(
                f"Email verification attempted with invalid UUID format: {token[:8]}..."
            )
            return Response(
                {"success": False, "error": "Invalid verification token format"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get client IP for logging
        client_ip = request.META.get("REMOTE_ADDR", "Unknown")

        # Attempt to get the verification token
        try:
            verification_token = EmailVerificationToken.objects.select_related(
                "user"
            ).get(token=token, used=False)
        except EmailVerificationToken.DoesNotExist:
            # Log failed verification attempt for security monitoring
            logger.warning(
                f"Email verification failed - invalid token: {token[:8]}... from IP: {client_ip}"
            )
            return Response(
                {"success": False, "error": "Invalid or expired verification token"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if token has expired
        if verification_token.is_expired():
            logger.info(
                f"Email verification failed - expired token for user {verification_token.user.id}"
            )
            return Response(
                {
                    "success": False,
                    "error": "Verification token has expired. Please request a new verification email.",
                    "expired": True,
                    "user_id": verification_token.user.id,  # Frontend might need this for resend
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = verification_token.user

        # Check if user account still exists and is valid
        if not user:
            logger.error(
                f"Email verification failed - user not found for token: {token[:8]}..."
            )
            return Response(
                {"success": False, "error": "User account not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Get user profile (defensive programming)
        profile, created = UserProfile.objects.get_or_create(user=user)

        if created:
            logger.warning(
                f"Created missing UserProfile for user {user.id} during email verification"
            )

        # Check if email is already verified
        if profile.email_verified:
            logger.info(
                f"Email verification attempted for already verified user: {user.username}"
            )
            return Response(
                {
                    "success": True,
                    "message": "Email address is already verified. You can log in now.",
                    "already_verified": True,
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "email_verified": True,
                        "email_verified_at": profile.email_verified_at,
                        "is_active": user.is_active,
                    },
                },
                status=status.HTTP_200_OK,
            )

        # Perform email verification in atomic transaction
        try:
            with transaction.atomic():
                # Mark email as verified
                profile.email_verified = True
                profile.email_verified_at = timezone.now()
                profile.save(update_fields=["email_verified", "email_verified_at"])

                # Activate user account
                user.is_active = True
                user.save(update_fields=["is_active"])

                # Mark token as used to prevent reuse
                verification_token.used = True
                verification_token.save(update_fields=["used"])

            # Log successful verification
            logger.info(
                f"Email verified successfully for user: {user.username} from IP: {client_ip}"
            )

            return Response(
                {
                    "success": True,
                    "message": "Email verified successfully! You can now log in.",
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "email_verified": True,
                        "email_verified_at": profile.email_verified_at,
                        "is_active": user.is_active,
                        "date_joined": user.date_joined,
                    },
                },
                status=status.HTTP_200_OK,
            )

        except IntegrityError as e:
            logger.error(
                f"Database integrity error during email verification for user {user.id}: {str(e)}"
            )
            return Response(
                {
                    "success": False,
                    "error": "Unable to complete email verification. Please try again.",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    except ValidationError as e:
        logger.error(f"Validation error during email verification: {str(e)}")
        return Response(
            {"success": False, "error": "Invalid verification data"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    except Exception as e:
        # Log unexpected errors with full context
        logger.error(
            f"Unexpected error during email verification for token {token[:8]}...: {str(e)}",
            exc_info=True,
        )
        return Response(
            {
                "success": False,
                "error": "Something went wrong during email verification. Please try again later.",
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([AllowAny])
def resend_verification_email(request):
    """
    Resend email verification link to user.

    This endpoint implements security best practices:
    - Rate limiting protection (logs support implementation)
    - No user enumeration (always returns success message)
    - Comprehensive audit logging
    - Input validation and sanitization
    """
    try:
        # Extract and normalize input data
        email = request.data.get("email", "").strip().lower()
        client_ip = request.META.get("REMOTE_ADDR", "Unknown")
        user_agent = request.META.get("HTTP_USER_AGENT", "Unknown")

        # Input validation
        if not email:
            logger.warning(
                f"Resend verification attempted with empty email from IP: {client_ip}"
            )
            return Response(
                {"success": False, "error": "Email address is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate email format
        try:
            validate_email(email)
        except ValidationError:
            logger.warning(
                f"Resend verification attempted with invalid email format: {email} from IP: {client_ip}"
            )
            return Response(
                {"success": False, "error": "Please enter a valid email address"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Log resend attempt for rate limiting and security monitoring
        logger.info(
            f"Resend verification email requested for: {email} from IP: {client_ip}"
        )

        # Standard security response - always return success to prevent user enumeration
        standard_response = Response(
            {
                "success": True,
                "message": "If the email exists in our system and is not verified, a verification email has been sent.",
            },
            status=status.HTTP_200_OK,
        )

        try:
            # Try to find user by email (case-insensitive)
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            # Log for security monitoring, but don't reveal user doesn't exist
            logger.info(
                f"Resend verification requested for non-existent email: {email} from IP: {client_ip}"
            )
            return standard_response

        # Get or create user profile (defensive programming)
        profile, created = UserProfile.objects.get_or_create(user=user)

        if created:
            logger.warning(
                f"Created missing UserProfile for user {user.id} during resend verification"
            )

        # Check if email is already verified
        if profile.email_verified:
            logger.info(
                f"Resend verification requested for already verified user: {user.username}"
            )
            # Return standard response for security (don't reveal verification status)
            return standard_response

        # Check if user account is active (shouldn't be for unverified users, but check anyway)
        if user.is_active:
            logger.warning(
                f"Resend verification for active but unverified user: {user.username}"
            )

        # Rate limiting check - count recent verification attempts
        from datetime import timedelta

        recent_threshold = timezone.now() - timedelta(minutes=5)  # 5-minute window
        recent_tokens = EmailVerificationToken.objects.filter(
            user=user, created_at__gte=recent_threshold
        ).count()

        if recent_tokens >= 3:  # Max 3 attempts per 5 minutes
            logger.warning(
                f"Rate limit exceeded for resend verification: {email} from IP: {client_ip}"
            )
            # Still return standard response for security
            return standard_response

        # Clean up old unused tokens for this user (optional - prevents token accumulation)
        EmailVerificationToken.objects.filter(
            user=user, used=False, expires_at__lt=timezone.now()
        ).delete()

        # Send verification email
        try:
            email_sent = send_verification_email(user)

            if email_sent:
                logger.info(
                    f"Verification email resent successfully to: {user.username} ({email})"
                )
                return standard_response
            else:
                # Log failure but still return standard response
                logger.error(
                    f"Failed to resend verification email to: {user.username} ({email})"
                )
                return standard_response

        except Exception as email_error:
            logger.error(
                f"Error sending verification email to {user.username}: {str(email_error)}"
            )
            # Still return standard response for security
            return standard_response

    except ValidationError as e:
        logger.error(f"Validation error during resend verification: {str(e)}")
        return Response(
            {"success": False, "error": "Invalid data provided"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    except Exception as e:
        # Log unexpected errors with context
        logger.error(
            f"Unexpected error during resend verification for email '{email}': {str(e)}",
            exc_info=True,
        )
        return Response(
            {
                "success": False,
                "error": "Something went wrong. Please try again later.",
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_profile(request):
    """
    Get current authenticated user's profile information.

    Returns:
        - User basic information
        - Profile data with verification status
        - Timestamps for audit trail
    """
    try:
        # Use get_or_create for defensive programming
        # Handles edge cases like legacy users or data inconsistencies
        profile, created = UserProfile.objects.get_or_create(user=request.user)

        # Log if profile was missing (indicates potential data integrity issue)
        if created:
            logger.warning(
                f"Created missing UserProfile for user {request.user.id} ({request.user.username}). "
                f"This may indicate a registration process issue."
            )

        # Return comprehensive user data
        return Response(
            {
                "success": True,
                "user": {
                    "id": request.user.id,
                    "username": request.user.username,
                    "email": request.user.email,
                    "is_active": request.user.is_active,
                    "date_joined": request.user.date_joined,
                    "last_login": request.user.last_login,
                },
                "profile": {
                    "email_verified": profile.email_verified,
                    "email_verified_at": profile.email_verified_at,
                    "created_at": profile.created_at,
                    "updated_at": profile.updated_at,
                },
            },
            status=status.HTTP_200_OK,
        )

    except Exception as e:
        # Log the error with context for debugging
        logger.error(
            f"Error retrieving profile for user {request.user.id}: {str(e)}",
            exc_info=True,  # Include stack trace
        )
        return Response(
            {
                "success": False,
                "error": "Unable to retrieve user profile. Please try again later.",
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# Alternative: Strict Version (If You Prefer)
# If you want to enforce strict data integrity:
# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def user_profile_strict(request):
#     """Get user profile - strict version that fails on missing profile"""
#     try:
#         profile = UserProfile.objects.select_related('user').get(user=request.user)

#         return Response({
#             'success': True,
#             'user': {
# =============================================================================
# PROFESSIONAL MISSING ENDPOINTS - ENTERPRISE GRADE IMPLEMENTATIONS
# =============================================================================


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    Professional logout endpoint with token blacklisting.

    Implements secure logout by blacklisting the refresh token
    and logging the logout event for security monitoring.
    """
    try:
        # Extract refresh token from request
        refresh_token = request.data.get("refresh_token")

        if not refresh_token:
            return Response(
                {
                    "success": False,
                    "error": "Refresh token is required for secure logout",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Blacklist the refresh token
            token = RefreshToken(refresh_token)
            token.blacklist()

            # Log successful logout for security monitoring
            client_ip = request.META.get("REMOTE_ADDR", "Unknown")
            logger.info(
                f"User {request.user.username} logged out successfully from IP: {client_ip}"
            )

            return Response(
                {"success": True, "message": "Logged out successfully"},
                status=status.HTTP_200_OK,
            )

        except Exception as token_error:
            # Log token blacklist failure but still count as successful logout
            logger.warning(
                f"Failed to blacklist token for user {request.user.username}: {str(token_error)}"
            )
            return Response(
                {"success": True, "message": "Logged out successfully"},
                status=status.HTTP_200_OK,
            )

    except Exception as e:
        logger.error(f"Logout error for user {request.user.username}: {str(e)}")
        return Response(
            {"success": False, "error": "Something went wrong during logout"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["PUT", "PATCH"])
@permission_classes([IsAuthenticated])
def update_profile(request):
    """
    Professional profile update endpoint.

    Allows users to update their profile information with
    comprehensive validation and security checks.
    """
    try:
        # Get user profile
        profile, created = UserProfile.objects.get_or_create(user=request.user)

        if created:
            logger.warning(
                f"Created missing profile for user {request.user.id} during update"
            )

        # Extract updatable fields
        first_name = request.data.get("first_name", "").strip()
        last_name = request.data.get("last_name", "").strip()
        phone_number = request.data.get("phone_number", "").strip()
        bio = request.data.get("bio", "").strip()
        birth_date = request.data.get("birth_date")

        # Validate input data
        errors = {}

        # Name validation
        if first_name and len(first_name) > 30:
            errors["first_name"] = "First name must be no more than 30 characters"
        if last_name and len(last_name) > 30:
            errors["last_name"] = "Last name must be no more than 30 characters"

        # Phone number validation
        if phone_number and (len(phone_number) < 10 or len(phone_number) > 20):
            errors["phone_number"] = "Phone number must be between 10 and 20 characters"

        # Bio validation
        if bio and len(bio) > 500:
            errors["bio"] = "Bio must be no more than 500 characters"

        # Birth date validation
        if birth_date:
            try:
                from datetime import datetime

                birth_date_obj = datetime.strptime(birth_date, "%Y-%m-%d").date()
                if birth_date_obj >= timezone.now().date():
                    errors["birth_date"] = "Birth date must be in the past"
            except ValueError:
                errors["birth_date"] = "Invalid birth date format. Use YYYY-MM-DD"

        if errors:
            return Response(
                {"success": False, "errors": errors}, status=status.HTTP_400_BAD_REQUEST
            )

        # Update user fields
        user_updated = False
        if first_name and first_name != request.user.first_name:
            request.user.first_name = first_name
            user_updated = True
        if last_name and last_name != request.user.last_name:
            request.user.last_name = last_name
            user_updated = True

        if user_updated:
            request.user.save(update_fields=["first_name", "last_name"])

        # Update profile fields
        profile_updated = False
        if phone_number and phone_number != profile.phone_number:
            profile.phone_number = phone_number
            profile_updated = True
        if bio and bio != profile.bio:
            profile.bio = bio
            profile_updated = True
        if birth_date and birth_date_obj != profile.birth_date:
            profile.birth_date = birth_date_obj
            profile_updated = True

        if profile_updated:
            profile.save(update_fields=["phone_number", "bio", "birth_date"])

        # Log profile update
        logger.info(f"Profile updated for user: {request.user.username}")

        return Response(
            {
                "success": True,
                "message": "Profile updated successfully",
                "user": {
                    "id": request.user.id,
                    "username": request.user.username,
                    "email": request.user.email,
                    "first_name": request.user.first_name,
                    "last_name": request.user.last_name,
                },
                "profile": {
                    "phone_number": profile.phone_number,
                    "bio": profile.bio,
                    "birth_date": profile.birth_date,
                    "email_verified": profile.email_verified,
                    "profile_completion": profile.profile_completion_percentage,
                },
            },
            status=status.HTTP_200_OK,
        )

    except Exception as e:
        logger.error(f"Profile update error for user {request.user.username}: {str(e)}")
        return Response(
            {"success": False, "error": "Something went wrong while updating profile"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_password(request):
    """
    Professional password change endpoint.

    Implements secure password change with validation,
    current password verification, and security logging.
    """
    try:
        current_password = request.data.get("current_password")
        new_password = request.data.get("new_password")
        confirm_password = request.data.get("confirm_password")

        # Input validation
        if not all([current_password, new_password, confirm_password]):
            return Response(
                {
                    "success": False,
                    "error": "Current password, new password, and confirmation are required",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verify current password
        if not request.user.check_password(current_password):
            logger.warning(
                f"Failed password change attempt for user {request.user.username} - incorrect current password"
            )
            return Response(
                {"success": False, "error": "Current password is incorrect"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check password confirmation
        if new_password != confirm_password:
            return Response(
                {
                    "success": False,
                    "error": "New password and confirmation do not match",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate new password strength
        try:
            validate_password(new_password, user=request.user)
        except ValidationError as e:
            return Response(
                {"success": False, "error": list(e.messages)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if new password is different from current
        if request.user.check_password(new_password):
            return Response(
                {
                    "success": False,
                    "error": "New password must be different from current password",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Update password
        request.user.set_password(new_password)
        request.user.save(update_fields=["password"])

        # Log password change for security
        client_ip = request.META.get("REMOTE_ADDR", "Unknown")
        logger.info(
            f"Password changed successfully for user: {request.user.username} from IP: {client_ip}"
        )

        return Response(
            {
                "success": True,
                "message": "Password changed successfully. Please log in with your new password.",
            },
            status=status.HTTP_200_OK,
        )

    except Exception as e:
        logger.error(
            f"Password change error for user {request.user.username}: {str(e)}"
        )
        return Response(
            {"success": False, "error": "Something went wrong while changing password"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([AllowAny])
def request_password_reset(request):
    """
    Professional password reset request endpoint.

    Implements secure password reset with rate limiting,
    security logging, and user enumeration protection.
    """
    try:
        email = request.data.get("email", "").strip().lower()
        client_ip = request.META.get("REMOTE_ADDR", "Unknown")

        # Input validation
        if not email:
            return Response(
                {"success": False, "error": "Email address is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate email format
        try:
            validate_email(email)
        except ValidationError:
            return Response(
                {"success": False, "error": "Please enter a valid email address"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Standard security response to prevent user enumeration
        standard_response = Response(
            {
                "success": True,
                "message": "If the email exists in our system, a password reset link has been sent.",
            },
            status=status.HTTP_200_OK,
        )

        # Log password reset request for security monitoring
        logger.info(f"Password reset requested for email: {email} from IP: {client_ip}")

        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            # Log for security but don't reveal user doesn't exist
            logger.info(f"Password reset requested for non-existent email: {email}")
            return standard_response

        # Check if user account is active
        if not user.is_active:
            logger.warning(
                f"Password reset requested for inactive user: {user.username}"
            )
            return standard_response

        # Rate limiting check - count recent reset attempts
        from datetime import timedelta

        recent_threshold = timezone.now() - timedelta(minutes=15)  # 15-minute window
        recent_tokens = EmailVerificationToken.objects.filter(
            user=user, created_at__gte=recent_threshold
        ).count()

        if recent_tokens >= 3:  # Max 3 attempts per 15 minutes
            logger.warning(
                f"Rate limit exceeded for password reset: {email} from IP: {client_ip}"
            )
            return standard_response

        # Create password reset token (reusing EmailVerificationToken model)
        reset_token = EmailVerificationToken.objects.create_for_user(user)

        # Send password reset email (you'll need to create this utility function)
        try:
            # For now, log the reset token (in production, send via email)
            logger.info(
                f"Password reset token created for {user.username}: {reset_token.token}"
            )
            # TODO: Implement send_password_reset_email(user, reset_token)

            return standard_response

        except Exception as email_error:
            logger.error(
                f"Failed to send password reset email to {user.username}: {str(email_error)}"
            )
            return standard_response

    except Exception as e:
        logger.error(f"Password reset request error for email '{email}': {str(e)}")
        return Response(
            {
                "success": False,
                "error": "Something went wrong. Please try again later.",
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([AllowAny])
def confirm_password_reset(request, token):
    """
    Professional password reset confirmation endpoint.

    Validates reset token and allows user to set new password
    with comprehensive security checks.
    """
    try:
        new_password = request.data.get("new_password")
        confirm_password = request.data.get("confirm_password")
        client_ip = request.META.get("REMOTE_ADDR", "Unknown")

        # Input validation
        if not all([new_password, confirm_password]):
            return Response(
                {
                    "success": False,
                    "error": "New password and confirmation are required",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check password confirmation
        if new_password != confirm_password:
            return Response(
                {"success": False, "error": "Password and confirmation do not match"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate token format
        try:
            import uuid

            uuid.UUID(str(token))
        except ValueError:
            logger.warning(
                f"Password reset attempted with invalid token format from IP: {client_ip}"
            )
            return Response(
                {"success": False, "error": "Invalid reset token"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get valid token
        reset_token = EmailVerificationToken.objects.get_valid_token(str(token))
        if not reset_token:
            logger.warning(
                f"Password reset attempted with invalid/expired token from IP: {client_ip}"
            )
            return Response(
                {"success": False, "error": "Invalid or expired reset token"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = reset_token.user

        # Validate new password strength
        try:
            validate_password(new_password, user=user)
        except ValidationError as e:
            return Response(
                {"success": False, "error": list(e.messages)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if new password is different from current (if user remembers it)
        if user.check_password(new_password):
            return Response(
                {
                    "success": False,
                    "error": "New password must be different from current password",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Reset password and mark token as used
        with transaction.atomic():
            user.set_password(new_password)
            user.save(update_fields=["password"])
            reset_token.mark_as_used(ip_address=client_ip)

        # Log successful password reset
        logger.info(
            f"Password reset completed for user: {user.username} from IP: {client_ip}"
        )

        return Response(
            {
                "success": True,
                "message": "Password reset successfully. You can now log in with your new password.",
            },
            status=status.HTTP_200_OK,
        )

    except Exception as e:
        logger.error(f"Password reset confirmation error: {str(e)}")
        return Response(
            {"success": False, "error": "Something went wrong during password reset"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def deactivate_account(request):
    """
    Professional account deactivation endpoint.

    Allows users to deactivate their account while preserving
    data for potential reactivation.
    """
    try:
        password = request.data.get("password")
        reason = request.data.get("reason", "").strip()

        # Verify password for security
        if not password:
            return Response(
                {
                    "success": False,
                    "error": "Password confirmation is required for account deactivation",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not request.user.check_password(password):
            logger.warning(
                f"Account deactivation attempted with incorrect password for user: {request.user.username}"
            )
            return Response(
                {"success": False, "error": "Incorrect password"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Deactivate account
        request.user.is_active = False
        request.user.save(update_fields=["is_active"])

        # Log deactivation with reason
        client_ip = request.META.get("REMOTE_ADDR", "Unknown")
        logger.info(
            f"Account deactivated for user: {request.user.username} from IP: {client_ip}. Reason: {reason or 'Not provided'}"
        )

        return Response(
            {
                "success": True,
                "message": "Account deactivated successfully. Contact support to reactivate.",
            },
            status=status.HTTP_200_OK,
        )

    except Exception as e:
        logger.error(
            f"Account deactivation error for user {request.user.username}: {str(e)}"
        )
        return Response(
            {
                "success": False,
                "error": "Something went wrong during account deactivation",
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_account(request):
    """
    Professional account deletion endpoint (GDPR Compliance).

    Permanently deletes user account and associated data
    with proper security verification and audit logging.
    """
    try:
        password = request.data.get("password")
        confirmation = request.data.get("confirmation", "").strip().lower()

        # Security verification
        if not password:
            return Response(
                {
                    "success": False,
                    "error": "Password confirmation is required for account deletion",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if confirmation != "delete my account":
            return Response(
                {
                    "success": False,
                    "error": 'Please type "delete my account" to confirm deletion',
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not request.user.check_password(password):
            logger.warning(
                f"Account deletion attempted with incorrect password for user: {request.user.username}"
            )
            return Response(
                {"success": False, "error": "Incorrect password"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Log account deletion for compliance
        client_ip = request.META.get("REMOTE_ADDR", "Unknown")
        username = request.user.username
        user_id = request.user.id

        # Delete user account (cascade will handle related data)
        with transaction.atomic():
            request.user.delete()

        logger.info(
            f"Account permanently deleted - User ID: {user_id}, Username: {username}, IP: {client_ip}"
        )

        return Response(
            {
                "success": True,
                "message": "Account deleted permanently. All data has been removed.",
            },
            status=status.HTTP_200_OK,
        )

    except Exception as e:
        logger.error(
            f"Account deletion error for user {request.user.username}: {str(e)}"
        )
        return Response(
            {"success": False, "error": "Something went wrong during account deletion"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
