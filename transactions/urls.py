from django.urls import path
from .views import (
    dashboard_view, 
    TransactionListView,
    TransactionCreateView,
    TransactionUpdateView,
    TransactionDeleteView,
)

urlpatterns = [
    path("", dashboard_view, name="dashboard"),
    path("transactions/", TransactionListView.as_view(), name="transaction-list"),
    path("create/", TransactionCreateView.as_view(), name="transaction-create"),
    path("<int:pk>/edit/", TransactionUpdateView.as_view(), name="transaction-edit"),
    path("<int:pk>/delete/", TransactionDeleteView.as_view(), name="transaction-delete"),
]
