import secrets
import string

from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from django.contrib.auth import get_user_model
from django.utils import timezone
from .mail_service import send_password_reset_email, send_welcome_email
from .models import PasswordResetCode
from .password_change_email import password_change_email_service
from .serializers import (
    LoginSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
    UserProfileSerializer,
)

User = get_user_model()

class RegisterView(generics.CreateAPIView):
    """
    Endpoint for new user registration.
    Automatically returns tokens upon successful creation.
    """
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        welcome_email_sent = send_welcome_email(user)
        
        # Generate tokens for immediate login
        refresh = RefreshToken.for_user(user)
        
        # Return user profile + tokens
        profile_serializer = UserProfileSerializer(user)
        return Response({
            "user": profile_serializer.data,
            "tokens": {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            },
            "email": {
                "welcome_sent": welcome_email_sent,
            },
        }, status=status.HTTP_201_CREATED)

class LoginView(TokenObtainPairView):
    """
    Secure login endpoint using CustomTokenObtainPairSerializer.
    Returns access and refresh tokens.
    """
    permission_classes = (permissions.AllowAny,)
    serializer_class = LoginSerializer

class LogoutView(APIView):
    """
    Secure logout endpoint that blacklists the provided refresh token.
    """
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response({"error": "Refresh token is required"}, status=status.HTTP_400_BAD_REQUEST)
                
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"detail": "Successfully logged out."}, status=status.HTTP_205_RESET_CONTENT)
        except (TokenError, InvalidToken):
            # Token already expired or invalid — treat as already logged out
            return Response({"detail": "Successfully logged out."}, status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class MeView(generics.RetrieveUpdateAPIView):
    """
    Retrieve or update the current authenticated user's profile.
    """
    serializer_class = UserProfileSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user

    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object())
        return Response(serializer.data)

    def patch(self, request, *args, **kwargs):
        # We only allow updating certain fields in UserProfileSerializer (username, avatar_url)
        return super().patch(request, *args, **kwargs)


class ChangePasswordView(APIView):
    """
    Change the authenticated user's password.
    Sends security notification email after successful change.
    """
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        """
        Change user password.
        
        Request body:
        {
            "current_password": "string",
            "new_password": "string"
        }
        """
        user = request.user
        
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')
        
        if not current_password:
            return Response({
                'error': 'Current password is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not new_password:
            return Response({
                'error': 'New password is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate current password
        if not user.check_password(current_password):
            return Response({
                'error': 'Current password is incorrect'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate new password strength
        if len(new_password) < 8:
            return Response({
                'error': 'Password must be at least 8 characters'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get request metadata
        ip_address = self._get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Update password
        user.set_password(new_password)
        user.save(update_fields=['password'])
        
        # Send password change notification email
        password_change_email_service.send_password_changed_email(
            user=user,
            event_type='password_changed',
            ip_address=ip_address,
            user_agent=user_agent,
            success=True,
            details={
                'changed_by_user': True,
            },
        )
        
        return Response({
            'detail': 'Password changed successfully'
        }, status=status.HTTP_200_OK)

    def _get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')


class PasswordResetRequestView(APIView):
    """
    Sends a 4-minute password reset code when the email belongs to an account.
    """
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        user = User.objects.filter(email__iexact=email).first()

        if not user:
            return Response({
                "exists": False,
                "detail": "This email is not in our database. Please sign up first.",
            }, status=status.HTTP_404_NOT_FOUND)

        now = timezone.now()
        code = _generate_password_reset_code()
        expires_at = now + timezone.timedelta(minutes=4)

        PasswordResetCode.objects.filter(
            user=user,
            used_at__isnull=True,
            expires_at__gt=now,
        ).update(used_at=now)
        reset_code = PasswordResetCode.create_for_user(user, code, expires_at)
        reset_email_sent = send_password_reset_email(user, code, expires_in_minutes=4)

        if not reset_email_sent:
            reset_code.mark_used()
            return Response({
                "exists": True,
                "email_sent": False,
                "error": "We found your account, but could not send the reset code. Please try again.",
            }, status=status.HTTP_502_BAD_GATEWAY)

        return Response({
            "exists": True,
            "email_sent": True,
            "detail": "Password reset code sent. It expires in 4 minutes.",
        }, status=status.HTTP_200_OK)


class PasswordResetConfirmView(APIView):
    """
    Confirms a database-backed reset code and updates the user's password.
    Reset codes expire after 4 minutes and are consumed after use.
    """
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        code = serializer.validated_data["code"]
        user = User.objects.filter(email__iexact=email).first()

        if not user:
            return Response({
                "error": "Reset code is invalid or expired."
            }, status=status.HTTP_400_BAD_REQUEST)

        reset_code = PasswordResetCode.objects.filter(
            user=user,
            used_at__isnull=True,
            expires_at__gt=timezone.now(),
        ).order_by("-created_at").first()

        if not reset_code or not reset_code.matches(code):
            return Response({
                "error": "Reset code is invalid or expired."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get request metadata before password change
        ip_address = self._get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Update password
        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])
        reset_code.mark_used()

        # Send password change notification email
        password_change_email_service.send_password_changed_email(
            user=user,
            event_type='password_reset',
            ip_address=ip_address,
            user_agent=user_agent,
            success=True,
            details={
                'reset_code_used': True,
                'reset_code_id': reset_code.id,
            },
        )

        return Response({"detail": "Password reset successfully."}, status=status.HTTP_200_OK)

    def _get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')


def _generate_password_reset_code():
    digits = [str(secrets.randbelow(10)) for _ in range(6)]
    letter = secrets.choice(string.ascii_uppercase)
    code = digits + [letter]
    secrets.SystemRandom().shuffle(code)
    return "".join(code)
