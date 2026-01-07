import csv
import os
import random
from datetime import datetime, timedelta

START_DATE = datetime(2020, 1, 1)
END_DATE = datetime.now()

CATEGORY_MAP = {
    "Bills & Fees": {
        "kind": "expense",
        "amount_range": (20, 400),
        "entries": [
            ("Vodafone", "Mobile plan monthly charge by Vodafone"),
            ("Vodafone", "Vodafone subscription payment"),
            ("Vodafone", "Vodafone service fee this month"),
            ("Comcast", "Internet subscription charged by Comcast"),
            ("Comcast", "Monthly Comcast internet payment"),
            ("Comcast", "Comcast service monthly fee"),
            ("City Water", "Water bill monthly payment to City Water"),
            ("City Water", "City Water monthly service fee"),
            ("Electric Company", "Electricity bill paid to Electric Company"),
            ("Electric Company", "Monthly electricity charge by Electric Company"),
            ("Gas Provider", "Monthly gas bill payment"),
            ("Gas Provider", "Gas provider service fee"),
            ("Internet Provider", "Internet subscription charged by ISP"),
            ("Internet Provider", "Monthly internet provider fee"),
            ("Insurance Inc.", "Insurance premium payment"),
            ("Insurance Inc.", "Annual insurance fee"),
            ("Bank Fee", "Bank account maintenance fee"),
            ("Bank Fee", "Bank monthly service charge"),
            ("Streaming Service", "Streaming service monthly subscription"),
            ("Streaming Service", "Monthly charge for streaming platform"),
        ]
    },

    "Drinks & Coffee": {
        "kind": "expense",
        "amount_range": (2, 10),
        "entries": [
            ("Starbucks", "Morning espresso at Starbucks"),
            ("Starbucks", "Latte from Starbucks"),
            ("Starbucks", "Cappuccino at Starbucks"),
            ("Costa Coffee", "Coffee from Costa Coffee"),
            ("Costa Coffee", "Iced latte at Costa Coffee"),
            ("Costa Coffee", "Morning coffee at Costa Coffee"),
            ("Dunkin' Donuts", "Iced coffee from Dunkin' Donuts"),
            ("Dunkin' Donuts", "Morning espresso at Dunkin' Donuts"),
            ("Dunkin' Donuts", "Coffee break at Dunkin' Donuts"),
            ("Local Cafe", "Afternoon coffee at Local Cafe"),
            ("Local Cafe", "Coffee to go from Local Cafe"),
            ("Cafe Nero", "Morning cappuccino at Cafe Nero"),
            ("Cafe Nero", "Latte for work at Cafe Nero"),
            ("Coffee Bar", "Double espresso at Coffee Bar"),
            ("Coffee Bar", "Specialty coffee at Coffee Bar"),
            ("Espresso House", "Morning espresso at Espresso House"),
            ("Bakery Cafe", "Coffee and pastry at Bakery Cafe"),
            ("Train Station Cafe", "Quick coffee at Train Station Cafe"),
            ("Mall Cafe", "Evening coffee at Mall Cafe"),
            ("Mall Cafe", "Coffee with dessert at Mall Cafe"),
        ]
    },

    "Food": {
        "kind": "expense",
        "amount_range": (8, 120),
        "entries": [
            ("McDonald's", "Lunch at McDonald's"),
            ("McDonald's", "Dinner at McDonald's"),
            ("McDonald's", "Takeaway from McDonald's"),
            ("Burger King", "Lunch at Burger King"),
            ("Burger King", "Dinner at Burger King"),
            ("Burger King", "Takeaway from Burger King"),
            ("KFC", "Chicken meal at KFC"),
            ("KFC", "Family dinner at KFC"),
            ("Subway", "Subway sandwich for lunch"),
            ("Subway", "Dinner from Subway"),
            ("Pizza Hut", "Pizza order from Pizza Hut"),
            ("Pizza Hut", "Family meal at Pizza Hut"),
            ("Domino's", "Pizza delivery from Domino's"),
            ("Domino's", "Lunch from Domino's"),
            ("Local Restaurant", "Dinner at local restaurant"),
            ("Local Restaurant", "Lunch at local restaurant"),
            ("Food Truck", "Lunch from food truck"),
            ("Italian Bistro", "Dinner at Italian bistro"),
            ("Asian Eatery", "Dinner at Asian eatery"),
            ("Asian Eatery", "Lunch at Asian eatery"),
        ]
    },

    "Groceries": {
        "kind": "expense",
        "amount_range": (10, 250),
        "entries": [
            ("Lidl", "Weekly grocery shopping at Lidl"),
            ("Lidl", "Fresh produce from Lidl"),
            ("Kaufland", "Monthly household supplies at Kaufland"),
            ("Kaufland", "Grocery shopping at Kaufland"),
            ("Aldi", "Weekly groceries from Aldi"),
            ("Aldi", "Fresh food shopping at Aldi"),
            ("Spar", "Weekly groceries at Spar"),
            ("Spar", "Vegetables and fruits from Spar"),
            ("Carrefour", "Supermarket shopping at Carrefour"),
            ("Carrefour", "Weekly grocery trip to Carrefour"),
            ("Local Market", "Vegetables from local market"),
            ("Local Market", "Fresh produce at local market"),
            ("Butcher Shop", "Meat purchase at butcher shop"),
            ("Butcher Shop", "Weekly meat supply from butcher"),
            ("Bakery", "Fresh bread at bakery"),
            ("Bakery", "Pastry purchase at bakery"),
            ("Supermarket", "Grocery run at supermarket"),
            ("Supermarket", "Weekly household items at supermarket"),
            ("Organic Store", "Organic food shopping at Organic Store"),
            ("Organic Store", "Weekly organic grocery from Organic Store"),
        ]
    },

    "Transport": {
        "kind": "expense",
        "amount_range": (2, 150),
        "entries": [
            ("Uber", "Uber ride for commute"),
            ("Uber", "Uber ride home"),
            ("Bolt", "Bolt ride for commute"),
            ("Bolt", "Bolt ride home"),
            ("Taxi", "Taxi to office"),
            ("Taxi", "Taxi home from work"),
            ("BP", "Fuel refill at BP"),
            ("BP", "Monthly gas at BP"),
            ("Shell", "Fuel refill at Shell"),
            ("Shell", "Monthly gas at Shell"),
            ("Train Station", "Train ticket for commute"),
            ("Train Station", "Train trip to city"),
            ("Bus Station", "Bus ticket purchase"),
            ("Bus Station", "Monthly bus pass"),
            ("Metro", "Metro monthly pass"),
            ("Metro", "Single metro trip"),
            ("Parking Garage", "Parking fee at garage"),
            ("Parking Garage", "Hourly parking at garage"),
            ("Car Rental", "Car rental for weekend trip"),
            ("Car Rental", "Business car rental"),
        ]
    },

    "Salary": {
        "kind": "income",
        "amount_range": (800, 6000),
        "entries": [
            ("Company Payroll", "Company payroll monthly salary"),
            ("Company Payroll", "Salary credited from Company Payroll"),
            ("Employer", "Salary payment from employer"),
            ("Employer", "Monthly salary deposit from employer"),
            ("Work Contract", "Work contract salary payment"),
            ("Salary Deposit", "Monthly salary deposit"),
            ("Monthly Salary", "Monthly salary credited"),
            ("Bonus Payment", "Bonus payment from employer"),
            ("HR Payroll", "HR payroll deposit"),
            ("Salary Payout", "Salary payout for work done"),
            ("Net Salary", "Net salary credited"),
            ("Wages", "Wages credited for work"),
            ("Company Payroll", "Payroll including bonus"),
            ("Employer", "Employer salary deposit"),
            ("Monthly Salary", "Salary including overtime"),
            ("HR Payroll", "HR salary payment"),
            ("Salary Deposit", "Salary deposit for month"),
            ("Bonus Payment", "Year-end bonus from employer"),
            ("Net Salary", "Net salary for month"),
            ("Wages", "Monthly wages credited"),
        ]
    },

    "Freelance": {
        "kind": "income",
        "amount_range": (100, 8000),
        "entries": [
            ("Client Payment", "Freelance project payment"),
            ("Client Payment", "Payment from client invoice"),
            ("Freelance Project", "Freelance project income"),
            ("Freelance Project", "Payment for freelance work"),
            ("Upwork", "Payment from Upwork project"),
            ("Upwork", "Freelance income via Upwork"),
            ("Fiverr", "Freelance job payment via Fiverr"),
            ("Fiverr", "Payment for Fiverr project"),
            ("Freelance Contract", "Freelance contract payment"),
            ("Freelance Contract", "Contracted freelance work payment"),
            ("Consulting Client", "Consulting project payment"),
            ("Consulting Client", "Payment from consulting client"),
            ("Remote Project", "Remote freelance project income"),
            ("Remote Project", "Payment for remote work"),
            ("Side Project", "Side project payment"),
            ("Side Project", "Freelance side job payment"),
            ("Professional Services", "Payment for professional services"),
            ("Professional Services", "Professional freelance income"),
            ("Freelance Job", "One-time freelance job income"),
            ("Freelance Job", "Payment for freelance job"),
        ]
    },

    "Investments": {
        "kind": "income",
        "amount_range": (50, 15000),
        "entries": [
            ("Robinhood", "Stock dividend payout from Robinhood"),
            ("Robinhood", "Investment gains from Robinhood"),
            ("Coinbase", "Crypto investment gains from Coinbase"),
            ("Coinbase", "Crypto profit from Coinbase"),
            ("Stock Portfolio", "Stock portfolio profit"),
            ("Stock Portfolio", "Capital gains from stocks"),
            ("ETF Dividend", "ETF dividend payout"),
            ("ETF Dividend", "Dividend received from ETF"),
            ("Investment Account", "Profit from investment account"),
            ("Investment Account", "Investment gains"),
            ("Crypto Gains", "Crypto portfolio profit"),
            ("Crypto Gains", "Crypto investment income"),
            ("Brokerage", "Brokerage account gains"),
            ("Brokerage", "Brokerage profit from investments"),
            ("Capital Gains", "Capital gains realized"),
            ("Capital Gains", "Profits from capital investments"),
            ("Dividend Payout", "Dividend income received"),
            ("Dividend Payout", "Dividend payout from portfolio"),
            ("Asset Return", "Asset investment return"),
            ("Asset Return", "Investment asset profit"),
        ]
    },

    "Refunds": {
        "kind": "income",
        "amount_range": (5, 2000),
        "entries": [
            ("Amazon Refund", "Refund for returned Amazon item"),
            ("Amazon Refund", "Amazon purchase refund"),
            ("Zalando Refund", "Refund from Zalando"),
            ("Zalando Refund", "Zalando return refund"),
            ("Store Refund", "Refund from store purchase"),
            ("Store Refund", "Store returned item refund"),
            ("Service Refund", "Service refund received"),
            ("Service Refund", "Refund for cancelled service"),
            ("Subscription Refund", "Subscription refund credited"),
            ("Subscription Refund", "Refund for subscription"),
            ("Payment Reversal", "Payment reversal refund"),
            ("Payment Reversal", "Transaction reversed"),
            ("Returned Item", "Refund for returned item"),
            ("Returned Item", "Item return refund"),
            ("Tax Refund", "Tax refund payment received"),
            ("Tax Refund", "Annual tax refund"),
            ("Overpayment Refund", "Overpayment refund credited"),
            ("Overpayment Refund", "Excess payment refunded"),
            ("Misc Refund", "Miscellaneous refund"),
            ("Misc Refund", "Refund from miscellaneous transaction"),
        ]
    },

    "Unspecified": {
        "kind": "random",
        "amount_range": (1, 3000),
        "entries": [
            ("Unspecified", "Uncategorized transaction"),
            ("Other Transaction", "Unknown payment source"),
            ("Miscellaneous", "Miscellaneous transaction"),
            ("Unknown", "Unidentified charge"),
            ("General Payment", "General account activity"),
            ("Other Income", "Unspecified income transaction"),
            ("Other Expense", "Unspecified expense transaction"),
            ("Uncategorized", "Unclassified account movement"),
            ("Unknown Activity", "Unknown transaction detail"),
            ("Other", "Other miscellaneous payment"),
            ("Unspecified", "Transaction with unknown category"),
            ("Other Transaction", "Generic transaction"),
            ("Miscellaneous", "Other uncategorized transaction"),
            ("Unknown", "Unknown financial movement"),
            ("General Payment", "General financial transaction"),
            ("Other Income", "Income not categorized"),
            ("Other Expense", "Expense not categorized"),
            ("Uncategorized", "Unspecified activity"),
            ("Unknown Activity", "Misc transaction"),
            ("Other", "Other financial operation"),
        ]
    }
}



