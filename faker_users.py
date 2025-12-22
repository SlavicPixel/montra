#!/usr/bin/env python3

import csv
import random
import secrets
import string
from faker import Faker

USER_COUNT = 100
OUTPUT_FILE = "users.csv"

fake = Faker()

def generate_password(length: int = 12) -> str:
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()-_"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def generate_username(first: str, last: str, existing: set) -> str:
    base = f"{first}.{last}".lower().replace(" ", "")
    username = base
    suffix = 1

    while username in existing:
        username = f"{base}{suffix}"
        suffix += 1

    existing.add(username)
    return username


def generate_user(used_usernames: set) -> dict:
    first = fake.first_name()
    last = fake.last_name()

    return {
        "username": generate_username(first, last, used_usernames),
        "firstname": first,
        "lastname": last,
        "password": generate_password(12),
        "age": random.randint(18, 90),
        "address": fake.address().replace("\n", ", "),
        "email": fake.email(),
    }

users = []
used_usernames = set()

for _ in range(USER_COUNT):
    users.append(generate_user(used_usernames))

with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "username",
            "email",
            "password",
            "firstname",
            "lastname",
            "age",
            "address",
        ],
    )
    writer.writeheader()
    for user in users:
        writer.writerow(user)

print("ALL DONE")
print(f"Generated {len(users)} users → {OUTPUT_FILE}\n")

for i, u in enumerate(users[:3], start=1):
    print(
        f"{i}. {u['username']} "
        f"({u['firstname']} {u['lastname']}), "
        f"age={u['age']}, email={u['email']}"
    )
