from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q

from .forms import TransactionForm
from .models import Transaction

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