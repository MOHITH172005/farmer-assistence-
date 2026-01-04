from django.db import models
from django.contrib.auth.models import User


class FarmerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    farmer_id = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=150)
    mobile = models.CharField(max_length=15, unique=True)

    pincode = models.CharField(max_length=6)
    district = models.CharField(max_length=100)
    state = models.CharField(max_length=100)

    primary_crop = models.CharField(max_length=100)
    land_area = models.DecimalField(max_digits=6, decimal_places=2)

    photo = models.ImageField(upload_to="farmer_photos/", null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    

    def __str__(self):
        return f"{self.farmer_id} - {self.full_name}"
        return self.full_name

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.message
class AIRequestLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    feature = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.feature}"
