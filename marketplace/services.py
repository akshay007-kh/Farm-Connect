from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import transaction
from .models import CartItem, CropListing, Order, OrderItem
@transaction.atomic
def checkout(customer, delivery):
    cart = list(CartItem.objects.filter(customer=customer).select_related("listing"))
    if not cart:
        raise ValidationError("Your cart is empty.")
    order = Order.objects.create(
        customer=customer,
        delivery_name=delivery["full_name"],
        delivery_phone=delivery["phone"],
        delivery_address=delivery["address"],
        delivery_city=delivery["city"],
        delivery_district=delivery["district"],
        delivery_postal_code=delivery["postal_code"],
    )
    total = Decimal("0.00")
    for item in cart:
        listing = CropListing.objects.select_for_update().get(pk=item.listing_id)
        qty = item.quantity_kg
        if not listing.is_active or qty <= 0 or listing.stock_kg < qty:
            raise ValidationError(f"Not enough stock for {listing.name}. Update your cart.")
        OrderItem.objects.create(order=order, listing=listing, crop_name=listing.name, quantity_kg=qty, unit_price=listing.price_per_kg)
        listing.stock_kg -= qty
        listing.save(update_fields=["stock_kg"])
        total += listing.price_per_kg * qty
    order.total = total
    order.save(update_fields=["total"])
    CartItem.objects.filter(customer=customer).delete()
    return order
