from django.urls import path

from . import views

app_name = "orders"

urlpatterns = [
    path("checkout/", views.checkout, name="checkout"),
    path("success/<uuid:order_number>/", views.success, name="success"),
    path("webhook/stripe/", views.StripeWebhookView.as_view(), name="stripe_webhook"),
    path("history/", views.order_history, name="order_history"),
    path("<uuid:order_number>/", views.order_detail, name="order_detail"),
]
