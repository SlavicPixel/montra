from decimal import Decimal

from django.db.models import Sum, Value, DecimalField
from django.db.models.functions import Coalesce
from django.utils import timezone as dj_timezone

from transactions.models import Transaction


def compute_dashboard_context(user):
    now = dj_timezone.localtime()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    if month_start.month == 12:
        next_month_start = month_start.replace(year=month_start.year + 1, month=1)
    else:
        next_month_start = month_start.replace(month=month_start.month + 1)

    month_qs = Transaction.objects.filter(
        user=user,
        date__gte=month_start.date(),
        date__lt=next_month_start.date(),
    ).select_related("category")

    zero_decimal = Value(
        Decimal("0.00"),
        output_field=DecimalField(max_digits=10, decimal_places=2),
    )

    income_total = month_qs.filter(kind="income").aggregate(
        total=Coalesce(Sum("amount"), zero_decimal)
    )["total"]

    expense_total = month_qs.filter(kind="expense").aggregate(
        total=Coalesce(Sum("amount"), zero_decimal)
    )["total"]

    net_total = income_total - expense_total

    expense_by_cat = (
        month_qs.filter(kind="expense")
        .values("category__name")
        .annotate(total=Coalesce(Sum("amount"), zero_decimal))
        .order_by("-total")
    )

    income_by_cat = (
        month_qs.filter(kind="income")
        .values("category__name")
        .annotate(total=Coalesce(Sum("amount"), zero_decimal))
        .order_by("-total")
    )

    def top_n_plus_other(rows, n=6, other_label="Other"):
        rows = list(rows)
        top = rows[:n]
        other_sum = sum((r["total"] for r in rows[n:]), start=Decimal("0.00"))
        if other_sum > 0:
            top.append({"category__name": other_label, "total": other_sum})

        labels = [r["category__name"] or "Uncategorized" for r in top]
        values = [float(r["total"]) for r in top]
        return labels, values

    exp_labels, exp_values = top_n_plus_other(expense_by_cat)
    inc_labels, inc_values = top_n_plus_other(income_by_cat)

    recent = (
        Transaction.objects.filter(user=user)
        .select_related("category")
        .order_by("-date", "-id")[:10]
    )

    return {
        "month_label": month_start.strftime("%B %Y"),
        "income_total": income_total,
        "expense_total": expense_total,
        "net_total": net_total,
        "exp_labels": exp_labels,
        "exp_values": exp_values,
        "inc_labels": inc_labels,
        "inc_values": inc_values,
        "recent": recent,
    }
