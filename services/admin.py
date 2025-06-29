
from django.contrib import admin
from .models import ServiceCategory, ServiceProvider, ServiceRequest, Review
from .google_api import geocode_address 
@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


@admin.register(ServiceProvider)
class ServiceProviderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'category', 'phone')
    search_fields = ('user__username', 'phone', 'address')
    exclude = ('latitude', 'longitude')  # 👈 Hide from admin form

    def save_model(self, request, obj, form, change):
        # Auto-fill lat/lng from address
        if obj.address:
            lat, lng = geocode_address(obj.address)
            if lat and lng:
                obj.latitude = lat
                obj.longitude = lng
        super().save_model(request, obj, form, change)


@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'provider', 'created_at', 'is_accepted', 'is_completed')
    list_filter = ('is_accepted', 'is_completed')

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'provider', 'rating', 'created_at')
    list_filter = ('rating',)
