from rest_framework import serializers
from .models import Order, OrderItem
from products.serializers import ProductListSerializer


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ['product', 'quantity', 'price', 'subtotal']


class OrderListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['id', 'order_number', 'created_at', 'status', 'total', 'items_count']


class OrderDetailSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'created_at', 'updated_at', 'status',
            'shipping_address', 'notes', 'items', 'subtotal', 'shipping_fee',
            'total', 'tracking_number'
        ]


class OrderCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['shipping_address', 'notes']

    def create(self, validated_data):
        user = self.context['request'].user
        cart = user.cart

        if not cart.items.exists():
            raise serializers.ValidationError("Cart is empty")

        order = Order.objects.create(user=user, **validated_data)

        # Create order items from cart
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                price=cart_item.product.price
            )

        # Calculate totals
        order.subtotal = sum(item.subtotal for item in order.items.all())
        order.total = order.subtotal + order.shipping_fee
        order.save()

        # Clear cart
        cart.items.all().delete()

        return order