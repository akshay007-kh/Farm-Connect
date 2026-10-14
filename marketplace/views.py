from decimal import Decimal, InvalidOperation
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth import get_user_model
from .forms import CropListingForm, StaffCropListingForm
from .order_forms import CheckoutForm
from .models import CartItem, CropListing, Order, OrderItem
from .services import checkout
User = get_user_model()

def home(request):
    listings = CropListing.objects.filter(is_active=True, stock_kg__gt=0).select_related("farmer")
    q, district = request.GET.get("q", "").strip(), request.GET.get("district", "").strip()
    if q:
        listings = listings.filter(name__icontains=q) | listings.filter(variety__icontains=q)
    if district:
        listings = listings.filter(district__icontains=district)
    return render(request, "marketplace/home.html", {"listings":listings[:9], "q":q, "district":district, "total_listings":CropListing.objects.filter(is_active=True).count()})
def _customer(user): return user.is_authenticated and user.role == user.Role.CUSTOMER
@login_required
def add_to_cart(request, listing_id):
    if request.method != "POST" or not _customer(request.user):
        return redirect("home")
    listing = get_object_or_404(CropListing, pk=listing_id, is_active=True)
    action = request.POST.get("action", "cart")
    try:
        qty = Decimal(request.POST.get("quantity_kg", "1"))
    except InvalidOperation:
        qty = Decimal("0")
    valid = True
    if not qty.is_finite() or qty <= 0:
        valid = False
        messages.error(request, "Enter a valid quantity greater than zero.")
    else:
        existing = CartItem.objects.filter(customer=request.user, listing=listing).first()
        new_quantity = qty + (existing.quantity_kg if existing else Decimal("0"))
        if new_quantity > listing.stock_kg:
            valid = False
            messages.error(request, f"Choose a quantity within the available {listing.stock_kg} kg.")
        elif existing:
            existing.quantity_kg = new_quantity
            existing.save(update_fields=["quantity_kg"])
            messages.success(request, "Cart quantity updated.")
        else:
            CartItem.objects.create(customer=request.user, listing=listing, quantity_kg=qty)
            messages.success(request, "Added to cart.")
    return redirect("checkout" if action == "buy" and valid else "cart")
@login_required
def cart(request):
    if not _customer(request.user): return redirect("home")
    items = list(CartItem.objects.filter(customer=request.user).select_related("listing"))
    subtotal = sum((item.line_total for item in items), Decimal("0.00"))
    return render(request, "marketplace/cart.html", {"items":items, "subtotal":subtotal, "item_count":sum(item.quantity_kg for item in items)})

@login_required
def update_cart_item(request, item_id):
    if request.method != "POST" or not _customer(request.user): return redirect("cart")
    item = get_object_or_404(CartItem.objects.select_related("listing"), pk=item_id, customer=request.user)
    try: quantity = Decimal(request.POST.get("quantity_kg", "0"))
    except InvalidOperation: quantity = Decimal("0")
    if not quantity.is_finite() or quantity <= 0:
        messages.error(request, "Enter a quantity greater than zero.")
    elif quantity > item.listing.stock_kg:
        messages.error(request, f"Only {item.listing.stock_kg} kg of {item.listing.name} is available.")
    else:
        item.quantity_kg = quantity
        item.save(update_fields=["quantity_kg"])
        messages.success(request, "Cart quantity updated.")
    return redirect("cart")

@login_required
def remove_cart_item(request, item_id):
    if request.method == "POST" and _customer(request.user):
        CartItem.objects.filter(pk=item_id, customer=request.user).delete()
        messages.success(request, "Item removed from your cart.")
    return redirect("cart")
@login_required
def place_order(request):
    if not _customer(request.user):
        return redirect("cart")
    items = list(CartItem.objects.filter(customer=request.user).select_related("listing"))
    if not items:
        messages.info(request, "Your cart is empty. Add a few fresh picks before checkout.")
        return redirect("cart")
    subtotal = sum((item.line_total for item in items), Decimal("0.00"))
    form = CheckoutForm(request.POST or None, user=request.user)
    if request.method == "GET":
        return render(request, "marketplace/checkout.html", {"form":form, "items":items, "subtotal":subtotal})
    if request.method != "POST": return redirect("cart")
    if not form.is_valid():
        return render(request, "marketplace/checkout.html", {"form":form, "items":items, "subtotal":subtotal})
    try:
        order = checkout(request.user, form.cleaned_data)
    except ValidationError as exc:
        messages.error(request, " ".join(exc.messages))
        return redirect("cart")
    request.user.phone = form.cleaned_data["phone"]
    request.user.district = form.cleaned_data["district"]
    request.user.delivery_address = form.cleaned_data["address"]
    request.user.delivery_city = form.cleaned_data["city"]
    request.user.delivery_postal_code = form.cleaned_data["postal_code"]
    request.user.save(update_fields=["phone", "district", "delivery_address", "delivery_city", "delivery_postal_code"])
    return render(request, "marketplace/order_success.html", {"order":order})
@login_required
def orders(request):
    if not _customer(request.user): return redirect("home")
    return render(request, "marketplace/orders.html", {"orders":Order.objects.filter(customer=request.user).prefetch_related("items")})
@login_required
def dashboard(request):
    if request.user.is_staff or request.user.is_superuser:
        return redirect("staff_dashboard")
    if request.user.role != request.user.Role.FARMER:
        return redirect("customer_dashboard")
    listings = CropListing.objects.filter(farmer=request.user)
    mine = Order.objects.filter(items__listing__farmer=request.user).distinct().order_by("-created_at")
    return render(request, "marketplace/dashboard.html", {"listings":listings, "stock_total":listings.aggregate(total=Sum("stock_kg"))["total"] or 0, "order_count":mine.count(), "recent_orders":mine[:5]})

