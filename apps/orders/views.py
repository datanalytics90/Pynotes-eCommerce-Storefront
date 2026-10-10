import stripe
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from apps.cart import services as cart_services

from . import services
from .forms import CheckoutForm
from .models import Order


def checkout(request):
    cart = request.cart
    if cart.total_items == 0:
        messages.warning(request, "Your cart is empty.")
        return redirect("catalog:product_list")

    initial = {}
    if request.user.is_authenticated:
        initial["email"] = request.user.email
        default_address = request.user.addresses.filter(is_default=True).first()
        if default_address:
            initial.update(
                full_name=default_address.full_name,
                line1=default_address.line1,
                line2=default_address.line2,
                city=default_address.city,
                state=default_address.state,
                postal_code=default_address.postal_code,
                country=default_address.country,
                phone_number=default_address.phone_number,
            )

    if request.method == "POST":
        form = CheckoutForm(request.POST, initial=initial)
        if form.is_valid():
            order = services.create_order_from_cart(
                cart=cart,
                email=form.cleaned_data["email"],
                shipping_data=form.cleaned_data,
                user=request.user if request.user.is_authenticated else None,
            )

            if not services.stripe_is_configured():
                services.mark_order_paid(order)
                cart_services.clear(cart)
                messages.info(
                    request,
                    "Stripe is not configured on this server, so payment was simulated in demo mode.",
                )
                return redirect("orders:success", order_number=order.order_number)

            session = services.create_checkout_session(order, request)
            return redirect(session.url, permanent=False)
    else:
        form = CheckoutForm(initial=initial)

    return render(request, "orders/checkout.html", {"form": form, "cart": cart})


def success(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    session_id = request.GET.get("session_id")
    if session_id and order.status == Order.Status.PENDING and services.stripe_is_configured():
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            if session.payment_status == "paid":
                services.mark_order_paid(order, payment_intent_id=session.get("payment_intent", "") or "")
                cart_services.clear(request.cart)
        except stripe.error.StripeError:
            pass
    return render(request, "orders/success.html", {"order": order})


@method_decorator(csrf_exempt, name="dispatch")
class StripeWebhookView(View):
    def post(self, request):
        payload = request.body
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")

        if settings.STRIPE_WEBHOOK_SECRET:
            try:
                event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
            except (ValueError, stripe.error.SignatureVerificationError):
                return HttpResponseBadRequest("Invalid webhook signature")
        else:
            import json

            event = json.loads(payload)

        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]
            order_number = session.get("metadata", {}).get("order_number")
            if order_number:
                try:
                    order = Order.objects.get(order_number=order_number)
                    services.mark_order_paid(order, payment_intent_id=session.get("payment_intent", "") or "")
                except Order.DoesNotExist:
                    pass

        return HttpResponse(status=200)


@login_required
def order_history(request):
    orders = request.user.orders.all()
    return render(request, "orders/order_history.html", {"orders": orders})


@login_required
def order_detail(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    return render(request, "orders/order_detail.html", {"order": order})
