from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q

from .forms import RegisterForm, LoginForm, TransactionForm
from .models import UserProfile, Transaction


def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data["username"],
                email=form.cleaned_data["email"],
                first_name=form.cleaned_data["first_name"],
                last_name=form.cleaned_data["last_name"],
                password=form.cleaned_data["password1"],
            )

            UserProfile.objects.create(user=user)

            login(request, user)
            return redirect("dashboard")
    else:
        form = RegisterForm()

    return render(request, "auth/register.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect("dashboard")
    else:
        form = LoginForm()

    return render(request, "auth/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("login")


@login_required
def dashboard_view(request):
    return render(request, "dashboard.html")

class MyTransactionsView(LoginRequiredMixin, ListView):
    model = Transaction
    template_name = "transactions/my_transactions.html"
    context_object_name = "transactions"
    paginate_by = 50

    def get_queryset(self):
        qs = (
            Transaction.objects
            .filter(user=self.request.user)
            .select_related("category")
        )

        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(
                Q(category__name__icontains=q) |
                Q(description__icontains=q) |
                Q(place__icontains=q)
            )

        return qs.order_by("-date")

class TransactionCreateView(LoginRequiredMixin, CreateView):
    model = Transaction
    form_class = TransactionForm
    template_name = "transactions/transaction_form.html"
    success_url = reverse_lazy("my-transactions")

    def form_valid(self, form):
        form.instance.user = self.request.user  # VEŽEMO NA USERA
        return super().form_valid(form)


class TransactionUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Transaction
    form_class = TransactionForm
    template_name = "transactions/transaction_form.html"
    success_url = reverse_lazy("my-transactions")

    def test_func(self):
        return self.get_object().user == self.request.user


class TransactionDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Transaction
    template_name = "transactions/transaction_confirm_delete.html"
    success_url = reverse_lazy("my-transactions")

    def test_func(self):
        return self.get_object().user == self.request.user