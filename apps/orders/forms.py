from django import forms


class CheckoutForm(forms.Form):
    email = forms.EmailField()
    full_name = forms.CharField(max_length=150)
    line1 = forms.CharField(max_length=255, label="Address line 1")
    line2 = forms.CharField(max_length=255, required=False, label="Address line 2")
    city = forms.CharField(max_length=100)
    state = forms.CharField(max_length=100)
    postal_code = forms.CharField(max_length=20)
    country = forms.CharField(max_length=100, initial="United States")
    phone_number = forms.CharField(max_length=20, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault(
                "class",
                "w-full rounded-lg border border-slate-300 px-4 py-2.5 focus:border-brand-500 "
                "focus:ring-brand-500 text-sm",
            )
