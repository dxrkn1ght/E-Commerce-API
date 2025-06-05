from rest_framework import serializers
from .models import CartItem
from products.serializers import ProductListSerializer

class CartItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    subtotal = serializers.ReadOnlyField()

    class Meta:
        model = CartItem
        fields = ['product', 'quantity', 'subtotal']

class AddToCartSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)

class CartSerializer(serializers.Serializer):
    items = CartItemSerializer(many=True, read_only=True)
    total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    items_count = serializers.IntegerField(read_only=True)