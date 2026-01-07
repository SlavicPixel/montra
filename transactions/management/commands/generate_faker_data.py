from django.core.management.base import BaseCommand
from faker_users import generate_users
from faker_data import generate_user_data


class Command(BaseCommand):
    help = "Generate fake users and transaction data"

    def add_arguments(self, parser):
        parser.add_argument(
            "user_count",
            type=int,
            help="Number of users to generate"
        )
        parser.add_argument(
            "min_entries",
            type=int,
            help="Minimum transactions per user"
        )
        parser.add_argument(
            "max_entries",
            type=int,
            help="Maximum transactions per user"
        )

    def handle(self, *args, **options):
        user_count = options["user_count"]
        min_entries = options["min_entries"]
        max_entries = options["max_entries"]

        self.stdout.write(self.style.SUCCESS("Generating users..."))
        generate_users(user_count)

        self.stdout.write(self.style.SUCCESS("Generating transaction data..."))
        generate_user_data(
            users_file="users.csv",
            output_dir="data",
            users_to_process=user_count,
            min_entries=min_entries,
            max_entries=max_entries,
        )

        self.stdout.write(self.style.SUCCESS("ALL DONE"))
