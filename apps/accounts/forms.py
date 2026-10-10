from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import Address, User


def _bootstrapify(fields):
    for field in fields.values():
        if isinstance(field.widget, forms.CheckboxInput):
            field.widget.attrs.setdefault("class", "form-check-input")
        else:
            field.widget.attrs.setdefault("class", "form-control")


class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)
    newsletter_opt_in = forms.BooleanField(required=False, label="Email me about new products & offers")

    class Meta:
        model = User
        fields = ["email", "first_name", "last_name", "newsletter_opt_in", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _bootstrapify(self.fields)


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(label="Email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _bootstrapify(self.fields)


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "phone_number", "newsletter_opt_in"]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "phone_number": forms.TextInput(attrs={"class": "form-control"}),
            "newsletter_opt_in": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = [
            "address_type", "full_name", "line1", "line2", "city",
            "state", "postal_code", "country", "phone_number", "is_default",
        ]
        widgets = {
            **{
                field: forms.TextInput(attrs={"class": "form-control"})
                for field in ["full_name", "line1", "line2", "city", "state", "postal_code", "country", "phone_number"]
            },
            "address_type": forms.Select(attrs={"class": "form-select"}),
            "is_default": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
