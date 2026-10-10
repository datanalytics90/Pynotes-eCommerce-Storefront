from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ReviewForm
from .models import Category, Product


def product_list(request):
    products = Product.objects.filter(is_active=True).select_related("category")

    query = request.GET.get("q", "").strip()
    if query:
        products = products.filter(Q(name__icontains=query) | Q(description__icontains=query))

    category_slug = request.GET.get("category")
    if category_slug:
        products = products.filter(category__slug=category_slug)

    sort = request.GET.get("sort", "newest")
    sort_map = {
        "newest": "-created_at",
        "price_asc": "price",
        "price_desc": "-price",
        "name": "name",
    }
    products = products.order_by(sort_map.get(sort, "-created_at"))

    paginator = Paginator(products, 12)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "catalog/product_list.html",
        {
            "page_obj": page_obj,
            "categories": Category.objects.filter(is_active=True),
            "query": query,
            "current_category": category_slug,
            "sort": sort,
        },
    )


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug, is_active=True)
    products = Product.objects.filter(category=category, is_active=True).order_by("-created_at")
    paginator = Paginator(products, 12)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(
        request,
        "catalog/category_detail.html",
        {"category": category, "page_obj": page_obj, "categories": Category.objects.filter(is_active=True)},
    )


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.select_related("category").prefetch_related("images", "reviews__user"),
        slug=slug,
        is_active=True,
    )
    related_products = (
        Product.objects.filter(category=product.category, is_active=True).exclude(pk=product.pk)[:4]
    )
    review_form = ReviewForm()
    user_has_reviewed = (
        request.user.is_authenticated and product.reviews.filter(user=request.user).exists()
    )
    return render(
        request,
        "catalog/product_detail.html",
        {
            "product": product,
            "related_products": related_products,
            "review_form": review_form,
            "user_has_reviewed": user_has_reviewed,
        },
    )


@login_required
def submit_review(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    if product.reviews.filter(user=request.user).exists():
        messages.warning(request, "You have already reviewed this product.")
        return redirect("catalog:product_detail", slug=slug)

    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()
            messages.success(request, "Thanks for your review!")
    return redirect("catalog:product_detail", slug=slug)
