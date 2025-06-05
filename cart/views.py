from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Sum, F
from .models import CartItem
from products.models import Product
from .serializers import AddToCartSerializer, CartItemSerializer


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def cart_view(request):
    if request.method == 'GET':
        cart_items = CartItem.objects.filter(user=request.user).select_related('product')
        total = sum(item.subtotal for item in cart_items)

        return Response({
            'success': True,
            'data': {
                'items': CartItemSerializer(cart_items, many=True, context={'request': request}).data,
                'total': total,
                'items_count': cart_items.count()
            }
        })

    elif request.method == 'POST':
        serializer = AddToCartSerializer(data=request.data)
        if serializer.is_valid():
            product_id = serializer.validated_data['product_id']
            quantity = serializer.validated_data['quantity']

            try:
                product = Product.objects.get(id=product_id, in_stock=True)
            except Product.DoesNotExist:
                return Response({
                    'success': False,
                    'error': {'message': 'Product not found or out of stock'}
                }, status=status.HTTP_404_NOT_FOUND)

            cart_item, created = CartItem.objects.get_or_create(
                user=request.user,
                product=product,
                defaults={'quantity': quantity}
            )

            if not created:
                cart_item.quantity += quantity
                cart_item.save()

            # Return updated cart
            cart_items = CartItem.objects.filter(user=request.user).select_related('product')
            total = sum(item.subtotal for item in cart_items)

            return Response({
                'success': True,
                'data': {
                    'items': CartItemSerializer(cart_items, many=True, context={'request': request}).data,
                    'total': total,
                    'items_count': cart_items.count()
                }
            })

        return Response({
            'success': False,
            'error': {'message': 'Invalid data', 'details': serializer.errors}
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_from_cart(request, product_id):
    try:
        cart_item = CartItem.objects.get(user=request.user, product_id=product_id)
        cart_item.delete()

        # Return updated cart
        cart_items = CartItem.objects.filter(user=request.user).select_related('product')
        total = sum(item.subtotal for item in cart_items)

        return Response({
            'success': True,
            'data': {
                'items': CartItemSerializer(cart_items, many=True, context={'request': request}).data,
                'total': total,
                'items_count': cart_items.count()
            }
        })

    except CartItem.DoesNotExist:
        return Response({
            'success': False,
            'error': {'message': 'Product not found in cart'}
        }, status=status.HTTP_404_NOT_FOUND)