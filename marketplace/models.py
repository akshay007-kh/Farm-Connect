from django.conf import settings
from django.db import models
class CropListing(models.Model):
    farmer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="listings")
    name = models.CharField(max_length=120)
    variety = models.CharField(max_length=120, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="crop_listings/", blank=True, null=True)
    price_per_kg = models.DecimalField(max_digits=10, decimal_places=2)
    stock_kg = models.DecimalField(max_digits=10, decimal_places=2)
    district = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ["name", "-created_at"]
    def __str__(self): return f"{self.name} — {self.farmer}"
class CartItem(models.Model):
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cart_items")
    listing = models.ForeignKey(CropListing, on_delete=models.CASCADE)
    quantity_kg = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    class Meta: constraints = [models.UniqueConstraint(fields=["customer", "listing"], name="unique_cart_listing")]
    @property
    def line_total(self): return self.quantity_kg * self.listing.price_per_kg
class Order(models.Model):
    class Status(models.TextChoices):
        PLACED = "placed", "Placed"
        ACCEPTED = "accepted", "Accepted"
        FULFILLED = "fulfilled", "Fulfilled"
        CANCELLED = "cancelled", "Cancelled"
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="orders")
    delivery_name = models.CharField(max_length=120, blank=True)
    delivery_phone = models.CharField(max_length=20, blank=True)
    delivery_address = models.TextField(blank=True)
    delivery_city = models.CharField(max_length=100, blank=True)
    delivery_district = models.CharField(max_length=100, blank=True)
    delivery_postal_code = models.CharField(max_length=10, blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PLACED)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    listing = models.ForeignKey(CropListing, on_delete=models.PROTECT)
    crop_name = models.CharField(max_length=120)
    quantity_kg = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    @property
    def line_total(self): return self.quantity_kg * self.unit_price
