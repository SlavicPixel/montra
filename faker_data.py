import csv
import os
import random
from datetime import datetime, timedelta


USERS_FILE = "users.csv"
OUTPUT_DIR = "data"
USERS_TO_PROCESS = 5

MIN_ENTRIES = 10_000
MAX_ENTRIES = 150_000

START_DATE = datetime(2020, 1, 1)
END_DATE = datetime(2025, 12, 31)


CATEGORY_MAP = {
    "Food": {
        "places": [
            "Lidl", "Kaufland", "Spar", "Carrefour", "Aldi",
            "Local Market", "Butcher Shop", "Fish Market",
            "Bakery", "Organic Store", "Supermarket",
            "Restaurant", "Fast Food", "Pizzeria",
            "Burger Place", "Asian Restaurant",
            "Italian Restaurant", "Street Food",
            "Food Truck", "Canteen"
        ],
        "descriptions": [
            "Groceries", "Weekly shopping", "Lunch",
            "Dinner", "Snack", "Breakfast",
            "Family meal", "Takeaway",
            "Fresh vegetables", "Meat purchase",
            "Seafood", "Frozen food",
            "Ready meals", "Bulk food",
            "Organic food", "Late night food",
            "Quick bite", "Home cooking",
            "Meal prep", "Party food"
        ],
        "amount_range": (5, 180)
    },

    "Coffee": {
        "places": [
            "Local Coffee Shop", "Cafe Bar", "Espresso Bar",
            "Coffee Corner", "Coffee House", "Bakery Cafe",
            "Downtown Cafe", "Neighborhood Cafe",
            "Specialty Coffee", "Coffee Truck",
            "Train Station Cafe", "Mall Cafe",
            "Office Cafe", "Bookstore Cafe",
            "Coffee Lounge", "Hipster Cafe",
            "Morning Cafe", "Late Night Cafe",
            "University Cafe", "Work Cafe"
        ],
        "descriptions": [
            "Espresso", "Latte", "Cappuccino",
            "Americano", "Flat white", "Iced coffee",
            "Mocha", "Double espresso",
            "Coffee to go", "Morning coffee",
            "Afternoon coffee", "Quick coffee",
            "Coffee meeting", "Takeaway coffee",
            "Cold brew", "Specialty coffee",
            "Coffee with milk", "Black coffee",
            "Sweet coffee", "Strong coffee"
        ],
        "amount_range": (2, 9)
    },

    "Transport": {
        "places": [
            "Gas Station", "Shell", "BP", "OMV",
            "Taxi", "Uber", "Bolt",
            "Bus Station", "Train Station",
            "Metro", "Parking Garage",
            "Car Wash", "Highway Toll",
            "Ferry", "Airport Transport",
            "Scooter Rental", "Bike Rental",
            "Car Rental", "Public Transport",
            "Fuel Station"
        ],
        "descriptions": [
            "Fuel", "Taxi ride", "Bus ticket",
            "Train ticket", "Metro ticket",
            "Parking fee", "Car wash",
            "Highway toll", "Airport transfer",
            "Ride sharing", "Monthly pass",
            "Single ride", "Vehicle rental",
            "Scooter ride", "Bike ride",
            "Commute", "Long distance travel",
            "Short trip", "Emergency ride",
            "Transport service"
        ],
        "amount_range": (2, 140)
    },

    "Shopping": {
        "places": [
            "Shopping Mall", "Clothing Store",
            "Electronics Store", "Online Shop",
            "Department Store", "Outlet Store",
            "Shoe Store", "Fashion Boutique",
            "Tech Store", "Mobile Shop",
            "Home Store", "Furniture Store",
            "Accessory Shop", "Gift Shop",
            "Bookstore", "Toy Store",
            "Sports Store", "Jewelry Store",
            "Discount Store", "Retail Shop"
        ],
        "descriptions": [
            "Clothes", "Shoes", "Electronics",
            "Accessories", "Gifts", "Household items",
            "New phone", "Computer equipment",
            "Fashion items", "Office supplies",
            "Books", "Toys", "Furniture",
            "Decorations", "Seasonal shopping",
            "Personal items", "Online order",
            "Replacement item", "Impulse buy",
            "Big purchase"
        ],
        "amount_range": (15, 1200)
    },

    "Bills": {
        "places": [
            "Electric Company", "Water Utility",
            "Gas Provider", "Internet Provider",
            "Mobile Operator", "Telecom Provider",
            "Utility Office", "Energy Provider",
            "Waste Management", "City Services",
            "Heating Provider", "TV Provider",
            "Streaming Service", "Cloud Service",
            "Subscription Service", "Hosting Provider",
            "Insurance Office", "Bank Service",
            "Property Management", "Service Provider"
        ],
        "descriptions": [
            "Electricity bill", "Water bill",
            "Gas bill", "Internet bill",
            "Mobile plan", "TV subscription",
            "Streaming subscription", "Cloud service",
            "Insurance payment", "Maintenance fee",
            "Monthly bill", "Service charge",
            "Utility payment", "Annual fee",
            "Contract payment", "Renewal fee",
            "Late fee", "Adjustment charge",
            "Extra service", "Recurring payment"
        ],
        "amount_range": (20, 350)
    },

    "Health": {
        "places": [
            "Pharmacy", "Clinic", "Hospital",
            "Private Doctor", "Dental Clinic",
            "Optician", "Medical Center",
            "Laboratory", "Health Center",
            "Physiotherapy", "Wellness Center",
            "Medical Store", "Emergency Room",
            "Specialist Clinic", "Dermatology Clinic",
            "Orthopedic Clinic", "Eye Clinic",
            "Mental Health Clinic", "Health Shop",
            "Rehab Center"
        ],
        "descriptions": [
            "Medication", "Doctor visit",
            "Dental check", "Medical exam",
            "Prescription drugs", "Vitamins",
            "Medical tests", "Lab analysis",
            "Therapy session", "Health consultation",
            "Emergency visit", "Follow-up visit",
            "Treatment", "Specialist visit",
            "Health supplies", "Medical equipment",
            "Routine check", "Vaccination",
            "Health service", "Medical care"
        ],
        "amount_range": (5, 400)
    },

    "Entertainment": {
        "places": [
            "Cinema", "Theater", "Concert Hall",
            "Music Club", "Streaming Platform",
            "Gaming Store", "Arcade",
            "Bowling Alley", "Escape Room",
            "Museum", "Gallery",
            "Amusement Park", "Festival",
            "Event Venue", "Sports Arena",
            "Night Club", "Bar",
            "Online Platform", "Subscription Service",
            "Leisure Center"
        ],
        "descriptions": [
            "Movie ticket", "Concert ticket",
            "Theater play", "Streaming subscription",
            "Game purchase", "Arcade games",
            "Bowling", "Escape room",
            "Museum entry", "Festival ticket",
            "Event entry", "Sports event",
            "Night out", "Club entry",
            "Entertainment fee", "Leisure activity",
            "Online content", "Digital purchase",
            "Weekend fun", "Evening entertainment"
        ],
        "amount_range": (7, 250)
    }
}


