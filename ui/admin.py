from django.contrib import admin
from .models import Product, Order, OrderItem, Activity

admin.site.register(Product)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Activity)