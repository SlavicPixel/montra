from django.contrib import admin
from .models import Transaction, Category, MonthlyCategoryReport

admin.site.register(Transaction)
admin.site.register(Category)
admin.site.register(MonthlyCategoryReport)