def random_date():
    delta_days = (END_DATE - START_DATE).days
    return (START_DATE + timedelta(days=random.randint(0, delta_days))).strftime("%Y-%m-%d")

def generate_user_data(
    users_file: str,
    output_dir: str,
    users_to_process: int,
    min_entries: int,
    max_entries: int,
):
    with open(users_file, newline="", encoding="utf-8") as f:
        users = list(csv.DictReader(f))

    selected_users = random.sample(users, users_to_process)
    os.makedirs(output_dir, exist_ok=True)

    for user in selected_users:
        username = user["username"]
        entry_count = random.randint(min_entries, max_entries)

        output_file = os.path.join(output_dir, f"{username}_data.csv")
        print(f"Generating {entry_count} rows for {username}")

        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "username",
                "kind",
                "title",
                "amount",
                "description",
                "date",
                "category"
            ])

            for _ in range(entry_count):
                category = random.choice(list(CATEGORY_MAP.keys()))
                meta = CATEGORY_MAP[category]

                # Pick a random (title, description) tuple
                title, description = random.choice(meta["entries"])

                kind = (
                    random.choice(["expense", "income"])
                    if meta["kind"] == "random"
                    else meta["kind"]
                )

                amount = round(random.uniform(*meta["amount_range"]), 2)

                writer.writerow([
                    username,
                    kind,
                    title,
                    amount,
                    description,
                    random_date(),
                    category
                ])

        print(f"Saved → {output_file}")
