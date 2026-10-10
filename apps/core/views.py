from django.contrib import messages
from django.shortcuts import redirect, render

from apps.catalog.models import Category, Product

from .forms import ContactForm


def home(request):
    featured_products = Product.objects.filter(is_active=True, is_featured=True).select_related("category")[:8]
    new_arrivals = Product.objects.filter(is_active=True).select_related("category").order_by("-created_at")[:8]
    categories = Category.objects.filter(is_active=True)[:6]
    return render(
        request,
        "core/home.html",
        {
            "featured_products": featured_products,
            "new_arrivals": new_arrivals,
            "categories": categories,
        },
    )


def about(request):
    return render(request, "core/about.html")


def contact(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Thanks for reaching out — we'll get back to you soon.")
            return redirect("core:contact")
    else:
        form = ContactForm()
    return render(request, "core/contact.html", {"form": form})
