# montra
Simple web finance application

## Importing Categories

Before loading users and transactions, you need to populate the categories in the database.  
Run the following management command:

```bash
python manage.py seed_categories
```
This will create all necessary categories for transactions.

## Generating and Loading Faker Users & Transactions

Use the `generate_faker_data` management command to quickly create test users and transactions.

### Generate Users and Transactions
```bash
python manage.py generate_faker_data <user_count> <min_entries> <max_entries>
```

Example:
```bash
python manage.py generate_faker_data 50 10000 50000
```

## Load Data into Database

After generating CSVs, load them with:
```bash
python manage.py load_faker_data
```
This imports users from `users.csv` and transactions from the `data/` folder, linking them to the correct categories.  

**Note:** Ensure categories exist in the database before loading transactions.

