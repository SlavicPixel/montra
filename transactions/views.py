from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.cache import cache
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.views.decorators.http import require_POST
from django.urls import reverse, reverse_lazy
from django.http import JsonResponse
from django.utils import timezone as dj_timezone
from django.db.models import Q, Sum, Avg, Count, Max
from django.db.models.functions import Coalesce

from .forms import TransactionForm
from .models import Transaction, MonthlyCategoryReport, YearlyCategoryReport, CustomRangeCategoryReport
from .reports import get_monthly_category_report
from .services.airflow import trigger_airflow_dag
from .services.dashboard import compute_dashboard_context
from .services.dashboard_cache import (
    make_dash_cache_key,
    make_lock_key,
    TTL_SECONDS,
    LOCK_TTL,
)
from montra.exchange_rates import get_latest_rates, get_top_rates, TOP_CURRENCIES

import uuid
from datetime import datetime, timezone, date
from logging import getLogger
from decimal import Decimal

logger = getLogger(__name__)

YEARLY_DAG_ID = "montra_yearly_spark_report"
CUSTOM_RANGE_DAG_ID = "montra_custom_range_spark_report"

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
def yearly_report_view(request):
    try:
        year = int(request.GET.get("year") or dj_timezone.localdate().year)
    except ValueError:
        year = dj_timezone.localdate().year

    qs = (
        YearlyCategoryReport.objects
        .filter(user=request.user, year=year)
        .select_related("category")
        .order_by("category__name")
    )

    rows = []
    computed_at = None

    if qs.exists():
        computed_at = qs.first().computed_at
        rows = [
            {
                "category_name": r.category.name,
                "total_amount": str(r.total_amount),
                "avg_amount": str(r.avg_amount),
                "tx_count": r.tx_count,
            }
            for r in qs
        ]
        source = "precomputed"
        not_ready = False
    else:
        source = "missing"
        not_ready = True

    return render(request, "transactions/yearly_report.html", {
        "year": year,
        "rows": rows,
        "source": source,
        "computed_at": computed_at,
        "not_ready": not_ready,
    })


@require_POST
@login_required
def trigger_yearly_refresh(request):
    try:
        year = int(request.POST.get("year") or dj_timezone.localdate().year)
    except ValueError:
        messages.error(request, "Invalid year.")
        return redirect("yearly_report")

    try:
        trigger_airflow_dag(
            YEARLY_DAG_ID,
            conf={"year": year, "user_id": request.user.id},
        )
        messages.success(
            request,
            f"Yearly report refresh for {year} has been queued."
        )
    except Exception as e:
        messages.error(
            request,
            f"Failed to trigger yearly report: {e}"
        )

    return redirect(f"/reports/yearly/?year={year}")

@login_required
def custom_range_report_view(request):
    today = dj_timezone.localdate()
    default_from = today.replace(day=1)
    default_to = today

    reports_qs = (
        CustomRangeCategoryReport.objects
        .filter(user=request.user)
        .values("request_id", "date_from", "date_to")
        .annotate(
            computed_at=Max("computed_at"),
            rows=Count("id"),
        )
        .order_by("-computed_at", "-date_to", "-date_from")
    )

    reports = []
    for r in reports_qs:
        r["status"] = "ready" if r["rows"] > 0 else "missing"
        reports.append(r)

    return render(request, "transactions/custom_range_index.html", {
        "date_from": default_from,
        "date_to": default_to,
        "reports": reports,
    })

@login_required
def custom_range_report_detail_view(request, request_id):
    qs = (
        CustomRangeCategoryReport.objects
        .filter(user=request.user, request_id=request_id)
        .select_related("category")
        .order_by("category__name")
    )

    rows = []
    computed_at = None
    date_from = None
    date_to = None
    source = "missing"
    not_ready = True

    first = qs.first()
    if first:
        computed_at = first.computed_at
        date_from = first.date_from
        date_to = first.date_to
        rows = [{
            "category_name": r.category.name,
            "total_amount": str(r.total_amount),
            "avg_amount": str(r.avg_amount),
            "tx_count": r.tx_count,
        } for r in qs]
        source = "precomputed"
        not_ready = False

    return render(request, "transactions/custom_range_report.html", {
        "request_id": request_id,
        "date_from": date_from,
        "date_to": date_to,
        "rows": rows,
        "computed_at": computed_at,
        "source": source,
        "not_ready": not_ready,
    })


@require_POST
@login_required
def trigger_custom_range_refresh(request):
    date_from = request.POST.get("date_from")
    date_to = request.POST.get("date_to")

    if not date_from or not date_to:
        messages.error(request, "Please provide date_from and date_to.")
        return redirect("custom_range_report")

    req_id = str(uuid.uuid4())

    trigger_airflow_dag(
        "montra_custom_range_spark_report",
        conf={
            "user_id": request.user.id,
            "request_id": req_id,
            "date_from": date_from,
            "date_to": date_to,
        },
    )

    messages.success(
        request,
        "Report has been queued. Refresh this page in a few seconds and it will appear in the list once ready."
    )

    #return redirect(f"{reverse('custom_range_report')}?request_id={req_id}")
    return redirect("custom_range_report")

@require_POST
@login_required
def delete_custom_range_report(request, request_id):
    deleted, _ = (
        CustomRangeCategoryReport.objects
        .filter(user=request.user, request_id=request_id)
        .delete()
    )

    if deleted:
        messages.success(request, "Custom range report deleted.")
    else:
        messages.info(request, "Report not found (or already deleted).")

    return redirect("custom_range_report")


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