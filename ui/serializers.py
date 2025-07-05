from rest_framework import serializers
from .models import Activity, Product, Order, OrderItem
from django.contrib.auth.models import User

class ActivitySerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    
    class Meta:
        model = Activity
        fields = ['id', 'user', 'details', 'timestamp', 'activity_type']
class OrderSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()

    class Meta:
        model = Order
        fields = ['id', 'user', 'total_amount', 'status', 'created_at']

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'image']