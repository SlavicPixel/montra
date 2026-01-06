from django.core.management.base import BaseCommand
from transactions.models import Category

DEFAULT_CATEGORIES = [
    "Bills & Fees",
    "Drinks & Coffee",
    "Food",
    "Groceries",
    "Transport",
    "Salary",
    "Freelance",
    "Investments",
    "Refunds",
    "Unspecified",
]

class Command(BaseCommand):
    help = "Seed default transaction categories (idempotent)."

    def handle(self, *args, **options):
        created = 0
        for name in DEFAULT_CATEGORIES:
            obj, was_created = Category.objects.get_or_create(name=name)
            if was_created:
                created += 1

        total = Category.objects.count()
        self.stdout.write(self.style.SUCCESS(
            f"Categories seeded. Created: {created}. Total categories: {total}."
        ))