# siteplans/models.py

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

DIRECTION_CHOICES = [
    ('N', 'North'),
    ('S', 'South'),
    ('E', 'East'),
    ('W', 'West'),
]

class City(models.Model):
    name = models.CharField(max_length=100)
    # Additional fields for future-proofing
    state = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, default='USA')

    def __str__(self):
        return self.name

class SitePlan(models.Model):
    city = models.ForeignKey(City, on_delete=models.PROTECT, related_name='site_plans')
    site_name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.site_name

class BoundaryPoint(models.Model):
    site_plan = models.ForeignKey(SitePlan, on_delete=models.CASCADE, related_name='boundary_points')
    direction1 = models.CharField(max_length=1, choices=DIRECTION_CHOICES)  # 'N' or 'S'
    angle_degrees = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(360)])
    angle_minutes = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(59)])
    angle_seconds = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(59)])
    direction2 = models.CharField(max_length=1, choices=DIRECTION_CHOICES)  # 'E' or 'W'
    length = models.FloatField(validators=[MinValueValidator(0.0)])  # Length should be positive

    def __str__(self):
        return f"{self.direction1}{self.angle_degrees}°{self.angle_minutes}'{self.angle_seconds}\"{self.direction2} - {self.length} ft"
