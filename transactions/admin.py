from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from django.urls import reverse
from django.utils.html import format_html
from django.db.models import Count
from .models import Transaction, Category

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("user", "transaction_type", "amount", "category", "description", "place", "date")
    search_fields = ("user__username", "description", "place")
    list_filter = ("category", "transaction_type", "date")

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "transaction_count_link")
    search_fields = ("name",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.annotate(_transaction_count=Count("transactions"))
        return qs

    def transaction_count_link(self, obj):
        count = getattr(obj, "_transaction_count", obj.transactions.count())
        url = reverse("admin:transactions_transaction_changelist") + f"?category__id__exact={obj.id}"
        return format_html('<a href="{}">{} transactions</a>', url, count)

    transaction_count_link.short_description = "Transactions"
