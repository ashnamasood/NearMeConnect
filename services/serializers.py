from rest_framework import serializers
from .models import ServiceProvider, ServiceRequest, Review,ServiceCategory, UserProfile
from django.contrib.auth.models import User
from .models import UserProfile
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['phone', 'is_service_provider']
class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(source='userprofile')
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'password', 'profile']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        profile_data = validated_data.pop('userprofile', {})
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password']
        )
        UserProfile.objects.create(
            user=user,
            phone=profile_data.get('phone', ''),
            is_service_provider=profile_data.get('is_service_provider', False)
        )
        return user

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        token['is_staff'] = user.is_staff
        if hasattr(user, 'userprofile'):
            token['is_service_provider'] = user.userprofile.is_service_provider
        return token
    
class ServiceCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceCategory
        fields = '__all__'

class ServiceProviderSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    
    class Meta:
        model = ServiceProvider
        fields = '__all__'
        depth = 1

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user_serializer = UserSerializer(data=user_data)
        if user_serializer.is_valid():
            user = user_serializer.save()
            provider = ServiceProvider.objects.create(user=user, **validated_data)
            return provider
        raise serializers.ValidationError(user_serializer.errors)

class ServiceRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceRequest
        fields = '__all__'
        read_only_fields = ['created_at']

class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = '__all__'
        read_only_fields = ['created_at']