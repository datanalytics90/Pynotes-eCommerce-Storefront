from django import forms

from .models import Review


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["rating", "title", "body"]
        widgets = {
            "rating": forms.Select(choices=[(i, f"{i} star{'s' if i != 1 else ''}") for i in range(5, 0, -1)]),
            "title": forms.TextInput(attrs={"class": "form-input", "placeholder": "Great product!"}),
            "body": forms.Textarea(attrs={"class": "form-input", "rows": 4}),
        }
