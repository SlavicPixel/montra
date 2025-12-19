import csv
import os
from datetime import datetime
from django.core.management.base import BaseCommand
from transactions.models import User, Expense

USERS_CSV = "users.csv"        
EXPENSES_DIR = "data"          

class Command(BaseCommand):
    help = "Import users and expenses from CSV files"

    def handle(self, *args, **options):
        # --- Import Users ---
        if not os.path.exists(USERS_CSV):
            self.stdout.write(self.style.ERROR(f"{USERS_CSV} not found"))
            return

        with open(USERS_CSV, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                User.objects.update_or_create(
                    username=row['username'],
                    defaults={
                        'firstname': row['firstname'],
                        'lastname': row['lastname'],
                        'password': row['password'],
                        'age': int(row['age']),
                        'address': row['address'],
                        'email': row['email'],
                    }
                )
        self.stdout.write(self.style.SUCCESS("Users imported successfully."))

        # --- Import Expenses ---
        if not os.path.exists(EXPENSES_DIR):
            self.stdout.write(self.style.WARNING(f"No expenses folder found at {EXPENSES_DIR}"))
            return

        for file_name in os.listdir(EXPENSES_DIR):
            if not file_name.endswith("_data.csv"):
                continue

            username = file_name.replace("_data.csv", "")
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"User {username} not found, skipping expenses."))
                continue

            file_path = os.path.join(EXPENSES_DIR, file_name)
            with open(file_path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                bulk_expenses = []
                for row in reader:
                    expense = Expense(
                        user=user,
                        transaction_type=row['transaction_type'],
                        amount=float(row['amount']),
                        category=row['category'],
                        description=row['description'],
                        place=row['place'],
                        date=datetime.strptime(row['date'], "%Y-%m-%d").date()
                    )
                    bulk_expenses.append(expense)

                Expense.objects.bulk_create(bulk_expenses, batch_size=5000)
                self.stdout.write(self.style.SUCCESS(f"{len(bulk_expenses)} expenses imported for {username}"))
