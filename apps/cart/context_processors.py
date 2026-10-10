def cart(request):
    return {"cart": getattr(request, "cart", None)}
