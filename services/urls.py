from django.urls import path
from .views import (
    UserCreateView, CustomTokenObtainPairView,
    discover_services, place_details, update_provider_location,
    create_service_request,
    ServiceCategoryListCreate, ServiceCategoryRetrieveUpdateDestroy,
    ServiceProviderListCreate, ServiceProviderRetrieveUpdateDestroy,
    ServiceRequestListCreate, ServiceRequestRetrieveUpdateDestroy,
    ReviewListCreate, ReviewRetrieveUpdateDestroy, admin_login 
)
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    # Authentication endpoints
    path('auth/register/', UserCreateView.as_view(), name='register'),
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Special function endpoints
    path('discover/', discover_services, name='discover-services'),
    path('places/<str:place_id>/', place_details, name='place-details'),
    path('update-location/', update_provider_location, name='update-location'),
    path('providers/<int:provider_id>/request/', create_service_request, name='create-request'),
    
    # CRUD endpoints
    path('categories/', ServiceCategoryListCreate.as_view(), name='category-list'),
    path('categories/<int:pk>/', ServiceCategoryRetrieveUpdateDestroy.as_view(), name='category-detail'),
    path('providers/', ServiceProviderListCreate.as_view(), name='provider-list'),
    path('providers/<int:pk>/', ServiceProviderRetrieveUpdateDestroy.as_view(), name='provider-detail'),
    path('requests/', ServiceRequestListCreate.as_view(), name='request-list'),
    path('requests/<int:pk>/', ServiceRequestRetrieveUpdateDestroy.as_view(), name='request-detail'),
    path('reviews/', ReviewListCreate.as_view(), name='review-list'),
    path('reviews/<int:pk>/', ReviewRetrieveUpdateDestroy.as_view(), name='review-detail'),
    path('auth/admin/login/', admin_login, name='admin-login'),
]