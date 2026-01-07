import csv
import secrets
import string
from faker import Faker

fake = Faker()


def generate_password(length: int = 12) -> str:
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()-_"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def generate_username(first: str, last: str, used: set) -> str:
    base = f"{first}.{last}".lower().replace(" ", "")
    username = base
    counter = 1

    while username in used:
        username = f"{base}{counter}"
        counter += 1

    used.add(username)
    return username


def generate_users(user_count: int, output_file: str = "users.csv"):
    used_usernames = set()

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["username", "firstname", "lastname", "email", "password"],
        )
        writer.writeheader()

        for _ in range(user_count):
            first = fake.first_name()
            last = fake.last_name()

            writer.writerow({
                "username": generate_username(first, last, used_usernames),
                "firstname": first,
                "lastname": last,
                "email": fake.email(),
                "password": generate_password(),
            })

    print(f"Generated {user_count} users → {output_file}")
