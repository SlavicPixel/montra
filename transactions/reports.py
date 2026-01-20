from django.db.models import Sum, Avg, Count
from django.utils import timezone
from .models import MonthlyCategoryReport, Transaction

def get_monthly_category_report(user, year: int, month: int):
    # 1) pokušaj precomputed
    qs = (
        MonthlyCategoryReport.objects
        .filter(user=user, year=year, month=month)
        .select_related("category")
        .order_by("category__name")
    )

    if qs.exists():
        return {
            "source": "precomputed",
            "computed_at": qs.first().computed_at,
            "rows": [
                {
                    "category_id": r.category_id,
                    "category_name": r.category.name,
                    "total_amount": r.total_amount,
                    "avg_amount": r.avg_amount,
                    "tx_count": r.tx_count,
                }
                for r in qs
            ],
        }

    # 2) fallback: izračunaj iz Transaction
    raw = (
        Transaction.objects
        .filter(user=user, kind="expense", date__year=year, date__month=month)
        .values("category_id", "category__name")
        .annotate(
            total_amount=Sum("amount"),
            avg_amount=Avg("amount"),
            tx_count=Count("id"),
        )
        .order_by("category__name")
    )

    return {
        "source": "dynamic",
        "computed_at": timezone.now(),
        "rows": [
            {
                "category_id": r["category_id"],
                "category_name": r["category__name"],
                "total_amount": r["total_amount"] or 0,
                "avg_amount": r["avg_amount"] or 0,
                "tx_count": r["tx_count"],
            }
            for r in raw
        ],
    }
