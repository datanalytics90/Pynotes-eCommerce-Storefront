from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import Address, User


class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)
    newsletter_opt_in = forms.BooleanField(required=False, label="Email me about new products & offers")

    class Meta:
        model = User
        fields = ["email", "first_name", "last_name", "newsletter_opt_in", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault(
                "class", "w-full rounded-lg border border-slate-300 px-4 py-2.5 focus:border-brand-500 "
                "focus:ring-brand-500 text-sm"
            )


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(label="Email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault(
                "class", "w-full rounded-lg border border-slate-300 px-4 py-2.5 focus:border-brand-500 "
                "focus:ring-brand-500 text-sm"
            )


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "phone_number", "newsletter_opt_in"]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-input"}),
            "last_name": forms.TextInput(attrs={"class": "form-input"}),
            "phone_number": forms.TextInput(attrs={"class": "form-input"}),
        }


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = [
            "address_type", "full_name", "line1", "line2", "city",
            "state", "postal_code", "country", "phone_number", "is_default",
        ]
        widgets = {
            field: forms.TextInput(attrs={"class": "form-input"})
            for field in ["full_name", "line1", "line2", "city", "state", "postal_code", "country", "phone_number"]
        }
