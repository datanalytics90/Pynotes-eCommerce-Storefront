from django.urls import path

from . import views

app_name = "orders"

urlpatterns = [
    path("checkout/", views.checkout, name="checkout"),
    path("pay/<uuid:order_number>/", views.razorpay_payment, name="razorpay_payment"),
    path("pay/<uuid:order_number>/verify/", views.razorpay_verify, name="razorpay_verify"),
    path("pay/<uuid:order_number>/failed/", views.razorpay_failed, name="razorpay_failed"),
    path("success/<uuid:order_number>/", views.success, name="success"),
    path("history/", views.order_history, name="order_history"),
    path("track/", views.order_tracking, name="order_tracking"),
    path("<uuid:order_number>/", views.order_detail, name="order_detail"),
    path("<uuid:order_number>/invoice/", views.download_invoice, name="download_invoice"),
    path("<uuid:order_number>/report-issue/", views.report_issue, name="report_issue"),
]
