from django.utils.functional import SimpleLazyObject

from .services import get_or_create_cart


class CartMiddleware:
    """Attaches the current user's/session's cart to every request as request.cart (lazy)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.cart = SimpleLazyObject(lambda: get_or_create_cart(request))
        return self.get_response(request)
