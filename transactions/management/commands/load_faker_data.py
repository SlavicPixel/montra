import csv
import os
from datetime import datetime

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from transactions.models import Transaction, Category  # use new folder
# from users.models import UserProfile  # not needed if you removed profile fields

USERS_CSV = "users.csv"
EXPENSES_DIR = "data"

User = get_user_model()


class Command(BaseCommand):
    help = "Import users and their transactions from CSV files"

    def handle(self, *args, **options):
        self.stdout.write("Starting import...")

        # ----------------------
        # USERS
        # ----------------------
        users_to_create = []
        user_rows = list(csv.DictReader(open(USERS_CSV, newline="", encoding="utf-8")))

        for row in user_rows:
            if not User.objects.filter(username=row["username"]).exists():
                users_to_create.append(
                    User(
                        username=row["username"],
                        email=row["email"],
                        first_name=row["firstname"],
                        last_name=row["lastname"],
                        # password=row["password"],  # optional: set raw passwords here
                    )
                )

        if users_to_create:
            User.objects.bulk_create(users_to_create, batch_size=1000)
        self.stdout.write(self.style.SUCCESS(f"{len(users_to_create)} users loaded."))

        # ----------------------
        # TRANSACTIONS
        # ----------------------
        existing_categories = {c.name: c for c in Category.objects.all()}

        for filename in os.listdir(EXPENSES_DIR):
            if not filename.endswith("_data.csv"):
                continue

            username = filename.replace("_data.csv", "")
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                self.stdout.write(f"User {username} not found, skipping.")
                continue

            file_path = os.path.join(EXPENSES_DIR, filename)
            transactions_to_create = []

            with open(file_path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)

                for row in reader:
                    cat_name = row["category"]
                    category = existing_categories.get(cat_name)
                    if not category:
                        self.stdout.write(f"Category {cat_name} not found, skipping row.")
                        continue

                    transactions_to_create.append(
                        Transaction(
                            user=user,
                            kind=row["kind"],
                            title=row["title"],
                            description=row.get("description", ""),
                            amount=float(row["amount"]),
                            category=category,
                            date=datetime.strptime(row["date"], "%Y-%m-%d").date(),
                        )
                    )

            if transactions_to_create:
                Transaction.objects.bulk_create(transactions_to_create, batch_size=5000)
                self.stdout.write(self.style.SUCCESS(
                    f"{len(transactions_to_create)} transactions loaded for {username}"
                ))

        self.stdout.write(self.style.SUCCESS("Import finished!"))