def random_date_2020_2025():
    delta_days = (END_DATE - START_DATE).days
    return (START_DATE + timedelta(days=random.randint(0, delta_days))).strftime("%Y-%m-%d")


with open(USERS_FILE, newline="", encoding="utf-8") as f:
    users = list(csv.DictReader(f))

selected_users = random.sample(users, USERS_TO_PROCESS)
os.makedirs(OUTPUT_DIR, exist_ok=True)

for user in selected_users:
    username = user["username"]
    entry_count = random.randint(MIN_ENTRIES, MAX_ENTRIES)

    output_file = os.path.join(OUTPUT_DIR, f"{username}_data.csv")
    print(f"Generating {entry_count} rows for {username}")

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "username",
            "transaction_type",
            "amount",
            "category",
            "description",
            "place",
            "date"
        ])

        for _ in range(entry_count):
            category = random.choice(list(CATEGORY_MAP.keys()))
            meta = CATEGORY_MAP[category]

            writer.writerow([
                username,
                random.choice(["card", "cash"]),
                round(random.uniform(*meta["amount_range"]), 2),
                category,
                random.choice(meta["descriptions"]),
                random.choice(meta["places"]),
                random_date_2020_2025()
            ])

    print(f"Saved → {output_file}")

print("ALL DONE")
