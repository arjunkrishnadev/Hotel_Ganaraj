from django.contrib import admin
from .models import Category, Product, Table, Booking

# Register your models here.
admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Table)
admin.site.register(Booking)
