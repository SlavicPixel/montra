from django.urls import path
from .views import (
    dashboard_view, 
    TransactionListView,
    TransactionCreateView,
    TransactionUpdateView,
    TransactionDeleteView,
    monthly_category_report,
    monthly_report_view,
    exchange_rates_api,
    currency_dashboard,
)

urlpatterns = [
    path("", dashboard_view, name="dashboard"),
    path("transactions/", TransactionListView.as_view(), name="transaction-list"),
    path("create/", TransactionCreateView.as_view(), name="transaction-create"),
    path("<int:pk>/edit/", TransactionUpdateView.as_view(), name="transaction-edit"),
    path("<int:pk>/delete/", TransactionDeleteView.as_view(), name="transaction-delete"),
    path("api/reports/monthly", monthly_category_report, name="monthly_category_report"),
    path("reports/monthly/", monthly_report_view, name="monthly_report"),
    path("api/exchange-rates", exchange_rates_api, name="exchange_rates_api"),
    path("tools/currencies/", currency_dashboard, name="currency-dashboard"),
]
