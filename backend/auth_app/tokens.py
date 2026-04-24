from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Extends simplejwt TokenObtainPairSerializer to add custom claims to the JWT payload.
    """
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token['user_id'] = user.id
        token['username'] = user.username
        token['role'] = user.role
        token['xp'] = user.xp
        token['level'] = user.level

        return token
