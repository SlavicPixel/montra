from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from decimal import Decimal


class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Transaction(models.Model):
    KIND_CHOICES = [
        ("income", "Income"),
        ("expense", "Expense"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="transactions",
    )
    kind = models.CharField(
    max_length=10,
    choices=KIND_CHOICES,
    default="expense"
    )
    title = models.CharField(max_length=100, default="")
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    description = models.TextField(blank=True, default="")
    date = models.DateField()
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="transactions")

    class Meta:
        ordering = ["-date", "-id"]
        indexes = [
            models.Index(fields=["user", "date"]),
            models.Index(fields=["category"]),
        ]

    def __str__(self):
        return f"{self.user} | {self.kind} | {self.amount} | {self.category}"
