from django import forms

from .models import IssueReport, Order


class CheckoutForm(forms.Form):
    first_name = forms.CharField(max_length=100)
    last_name = forms.CharField(max_length=100)
    email = forms.EmailField()
    phone_number = forms.CharField(max_length=20, label="Phone")
    line1 = forms.CharField(max_length=255, label="Address")
    line2 = forms.CharField(max_length=255, required=False, label="Address line 2")
    city = forms.CharField(max_length=100)
    state = forms.CharField(max_length=100)
    postal_code = forms.CharField(max_length=20, label="PIN code")
    country = forms.CharField(max_length=100, initial="India", widget=forms.HiddenInput)
    payment_method = forms.ChoiceField(
        choices=Order.PaymentMethod.choices, initial=Order.PaymentMethod.PREPAID, widget=forms.RadioSelect
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name != "payment_method":
                field.widget.attrs.setdefault("class", "form-control")

    def shipping_data(self):
        data = self.cleaned_data
        return {
            "full_name": f"{data['first_name']} {data['last_name']}".strip(),
            "line1": data["line1"],
            "line2": data.get("line2", ""),
            "city": data["city"],
            "state": data["state"],
            "postal_code": data["postal_code"],
            "country": data.get("country") or "India",
            "phone_number": data["phone_number"],
        }


class OrderTrackingForm(forms.Form):
    order_number = forms.CharField(max_length=40, label="Order number")
    email = forms.EmailField(label="Email used at checkout")


class IssueReportForm(forms.ModelForm):
    class Meta:
        model = IssueReport
        fields = ["description", "photo"]
        widgets = {
            "description": forms.Textarea(
                attrs={"class": "form-control", "rows": 5, "placeholder": "Describe the damaged/wrong item..."}
            ),
            "photo": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }
