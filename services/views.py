from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser,AllowAny
from .models import ServiceCategory, ServiceProvider, ServiceRequest, Review

from .google_api import get_nearby_services, get_current_location, geocode_address, get_place_details, validate_coordinates
from django.db.models import F, ExpressionWrapper, FloatField
from django.db.models.functions import Sqrt, Power
from django.shortcuts import get_object_or_404
import requests
from rest_framework import generics, status
# from django.contrib.auth import authenticate, login
from .serializers import UserSerializer, CustomTokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import (
    ServiceCategorySerializer, 
    ServiceProviderSerializer,
    ServiceRequestSerializer,
    ReviewSerializer
)


@api_view(['POST'])
def refresh_token(request):
    try:
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({"error": "Refresh token is required"}, status=400)

        token = RefreshToken(refresh_token)
        access_token = str(token.access_token)
        
        return Response({
            'access': access_token,
            'refresh': str(token)
        })
    except Exception as e:
        return Response({"error": str(e)}, status=401)
    
class UserCreateView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = []

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({"message": "User created successfully"}, status=status.HTTP_201_CREATED)

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

from django.contrib.auth import authenticate

@api_view(['POST'])
@permission_classes([AllowAny])
def admin_login(request):
    username = request.data.get('username')
    
    password = request.data.get('password')
    print(username,password)
    user = authenticate(username=username, password=password)
    
    if user is not None and user.is_staff:
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'is_admin': True,
            'username': user.username
        })
    return Response({"error": "Invalid admin credentials"}, status=400)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_service_requests(request):
    """
    Get all service requests for the current user
    GET /api/requests/
    """
    if hasattr(request.user, 'serviceprovider'):
        # Provider viewing their requests
        requests = ServiceRequest.objects.filter(provider=request.user.serviceprovider)
    else:
        # Customer viewing their requests
        requests = ServiceRequest.objects.filter(customer=request.user)
    
    serializer = ServiceRequestSerializer(requests, many=True)
    return Response(serializer.data)
# ------------------------- Provider List -------------------------
@api_view(['GET'])
def provider_list(request):
    providers = ServiceProvider.objects.all().select_related('user', 'category')
    serializer = ServiceProviderSerializer(providers, many=True)
    return Response(serializer.data)

# ------------------------- Provider Detail -------------------------
@api_view(['GET'])
def provider_detail(request, pk):
    try:
        provider = ServiceProvider.objects.get(pk=pk)
        serializer = ServiceProviderSerializer(provider)
        return Response(serializer.data)
    except ServiceProvider.DoesNotExist:
        return Response({'error': 'Provider not found'}, status=status.HTTP_404_NOT_FOUND)

