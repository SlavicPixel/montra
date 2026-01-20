from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.db.models import Q, Sum, Avg, Count

from .forms import TransactionForm
from .models import Transaction, MonthlyCategoryReport
from .reports import get_monthly_category_report

@login_required
def dashboard_view(request):
    return render(request, "transactions/dashboard.html")


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

        return qs.order_by("-date")

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

from django.shortcuts import render
from datetime import date
from .reports import get_monthly_category_report

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