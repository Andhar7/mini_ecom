from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import EmailVerificationToken

def send_verification_email(user):
    """Send email verification email to user"""
    try:
        # Create or get existing token
        token, created = EmailVerificationToken.objects.get_or_create(
            user=user,
            used=False,
            defaults={}
        )
        
        # If token already exists and not expired, use it
        if not created and token.is_expired():
            # Delete expired token and create new one
            token.delete()
            token = EmailVerificationToken.objects.create(user=user)
        
        verification_url = f"{settings.FRONTEND_URL}/verify-email/{token.token}"
        
        subject = 'Verify Your Email Address - Todo App'
        
        # Create HTML email content
        html_message = f"""
        <html>
        <body>
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #333;">Welcome to Todo App!</h2>
                <p>Hi {user.username},</p>
                <p>Thank you for registering with Todo App. Please verify your email address by clicking the button below:</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{verification_url}" 
                       style="background-color: #007bff; color: white; padding: 12px 30px; 
                              text-decoration: none; border-radius: 5px; display: inline-block;">
                        Verify Email Address
                    </a>
                </div>
                
                <p>Or copy and paste this link in your browser:</p>
                <p style="word-break: break-all; color: #007bff;">{verification_url}</p>
                
                <p><strong>This link will expire in 24 hours.</strong></p>
                
                <p>If you didn't create an account with us, please ignore this email.</p>
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                <p style="color: #666; font-size: 12px;">
                    This is an automated email. Please do not reply to this email.
                </p>
            </div>
        </body>
        </html>
        """
        
        # Plain text version
        plain_message = f"""
        Welcome to Todo App!
        
        Hi {user.username},
        
        Thank you for registering with Todo App. Please verify your email address by visiting this link:
        
        {verification_url}
        
        This link will expire in 24 hours.
        
        If you didn't create an account with us, please ignore this email.
        """
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        return True
        
    except Exception as e:
        print(f"Error sending verification email: {str(e)}")
        return False