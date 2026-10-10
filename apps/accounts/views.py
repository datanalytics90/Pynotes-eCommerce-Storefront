from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import AddressForm, EmailAuthenticationForm, ProfileForm, SignUpForm
from .models import Address


class SignUpView(CreateView):
    form_class = SignUpForm
    template_name = "accounts/signup.html"
    success_url = reverse_lazy("core:home")

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(self.request, "Welcome to PyNotes! Your account has been created.")
        return response


class EmailLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = EmailAuthenticationForm
    redirect_authenticated_user = True


class EmailLogoutView(LogoutView):
    next_page = reverse_lazy("core:home")


@login_required
def dashboard(request):
    orders = request.user.orders.all()[:5]
    addresses = request.user.addresses.all()
    return render(request, "account/dashboard.html", {"orders": orders, "addresses": addresses})


@login_required
def account_details(request):
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Account details updated.")
            return redirect("accounts:account_details")
    else:
        form = ProfileForm(instance=request.user)
    return render(request, "account/account_details.html", {"form": form})


@login_required
def addresses(request):
    return render(request, "account/addresses.html", {"addresses": request.user.addresses.all()})


@login_required
def address_create(request):
    if request.method == "POST":
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            messages.success(request, "Address saved.")
            return redirect("accounts:addresses")
    else:
        form = AddressForm()
    return render(request, "accounts/address_form.html", {"form": form})


@login_required
def address_edit(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    if request.method == "POST":
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            messages.success(request, "Address updated.")
            return redirect("accounts:addresses")
    else:
        form = AddressForm(instance=address)
    return render(request, "accounts/address_form.html", {"form": form, "address": address})


@login_required
def address_delete(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    if request.method == "POST":
        address.delete()
        messages.success(request, "Address removed.")
    return redirect("accounts:addresses")
