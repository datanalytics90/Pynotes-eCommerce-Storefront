from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect, render

from apps.catalog.models import Product

from .forms import ContactForm
from .models import FAQ, LegalPage, Testimonial


def home(request):
    featured_products = (
        Product.objects.filter(is_active=True, is_featured=True, is_bundle=False)
        .select_related("category")[:8]
    )
    bundles = Product.objects.filter(is_active=True, is_bundle=True).order_by("price")[:5]
    book_count = Product.objects.filter(is_active=True, is_bundle=False).count()
    testimonials = Testimonial.objects.filter(is_active=True)[:3]
    return render(
        request,
        "core/home.html",
        {
            "featured_products": featured_products,
            "bundles": bundles,
            "book_count": book_count,
            "testimonials": testimonials,
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


def faq(request):
    faqs = FAQ.objects.filter(is_active=True)
    groups = {}
    for item in faqs:
        groups.setdefault(item.get_group_display(), []).append(item)
    return render(request, "core/faq.html", {"groups": groups})


def legal_page(request, slug):
    try:
        page = LegalPage.objects.get(slug=slug)
    except LegalPage.DoesNotExist:
        raise Http404
    return render(request, "core/legal_page.html", {"page": page})
