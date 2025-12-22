from django.urls import path
from .views import (
    dashboard_view, 
    MyTransactionsView,
    TransactionCreateView,
    TransactionUpdateView,
    TransactionDeleteView,
)

urlpatterns = [
    path("", dashboard_view, name="dashboard"),
    path("my/", MyTransactionsView.as_view(), name="my-transactions"),
    path("create/", TransactionCreateView.as_view(), name="transaction-create"),
    path("<int:pk>/edit/", TransactionUpdateView.as_view(), name="transaction-edit"),
    path("<int:pk>/delete/", TransactionDeleteView.as_view(), name="transaction-delete"),
]
