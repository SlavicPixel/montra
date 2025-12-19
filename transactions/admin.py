from django.contrib import admin
from .models import User, Expense

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("username", "firstname", "lastname", "email", "age")

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ("user", "transaction_type", "amount", "category", "date", "place")
    list_filter = ("category", "transaction_type", "date")
