from django.urls import path

from . import views

app_name = "cart"

urlpatterns = [
    path("", views.cart_detail, name="cart_detail"),
    path("add/<slug:slug>/", views.add_to_cart, name="add_to_cart"),
    path("buy-now/<slug:slug>/", views.buy_now, name="buy_now"),
    path("update/<int:product_id>/", views.update_cart_item, name="update_cart_item"),
    path("remove/<int:product_id>/", views.remove_from_cart, name="remove_from_cart"),
    path("coupon/apply/", views.apply_coupon, name="apply_coupon"),
    path("coupon/remove/", views.remove_coupon, name="remove_coupon"),
]
