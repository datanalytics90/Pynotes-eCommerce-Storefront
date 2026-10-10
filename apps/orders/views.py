import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from razorpay.errors import BadRequestError, GatewayError, ServerError

from apps.cart import services as cart_services

from . import services
from .forms import CheckoutForm, IssueReportForm, OrderTrackingForm
from .invoice import invoice_response
from .models import Order

logger = logging.getLogger(__name__)


def checkout(request):
    cart = request.cart
    if cart.total_items == 0:
        messages.warning(request, "Your cart is empty.")
        return redirect("catalog:product_list")

    initial = {"country": "India"}
    if request.user.is_authenticated:
        initial["email"] = request.user.email
        initial["first_name"] = request.user.first_name
        initial["last_name"] = request.user.last_name
        default_address = request.user.addresses.filter(is_default=True).first()
        if default_address:
            name_parts = default_address.full_name.split(" ", 1)
            initial["first_name"] = name_parts[0]
            initial["last_name"] = name_parts[1] if len(name_parts) > 1 else ""
            initial.update(
                line1=default_address.line1,
                line2=default_address.line2,
                city=default_address.city,
                state=default_address.state,
                postal_code=default_address.postal_code,
                phone_number=default_address.phone_number,
            )

    if request.method == "POST":
        form = CheckoutForm(request.POST, initial=initial)
        if form.is_valid():
            payment_method = form.cleaned_data["payment_method"]
            order = services.create_order_from_cart(
                cart=cart,
                email=form.cleaned_data["email"],
                shipping_data=form.shipping_data(),
                payment_method=payment_method,
                user=request.user if request.user.is_authenticated else None,
            )

            if payment_method == Order.PaymentMethod.COD:
                services.mark_order_processing(order, note="COD order placed")
                cart_services.clear(cart)
                messages.success(request, "Your Cash on Delivery order has been placed!")
                return redirect("orders:success", order_number=order.order_number)

            # Prepaid
            if not services.razorpay_is_configured():
                services.mark_order_processing(order, note="Prepaid order (demo mode — Razorpay not configured)")
                cart_services.clear(cart)
                messages.info(
                    request, "Razorpay is not configured on this server, so payment was simulated in demo mode."
                )
                return redirect("orders:success", order_number=order.order_number)

            try:
                services.create_razorpay_order(order)
            except (BadRequestError, GatewayError, ServerError, ConnectionError) as exc:
                logger.error("Razorpay order creation failed for %s: %s", order.order_number, exc)
                order.status = Order.Status.FAILED
                order.save(update_fields=["status"])
                order.status_history.create(status=Order.Status.FAILED, note="Razorpay order creation failed")
                messages.error(
                    request,
                    "We couldn't reach Razorpay to start your payment. Please try again, or choose "
                    "Cash on Delivery.",
                )
                return redirect("orders:checkout")
            return redirect("orders:razorpay_payment", order_number=order.order_number)
    else:
        form = CheckoutForm(initial=initial)

    return render(request, "orders/checkout.html", {"form": form, "cart": cart})


def razorpay_payment(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, status=Order.Status.PENDING_PAYMENT)
    return render(
        request,
        "orders/razorpay_payment.html",
        {
            "order": order,
            "razorpay_key_id": settings.RAZORPAY_KEY_ID,
            "amount_paise": int(order.total * 100),
        },
    )


@require_POST
def razorpay_verify(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    payment_id = request.POST.get("razorpay_payment_id", "")
    razorpay_order_id = request.POST.get("razorpay_order_id", "")
    signature = request.POST.get("razorpay_signature", "")

    try:
        services.verify_razorpay_payment(order, payment_id, razorpay_order_id, signature)
    except Exception:
        return JsonResponse({"ok": False, "error": "Signature verification failed."}, status=400)

    services.mark_order_processing(order, note="Razorpay payment verified")
    cart_services.clear(request.cart)
    return JsonResponse({"ok": True, "redirect_url": f"/orders/success/{order.order_number}/"})


@require_POST
def razorpay_failed(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    order.status = Order.Status.FAILED
    order.save(update_fields=["status"])
    order.status_history.create(status=Order.Status.FAILED, note="Razorpay payment failed")
    return JsonResponse({"ok": True})


def success(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    return render(request, "orders/success.html", {"order": order})


@login_required
def order_history(request):
    orders = request.user.orders.all()
    return render(request, "orders/order_history.html", {"orders": orders})


@login_required
def order_detail(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    return render(request, "orders/order_detail.html", {"order": order})


@login_required
def download_invoice(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    return invoice_response(order)


@login_required
def report_issue(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    if request.method == "POST":
        form = IssueReportForm(request.POST, request.FILES)
        if form.is_valid():
            issue = form.save(commit=False)
            issue.order = order
            issue.was_within_window = order.issue_window_open
            issue.save()
            messages.success(request, "Thanks — we've received your report and will be in touch.")
            return redirect("orders:order_detail", order_number=order.order_number)
    else:
        form = IssueReportForm()
    return render(request, "account/report_issue.html", {"form": form, "order": order})


def order_tracking(request):
    order = None
    if request.method == "POST":
        form = OrderTrackingForm(request.POST)
        if form.is_valid():
            order = Order.objects.filter(
                order_number=form.cleaned_data["order_number"], email__iexact=form.cleaned_data["email"]
            ).first()
            if not order:
                messages.error(request, "We couldn't find an order matching that number and email.")
    else:
        form = OrderTrackingForm()
    return render(request, "account/order_tracking.html", {"form": form, "order": order})
