from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from django.urls import reverse
from django.utils.html import format_html
from django.db.models import Count
from .models import UserProfile, Transaction, Category

admin.site.unregister(User)

@admin.register(User)
class UserAdmin(DefaultUserAdmin):
    list_display = ("username", "first_name", "last_name", "email", "age")
    list_filter = DefaultUserAdmin.list_filter
    search_fields = DefaultUserAdmin.search_fields

    def age(self, obj):
        return obj.profile.age if hasattr(obj, "profile") else None
    age.short_description = "Age"

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "age", "address")
    search_fields = ("user__username", "address")

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("user", "transaction_type", "amount", "category", "date", "place")
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
