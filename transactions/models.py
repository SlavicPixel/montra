from django.db import models

class User(models.Model):
    username = models.CharField(max_length=50, unique=True)
    firstname = models.CharField(max_length=50)
    lastname = models.CharField(max_length=50)
    password = models.CharField(max_length=50)
    age = models.IntegerField()
    address = models.CharField(max_length=200)
    email = models.EmailField()

    def __str__(self):
        return self.username

class Expense(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=10)
    amount = models.FloatField()
    category = models.CharField(max_length=50)
    description = models.CharField(max_length=100)
    place = models.CharField(max_length=100)
    date = models.DateField()

    def __str__(self):
        return f"{self.user.username} - {self.category} - {self.amount}"
