from django import forms
from django.utils import timezone
from .models import Transaction

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = [
            "kind",
            "title",
            "amount",
            "category",
            "description",
            "date",
        ]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "title": forms.TextInput(attrs={"placeholder": "e.g. Grocery shopping"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk and not self.initial.get("date"):
            self.initial["date"] = timezone.localdate()

