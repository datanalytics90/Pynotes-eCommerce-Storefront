from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.catalog.models import Coupon, Product

from . import services


def cart_detail(request):
    cart = request.cart
    return render(request, "cart/cart_detail.html", {"cart": cart})


@require_POST
def add_to_cart(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    quantity = int(request.POST.get("quantity", 1) or 1)
    if quantity < 1:
        quantity = 1
    if not product.is_digital and quantity > product.stock:
        quantity = max(product.stock, 0)
    if not product.is_digital and product.stock <= 0:
        messages.error(request, f"{product.name} is out of stock.")
    else:
        services.add_item(request.cart, product, quantity)
        messages.success(request, f"Added {product.name} to your cart.")

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"ok": True, "total_items": request.cart.total_items})
    return redirect(request.META.get("HTTP_REFERER", "cart:cart_detail"))


@require_POST
def update_cart_item(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    quantity = int(request.POST.get("quantity", 1) or 0)
    services.set_item_quantity(request.cart, product, quantity)
    return redirect("cart:cart_detail")


@require_POST
def remove_from_cart(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    services.remove_item(request.cart, product)
    messages.info(request, f"Removed {product.name} from your cart.")
    return redirect("cart:cart_detail")


@require_POST
def apply_coupon(request):
    code = request.POST.get("code", "").strip().upper()
    cart = request.cart
    try:
        coupon = Coupon.objects.get(code=code)
    except Coupon.DoesNotExist:
        messages.error(request, "That coupon code is not valid.")
        return redirect("cart:cart_detail")

    if not coupon.is_valid():
        messages.error(request, "That coupon has expired or is no longer active.")
        return redirect("cart:cart_detail")

    cart.coupon = coupon
    cart.save(update_fields=["coupon"])
    messages.success(request, f"Coupon {coupon.code} applied — {coupon.discount_percent}% off!")
    return redirect("cart:cart_detail")


@require_POST
def remove_coupon(request):
    cart = request.cart
    cart.coupon = None
    cart.save(update_fields=["coupon"])
    messages.info(request, "Coupon removed.")
    return redirect("cart:cart_detail")
