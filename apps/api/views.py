from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.cart import services as cart_services
from apps.cart.models import Cart
from apps.catalog.models import Category, Product
from apps.orders.models import Order

from .serializers import (
    CartSerializer,
    CategorySerializer,
    OrderSerializer,
    ProductDetailSerializer,
    ProductListSerializer,
    RegisterSerializer,
    UserSerializer,
)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    lookup_field = "slug"
    permission_classes = [permissions.AllowAny]


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.filter(is_active=True).select_related("category").prefetch_related("images")
    lookup_field = "slug"
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["category__slug", "is_featured", "is_bundle"]
    search_fields = ["name", "description"]
    ordering_fields = ["price", "created_at", "name"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ProductDetailSerializer
        return ProductListSerializer


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class CartView(APIView):
    permission_classes = [permissions.AllowAny]

    def _get_cart(self, request):
        if request.user.is_authenticated:
            cart, _ = Cart.objects.get_or_create(user=request.user)
            return cart
        if not request.session.session_key:
            request.session.create()
        cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key, user=None)
        return cart

    def get(self, request):
        cart = self._get_cart(request)
        return Response(CartSerializer(cart).data)

    def post(self, request):
        cart = self._get_cart(request)
        product = Product.objects.filter(pk=request.data.get("product_id"), is_active=True).first()
        if not product:
            return Response({"detail": "Product not found."}, status=status.HTTP_404_NOT_FOUND)
        quantity = int(request.data.get("quantity", 1))
        cart_services.add_item(cart, product, quantity)
        return Response(CartSerializer(cart).data, status=status.HTTP_201_CREATED)

    def delete(self, request):
        cart = self._get_cart(request)
        product = Product.objects.filter(pk=request.data.get("product_id")).first()
        if product:
            cart_services.remove_item(cart, product)
        return Response(CartSerializer(cart).data)


class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related("items")
