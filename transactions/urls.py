from django.urls import path
from .views import (
    register_view,
    login_view,
    logout_view,
    dashboard_view, 
    MyTransactionsView,
    TransactionCreateView,
    TransactionUpdateView,
    TransactionDeleteView,
)

urlpatterns = [
    path("register/", register_view, name="register"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("", dashboard_view, name="dashboard"),
    path("my/", MyTransactionsView.as_view(), name="my-transactions"),
    path("create/", TransactionCreateView.as_view(), name="transaction-create"),
    path("<int:pk>/edit/", TransactionUpdateView.as_view(), name="transaction-edit"),
    path("<int:pk>/delete/", TransactionDeleteView.as_view(), name="transaction-delete"),
]
