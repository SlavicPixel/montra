from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.cache import cache
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.utils import timezone as dj_timezone
from django.db.models import Q, Sum, Avg, Count, DecimalField, Value
from django.db.models.functions import Coalesce

from .forms import TransactionForm
from .models import Transaction, MonthlyCategoryReport
from .reports import get_monthly_category_report
from .services.dashboard import compute_dashboard_context
from .services.dashboard_cache import (
    make_dash_cache_key,
    make_lock_key,
    TTL_SECONDS,
    LOCK_TTL,
)
from montra.exchange_rates import get_latest_rates, get_top_rates, TOP_CURRENCIES

from datetime import datetime, timezone, date
from logging import getLogger
from decimal import Decimal

logger = getLogger(__name__)

@login_required
def dashboard_view(request):
    now = dj_timezone.localtime()
    ym = now.strftime("%Y-%m")

    cache_key = make_dash_cache_key(request.user.id, ym)
    cached = cache.get(cache_key)
    if cached:
        return render(request, "transactions/dashboard.html", cached)

    lock_key = make_lock_key(request.user.id, ym)
    got_lock = cache.add(lock_key, "1", timeout=LOCK_TTL)

    if not got_lock:
        context = compute_dashboard_context(request.user)
        return render(request, "transactions/dashboard.html", context)

    try:
        context = compute_dashboard_context(request.user)
        cache.set(cache_key, context, timeout=TTL_SECONDS)
        return render(request, "transactions/dashboard.html", context)
    finally:
        cache.delete(lock_key)


class TransactionListView(LoginRequiredMixin, ListView):
    model = Transaction
    template_name = "transactions/transaction_list.html"
    context_object_name = "transactions"
    paginate_by = 50
    ordering = ["-date", "-id"]

    def get_queryset(self):
        qs = (
            Transaction.objects
            .filter(user=self.request.user)
            .select_related("category")
        )

        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(
                Q(title__icontains=q) |
                Q(description__icontains=q) |
                Q(category__name__icontains=q)
            )

        return qs.order_by("-date", "-id")

class TransactionCreateView(LoginRequiredMixin, CreateView):
    model = Transaction
    form_class = TransactionForm
    template_name = "transactions/transaction_form.html"
    success_url = reverse_lazy("transaction-list")
    extra_context = {"action": "Create"}

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class TransactionUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Transaction
    form_class = TransactionForm
    template_name = "transactions/transaction_form.html"
    success_url = reverse_lazy("transaction-list")
    extra_context = {"action": "Update"}

    def test_func(self):
        return self.get_object().user == self.request.user


class TransactionDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Transaction
    template_name = "transactions/transaction_confirm_delete.html"
    success_url = reverse_lazy("transaction-list")

    def test_func(self):
        return self.get_object().user == self.request.user



@login_required
def monthly_report_view(request):
    today = date.today()
    year = int(request.GET.get("year", today.year))
    month = int(request.GET.get("month", today.month))

    report = get_monthly_category_report(request.user, year, month)

    return render(request, "transactions/monthly_report.html", {
        "year": year,
        "month": month,
        "source": report["source"],
        "computed_at": report["computed_at"],
        "rows": report["rows"],
    })


@login_required
def monthly_category_report(request):
    try:
        year = int(request.GET.get("year"))
        month = int(request.GET.get("month"))
    except (TypeError, ValueError):
        return JsonResponse({"error": "Provide ?year=YYYY&month=MM"}, status=400)

    if month < 1 or month > 12:
        return JsonResponse({"error": "month must be 1-12"}, status=400)

    # FAST PATH: precomputed
    qs = (
        MonthlyCategoryReport.objects
        .filter(user=request.user, year=year, month=month)
        .select_related("category")
        .order_by("category__name")
    )

    if qs.exists():
        data = [
            {
                "category_id": r.category_id,
                "category_name": r.category.name,
                "total_amount": str(r.total_amount),
                "avg_amount": str(r.avg_amount),
                "tx_count": r.tx_count,
                "computed_at": r.computed_at.isoformat(),
            }
            for r in qs
        ]
        return JsonResponse({"source": "precomputed", "year": year, "month": month, "data": data})

    # FALLBACK: compute on the fly
    raw = (
        Transaction.objects
        .filter(user=request.user, kind="expense", date__year=year, date__month=month)
        .values("category_id", "category__name")
        .annotate(
            total_amount=Sum("amount"),
            avg_amount=Avg("amount"),
            tx_count=Count("id"),
        )
        .order_by("category__name")
    )

    data = [
        {
            "category_id": r["category_id"],
            "category_name": r["category__name"],
            "total_amount": str(r["total_amount"] or 0),
            "avg_amount": str(r["avg_amount"] or 0),
            "tx_count": r["tx_count"],
        }
        for r in raw
    ]

    return JsonResponse({"source": "dynamic", "year": year, "month": month, "data": data})

@login_required
def exchange_rates_api(request):
    base = request.GET.get("base", "EUR")
    symbols = request.GET.get("symbols", "USD").split(",")
    data = get_latest_rates(base=base, symbols=symbols)
    return JsonResponse(data)

@login_required
def currency_dashboard(request):
    base = request.GET.get("base", "EUR").upper()
    data = get_top_rates(base=base)  # returns {base, rates, timestamp, source}

    # rates dict -> list for table
    rows = []
    rates = data.get("rates") or {}
    for c in TOP_CURRENCIES:
        if c in rates:
            rows.append({"currency": c, "rate": rates[c]})

    updated_at = None
    if data.get("timestamp"):
        updated_at = datetime.fromtimestamp(
            int(data["timestamp"]),
            tz=timezone.utc,
        )

    logger.info(
    "Monthly report requested",
    extra={"user_id": request.user.id, "report": "monthly_category"}
    )

    return render(request, "transactions/currency_dashboard.html", {
        "base": data.get("base", base),
        "rows": rows,
        "source": data.get("source"),
        "timestamp": data.get("timestamp"),
        "currencies": [data.get("base", base)] + TOP_CURRENCIES,
        "rates_dict": rates,
        "updated_at": updated_at,
    })