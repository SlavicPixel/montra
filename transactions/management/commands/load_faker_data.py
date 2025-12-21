import csv
import os
from datetime import datetime

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from transactions.models import UserProfile, Transaction, Category

USERS_CSV = "users.csv"
EXPENSES_DIR = "data"


class Command(BaseCommand):
    def handle(self, *args, **options):
        self.stdout.write("Starting import...")

        # ----------------------
        # USERS
        # ----------------------
        users_to_create = []
        profiles_to_create = []
        user_rows = list(csv.DictReader(open(USERS_CSV, newline="", encoding="utf-8")))

        for row in user_rows:
            if not User.objects.filter(username=row["username"]).exists():
                users_to_create.append(
                    User(
                        username=row["username"],
                        email=row["email"],
                        first_name=row["firstname"],
                        last_name=row["lastname"],
                        password=row["password"],  
                    )
                )

        User.objects.bulk_create(users_to_create, batch_size=1000)

        # Create UserProfiles
        existing_users = User.objects.filter(username__in=[r["username"] for r in user_rows])
        username_to_row = {r["username"]: r for r in user_rows}

        for user in existing_users:
            row = username_to_row[user.username]
            profiles_to_create.append(
                UserProfile(
                    user=user,
                    age=int(row["age"]),
                    address=row["address"]
                )
            )

        UserProfile.objects.bulk_create(profiles_to_create, batch_size=1000)
        self.stdout.write(self.style.SUCCESS(f"{len(users_to_create)} users loaded."))

        # ----------------------
        # TRANSACTIONS
        # ----------------------
        # fetch existing categories once
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
                    if cat_name in existing_categories:
                        category = existing_categories[cat_name]
                    else:
                        category = Category(name=cat_name)
                        existing_categories[cat_name] = category

                    transactions_to_create.append(
                        Transaction(
                            user=user,
                            transaction_type=row["transaction_type"],
                            amount=row["amount"],
                            category=category,
                            description=row.get("description", ""),
                            place=row["place"],
                            date=datetime.strptime(row["date"], "%Y-%m-%d").date(),
                        )
                    )

            # bulk insert categories first (samo nove)
            new_categories = [c for c in existing_categories.values() if c.pk is None]
            if new_categories:
                Category.objects.bulk_create(new_categories, batch_size=1000)
                for c in new_categories:
                    c.refresh_from_db()  # ensure pk is set

            # bulk insert transactions
            Transaction.objects.bulk_create(transactions_to_create, batch_size=5000)
            self.stdout.write(self.style.SUCCESS(
                f"{len(transactions_to_create)} transactions loaded for {username}"
            ))

        self.stdout.write(self.style.SUCCESS("Import finished!"))
