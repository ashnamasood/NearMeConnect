from django.db import models
from django.contrib.auth.models import User

class ServiceCategory(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class ServiceProvider(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE)
    bio = models.TextField()
    phone = models.CharField(max_length=15)
    address = models.CharField(max_length=255)
    latitude = models.FloatField()
    longitude = models.FloatField()
    profile_image = models.ImageField(upload_to='profiles/')
    rating = models.FloatField(default=0)

    def __str__(self):
        return f"{self.user.username} - {self.category.name}"

class ServiceRequest(models.Model):
    customer = models.ForeignKey(User, on_delete=models.CASCADE)
    provider = models.ForeignKey(ServiceProvider, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_accepted = models.BooleanField(default=False)
    is_completed = models.BooleanField(default=False)

    def __str__(self):
        return f"Request from {self.customer.username} to {self.provider.user.username}"

class Review(models.Model):
    customer = models.ForeignKey(User, on_delete=models.CASCADE)
    provider = models.ForeignKey(ServiceProvider, on_delete=models.CASCADE)
    rating = models.IntegerField()
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer.username} → {self.provider.user.username} ({self.rating})"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15, blank=True)
    is_service_provider = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username