# ------------------------- Discover Services -------------------------
@api_view(['GET'])
def discover_services(request):
    """
    Discover services near user with distance-based sorting
    Example: /api/discover/?service=electrician&address=123+Main+St&radius=3000
    """
    service_type = request.GET.get('service')
    address = request.GET.get('address')
    radius = request.GET.get('radius', 5000)

    # Validate service type
    if not service_type:
        return Response({'error': 'Service type is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        valid_services = ServiceCategory.objects.values_list('name', flat=True)
        valid_services = [s.lower() for s in valid_services]
        if service_type.lower() not in valid_services:
            return Response(
                {'error': f'Invalid service type. Valid options: {", ".join(valid_services)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
    except Exception:
        return Response({'error': 'Could not validate service types'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    try:
        # Get coordinates
        lat, lng = geocode_address(address) if address else get_current_location()
        if not lat or not lng or not validate_coordinates(lat, lng):
            return Response({'error': 'Could not determine valid location.'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate radius
        radius = int(radius)
        if radius <= 0 or radius > 50000:
            raise ValueError

        # Get Google Places results
        results = get_nearby_services(lat, lng, service_type.lower(), radius)

        # Get local providers sorted by distance
        local_providers = ServiceProvider.objects.filter(
            category__name__iexact=service_type
        ).annotate(
            distance=ExpressionWrapper(
                Sqrt(
                    Power(F('latitude') - lat, 2) + 
                    Power(F('longitude') - lng, 2)
                ),
                output_field=FloatField()
            )
        ).order_by('distance')[:10]  # Get 10 nearest providers

        local_results = [{
            'name': f"{p.user.get_full_name() or p.user.username} (NearMeConnect)",
            'address': p.address,
            'location': {'lat': p.latitude, 'lng': p.longitude},
            'distance_km': round(p.distance * 111, 2),  # Convert to approximate km
            'maps_link': f"https://www.google.com/maps/search/?api=1&query={p.latitude},{p.longitude}",
            'phone': p.phone,
            'rating': p.rating,
            'is_local': True,
            'provider_id': p.id
        } for p in local_providers]

        return Response({
            'service_type': service_type,
            'user_location': {'lat': lat, 'lng': lng},
            'radius': radius,
            'google_results': results.get('results', []),
            'local_providers': local_results
        })

    except ValueError:
        return Response(
            {'error': 'Radius must be a positive number (max 50000)'},
            status=status.HTTP_400_BAD_REQUEST
        )
    except requests.exceptions.RequestException as e:
        return Response(
            {'error': f'Google API request failed: {str(e)}'},
            status=status.HTTP_502_BAD_GATEWAY
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# ------------------------- Update Provider Location -------------------------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_provider_location(request):
    """Update provider location with validation"""
    if not hasattr(request.user, 'serviceprovider'):
        return Response(
            {'error': 'Only service providers can update location'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        lat = float(request.data.get('latitude'))
        lng = float(request.data.get('longitude'))
        
        if not validate_coordinates(lat, lng):
            return Response(
                {'error': 'Invalid coordinates - out of valid range'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        provider = request.user.serviceprovider
        provider.latitude = lat
        provider.longitude = lng
        provider.save()
        
        return Response({
            'message': 'Location updated successfully',
            'location': {'lat': lat, 'lng': lng}
        })
        
    except (TypeError, ValueError):
        return Response(
            {'error': 'Invalid coordinate format'},
            status=status.HTTP_400_BAD_REQUEST
        )

# ------------------------- Create Service Request -------------------------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_service_request(request, provider_id):
    """Create service request with automatic distance check"""
    provider = get_object_or_404(ServiceProvider, pk=provider_id)
    
    # Get requester's location
    lat, lng = get_current_location()
    if not lat or not lng or not validate_coordinates(lat, lng):
        return Response(
            {'error': 'Could not determine your location'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Calculate distance (simplified haversine)
    distance = ((lat - provider.latitude)**2 + (lng - provider.longitude)**2)**0.5
    if distance > 0.1:  # ~11km threshold
        return Response(
            {'error': 'Provider is too far from your location'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    serializer = ServiceRequestSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(customer=request.user, provider=provider)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    # In views.py - update the function name
@api_view(['GET'])
def place_details(request, place_id):  # Changed from get_place_details
    if not place_id:
        return Response({'error': 'Place ID is required'}, status=status.HTTP_400_BAD_REQUEST)

    if place_id.isdigit():
        try:
            provider = ServiceProvider.objects.get(pk=int(place_id))
            serializer = ServiceProviderSerializer(provider)
            return Response({'is_local': True, 'result': serializer.data})
        except ServiceProvider.DoesNotExist:
            pass

    results = get_place_details(place_id)  # This calls the google_api function
    if results.get('status') != 'OK':
        return Response({'error': results.get('error_message', 'Place not found')}, 
                       status=status.HTTP_404_NOT_FOUND)

    return Response({'is_local': False, 'result': results.get('result')})


#   CRUD
class ServiceCategoryListCreate(generics.ListCreateAPIView):
    queryset = ServiceCategory.objects.all()
    serializer_class = ServiceCategorySerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method == 'POST':
            print("apicalled")
            return [IsAdminUser()]
        return super().get_permissions()

class ServiceCategoryRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    queryset = ServiceCategory.objects.all()
    serializer_class = ServiceCategorySerializer
    permission_classes = [IsAuthenticated,IsAdminUser]

# ServiceProvider CRUD
class ServiceProviderListCreate(generics.ListCreateAPIView):
    queryset = ServiceProvider.objects.all()
    serializer_class = ServiceProviderSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        if self.request.user.userprofile.is_service_provider:
            serializer.save(user=self.request.user)

class ServiceProviderRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    queryset = ServiceProvider.objects.all()
    serializer_class = ServiceProviderSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [IsAuthenticated()]
        return super().get_permissions()

# ServiceRequest CRUD
class ServiceRequestListCreate(generics.ListCreateAPIView):
    serializer_class = ServiceRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'serviceprovider'):
            return ServiceRequest.objects.filter(provider=user.serviceprovider)
        return ServiceRequest.objects.filter(customer=user)

    def perform_create(self, serializer):
        if not self.request.user.userprofile.is_service_provider:
            serializer.save(customer=self.request.user)

class ServiceRequestRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    queryset = ServiceRequest.objects.all()
    serializer_class = ServiceRequestSerializer
    permission_classes = [IsAuthenticated]

# Review CRUD
class ReviewListCreate(generics.ListCreateAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        provider_id = self.request.query_params.get('provider_id')
        if provider_id:
            return Review.objects.filter(provider_id=provider_id)
        return Review.objects.filter(customer=self.request.user)

    def perform_create(self, serializer):
        serializer.save(customer=self.request.user)

class ReviewRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]
    