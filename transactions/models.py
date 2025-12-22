from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal

class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ("card", "Card"),
        ("cash", "Cash"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="transactions"
    )
    transaction_type = models.CharField(
        max_length=10,
        choices=TRANSACTION_TYPES
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))]
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="transactions"
    )
    description = models.TextField()  
    place = models.CharField(max_length=100)
    date = models.DateField()

    class Meta:
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["date"]),
        ]
        ordering = ["-date"]

    def __str__(self):
        return f"{self.user.username} | {self.transaction_type} | {self.amount} | {self.category.name}"
