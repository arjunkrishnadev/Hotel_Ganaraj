from django.db import models
from django.db import models
from django.utils.text import slugify
# Create your models here.



class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    image = models.ImageField(upload_to='categories/')
    description = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='products/')
    is_available = models.BooleanField(default=True)
    OFFER_TAGS = [
        ('new', 'New'),
        ('bestseller', 'Bestseller'),
        ('spicy', 'Spicy'),
        ('discount', 'Discount'),
        ('limited', 'Limited'),
    ]

    offer_tag = models.CharField(max_length=20, choices=OFFER_TAGS, blank=True, null=True)
    offer_text = models.CharField(max_length=50, blank=True, null=True)  # Optional custom text like "20% OFF"

    # Homepage Offer Fields
    is_homepage_offer = models.BooleanField(default=False, verbose_name="Show in Homepage Offer Section")
    offer_title = models.CharField(max_length=100, blank=True, null=True, help_text="e.g. Tasty Thursdays")
    offer_discount_percentage = models.IntegerField(default=0, help_text="Percentage discount e.g. 20")

    def __str__(self):
        return self.name

class Table(models.Model):
    table_number = models.IntegerField(unique=True)
    capacity = models.IntegerField()

    def __str__(self):
        return f"Table {self.table_number} (Capacity: {self.capacity})"

class Booking(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Cancelled', 'Cancelled'),
    ]

    customer_name = models.CharField(max_length=100)
    customer_phone = models.CharField(max_length=15)
    table = models.ForeignKey(Table, on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateField()
    time = models.TimeField()
    guests = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')

    def __str__(self):
        return f"Booking for {self.customer_name} on {self.date} at {self.time}"
