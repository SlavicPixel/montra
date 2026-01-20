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

class MonthlyCategoryReport(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)

    year = models.IntegerField()
    month = models.IntegerField()

    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    avg_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    tx_count = models.IntegerField(default=0)

    computed_at = models.DateTimeField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "category", "year", "month"],
                name="uniq_monthly_report_user_category_period",
            )
        ]
        indexes = [
            models.Index(fields=["user", "year", "month"]),
            models.Index(fields=["category"]),
        ]

    def __str__(self):
        return f"{self.user_id} {self.category_id} {self.year}-{self.month:02d}"