@login_required
def customer_dashboard(request):
    if request.user.is_staff or request.user.is_superuser: return redirect("staff_dashboard")
    if request.user.role == request.user.Role.FARMER: return redirect("dashboard")
    if request.user.role == request.user.Role.EXPERT: return redirect("expert_dashboard")
    recent = Order.objects.filter(customer=request.user).order_by("-created_at")[:4]
    return render(request, "marketplace/customer_dashboard.html", {"recent_orders":recent, "cart_count":CartItem.objects.filter(customer=request.user).count(), "listing_count":CropListing.objects.filter(is_active=True).count()})

@login_required
def expert_dashboard(request):
    if request.user.is_staff or request.user.is_superuser: return redirect("staff_dashboard")
    if request.user.role != request.user.Role.EXPERT: return redirect("dashboard" if request.user.role == request.user.Role.FARMER else "customer_dashboard")
    from advisory.models import Consultation
    return render(request, "marketplace/expert_dashboard.html", {"consultations":Consultation.objects.filter(expert=request.user).order_by("-created_at")[:8]})

@login_required
def farmer_listing_create(request):
    if request.user.role != request.user.Role.FARMER: return redirect("home")
    form = CropListingForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        listing = form.save(commit=False); listing.farmer = request.user; listing.save()
        messages.success(request, "Crop listing published."); return redirect("dashboard")
    return render(request, "marketplace/listing_form.html", {"form":form, "page_title":"Add a crop listing", "back_url":"dashboard"})

@login_required
def farmer_listing_edit(request, listing_id):
    listing = get_object_or_404(CropListing, pk=listing_id, farmer=request.user) if request.user.role == request.user.Role.FARMER else None
    if listing is None: return redirect("home")
    form = CropListingForm(request.POST or None, request.FILES or None, instance=listing)
    if request.method == "POST" and form.is_valid():
        form.save(); messages.success(request, "Listing updated."); return redirect("dashboard")
    return render(request, "marketplace/listing_form.html", {"form":form, "page_title":"Edit crop listing", "back_url":"dashboard"})

@staff_member_required(login_url="login")
def staff_dashboard(request):
    context = {
        "farmer_count":User.objects.filter(role=User.Role.FARMER).count(),
        "customer_count":User.objects.filter(role=User.Role.CUSTOMER).count(),
        "expert_count":User.objects.filter(role=User.Role.EXPERT).count(),
        "listing_count":CropListing.objects.count(),
        "active_listing_count":CropListing.objects.filter(is_active=True).count(),
        "order_count":Order.objects.count(),
        "revenue":Order.objects.exclude(status=Order.Status.CANCELLED).aggregate(total=Sum("total"))["total"] or 0,
        "users":User.objects.order_by("-date_joined")[:8],
        "listings":CropListing.objects.select_related("farmer").order_by("-created_at")[:8],
        "orders":Order.objects.select_related("customer").order_by("-created_at")[:8],
        "status_choices":Order.Status.choices,
    }
    return render(request, "marketplace/staff_dashboard.html", context)

@staff_member_required(login_url="login")
def staff_listing_create(request):
    form = StaffCropListingForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        form.save(); messages.success(request, "Crop listing created."); return redirect("staff_dashboard")
    return render(request, "marketplace/listing_form.html", {"form":form, "page_title":"Create crop listing", "back_url":"staff_dashboard"})

@staff_member_required(login_url="login")
def staff_listing_edit(request, listing_id):
    listing = get_object_or_404(CropListing, pk=listing_id)
    form = StaffCropListingForm(request.POST or None, request.FILES or None, instance=listing)
    if request.method == "POST" and form.is_valid():
        form.save(); messages.success(request, "Listing updated."); return redirect("staff_dashboard")
    return render(request, "marketplace/listing_form.html", {"form":form, "page_title":"Edit crop listing", "back_url":"staff_dashboard"})

@staff_member_required(login_url="admin_login")
def staff_members(request):
    role_filter = request.GET.get("role", "")
    members = User.objects.filter(is_superuser=False, is_staff=False).order_by("-date_joined")
    if role_filter in User.Role.values:
        members = members.filter(role=role_filter)
    return render(request, "marketplace/staff_members.html", {"members":members, "role_filter":role_filter, "role_choices":User.Role.choices})

@staff_member_required(login_url="admin_login")
def staff_member_update(request, user_id):
    if request.method == "POST":
        member = get_object_or_404(User, pk=user_id, is_staff=False, is_superuser=False)
        next_role = request.POST.get("role")
        if next_role in User.Role.values:
            member.role = next_role
            member.is_active = request.POST.get("is_active") == "true"
            member.save(update_fields=["role", "is_active"])
            messages.success(request, f"Account for {member.username} updated.")
    return redirect("staff_members")

@staff_member_required(login_url="login")
def staff_order_status(request, order_id):
    if request.method == "POST":
        with transaction.atomic():
            order = get_object_or_404(Order.objects.select_for_update(), pk=order_id)
            next_status = request.POST.get("status")
            if next_status in Order.Status.values:
                if order.status == Order.Status.CANCELLED and next_status != Order.Status.CANCELLED:
                    messages.error(request, "Cancelled orders cannot be reopened from this dashboard.")
                else:
                    if next_status == Order.Status.CANCELLED and order.status != Order.Status.CANCELLED:
                        for item in order.items.select_related("listing"):
                            listing = CropListing.objects.select_for_update().get(pk=item.listing_id)
                            listing.stock_kg += item.quantity_kg
                            listing.save(update_fields=["stock_kg"])
                    order.status = next_status
                    order.save(update_fields=["status"])
                    messages.success(request, f"Order #{order.pk} updated.")
    return redirect("staff_dashboard")
