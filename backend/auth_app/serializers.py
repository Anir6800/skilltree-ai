from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from quests.models import QuestSubmission
from .tokens import CustomTokenObtainPairSerializer

User = get_user_model()

class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for the current user's profile and progression stats.
    """
    quests_completed_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'xp', 'level', 
            'streak_days', 'role', 'avatar_url', 
            'quests_completed_count', 'date_joined'
        ]
        read_only_fields = ['id', 'email', 'xp', 'level', 'streak_days', 'role', 'date_joined']

    def get_quests_completed_count(self, obj):
        return QuestSubmission.objects.filter(user=obj, status='passed').count()

class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration with strict password validation.
    """
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password_confirm')

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            print(f"DEBUG: Registration failed - Email {value} already exists")
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate(self, attrs):
        print(f"DEBUG: Registering user: {attrs.get('username')}, email: {attrs.get('email')}")
        
        if attrs['password'] != attrs['password_confirm']:
            print("DEBUG: Password mismatch")
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        
        # Additional strength check if not already covered by validators
        password = attrs['password']
        if not any(char.isdigit() for char in password):
            print("DEBUG: Password missing digit")
            raise serializers.ValidationError({"password": "Password must contain at least one digit."})
        if not any(char.isupper() for char in password):
            print("DEBUG: Password missing uppercase")
            raise serializers.ValidationError({"password": "Password must contain at least one uppercase letter."})
            
        print("DEBUG: Registration validation successful")
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user

class LoginSerializer(CustomTokenObtainPairSerializer):
    """
    Serializer for login, supporting both username and email.
    """
    username = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)
    password = serializers.CharField(write_only=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure 'username' is not required so we can use 'email' instead
        if 'username' in self.fields:
            self.fields['username'].required = False

    def validate(self, attrs):
        email = attrs.get("email")
        username = attrs.get("username")
        password = attrs.get("password")

        print(f"DEBUG: Login attempt - email: {email}, username: {username}")

        if not email and not username:
            raise serializers.ValidationError("Either username or email is required.")
        
        if not password:
            raise serializers.ValidationError("Password is required.")

        identifier = email or username
        
        if identifier and "@" in identifier:
            try:
                user = User.objects.get(email=identifier)
                attrs["username"] = user.username
                print(f"DEBUG: Resolved email {identifier} to username {user.username}")
            except User.DoesNotExist:
                print(f"DEBUG: Email {identifier} not found, falling back to identifier as username")
                attrs["username"] = identifier
        else:
            attrs["username"] = identifier
            print(f"DEBUG: Using identifier {identifier} as username")
            
        try:
            return super().validate(attrs)
        except Exception as e:
            print(f"DEBUG: super().validate failed: {str(e)}")
            raise e
