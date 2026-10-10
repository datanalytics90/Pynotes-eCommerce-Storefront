from django.db import transaction

from .models import Cart, CartItem


def get_or_create_cart(request):
    if not request.session.session_key:
        request.session.create()

    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        # Merge any guest cart created before login into the user's cart.
        guest_cart = Cart.objects.filter(session_key=request.session.session_key, user__isnull=True).first()
        if guest_cart and guest_cart.pk != cart.pk:
            merge_carts(source=guest_cart, destination=cart)
        return cart

    cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key, user=None)
    return cart


@transaction.atomic
def merge_carts(source: Cart, destination: Cart):
    for item in source.items.all():
        existing = destination.items.filter(product=item.product).first()
        if existing:
            existing.quantity += item.quantity
            existing.save(update_fields=["quantity"])
        else:
            item.cart = destination
            item.save(update_fields=["cart"])
    source.delete()


def add_item(cart: Cart, product, quantity: int = 1):
    item, created = CartItem.objects.get_or_create(cart=cart, product=product, defaults={"quantity": quantity})
    if not created:
        item.quantity += quantity
        item.save(update_fields=["quantity"])
    return item


def set_item_quantity(cart: Cart, product, quantity: int):
    if quantity <= 0:
        cart.items.filter(product=product).delete()
        return None
    item, _ = CartItem.objects.get_or_create(cart=cart, product=product, defaults={"quantity": quantity})
    item.quantity = quantity
    item.save(update_fields=["quantity"])
    return item


def remove_item(cart: Cart, product):
    cart.items.filter(product=product).delete()


def clear(cart: Cart):
    cart.items.all().delete()
    cart.coupon = None
    cart.save(update_fields=["coupon"])
