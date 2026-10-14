from django.contrib import admin
from .models import CartItem, CropListing, Order, OrderItem
@admin.register(CropListing)
class CropListingAdmin(admin.ModelAdmin):
    list_display = ("name", "variety", "farmer", "district", "price_per_kg", "stock_kg", "is_active")
    search_fields = ("name", "variety", "district", "farmer__username")
    list_filter = ("district", "is_active")
admin.site.register(CartItem)
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("crop_name", "quantity_kg", "unit_price")
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "status", "total", "created_at")
    inlines = [OrderItemInline]
