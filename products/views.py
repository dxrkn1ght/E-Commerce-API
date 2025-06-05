from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q
import json
from .models import Product, ProductLike, Review
from .serializers import (
    ProductListSerializer, ProductDetailSerializer,
    ReviewSerializer, CreateReviewSerializer
)
from .filters import ProductFilter
from orders.models import OrderItem


class ProductListView(generics.ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductListSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ['title', 'description']
    ordering_fields = ['price', 'created_at', 'title']
    ordering = ['created_at']

    def get_queryset(self):
        queryset = super().get_queryset()

        # Custom filtering
        category = self.request.query_params.get('category')
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        attributes = self.request.query_params.get('attributes')

        if category:
            queryset = queryset.filter(category_id=category)
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        if attributes:
            try:
                attr_dict = json.loads(attributes)
                for key, value in attr_dict.items():
                    queryset = queryset.filter(attributes__contains={key: value})
            except json.JSONDecodeError:
                pass

        return queryset


class ProductDetailView(generics.RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductDetailSerializer
    permission_classes = [AllowAny]


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def like_product(request, pk):
    try:
        product = Product.objects.get(pk=pk)
        like, created = ProductLike.objects.get_or_create(
            product=product, user=request.user
        )

        if not created:
            like.delete()
            liked = False
        else:
            liked = True

        return Response({
            'success': True,
            'data': {
                'liked': liked,
                'likes_count': product.likes_count
            }
        })
    except Product.DoesNotExist:
        return Response({
            'success': False,
            'error': {'message': 'Product not found'}
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_review(request, pk):
    try:
        product = Product.objects.get(pk=pk)

        # Check if user has ordered this product
        has_ordered = OrderItem.objects.filter(
            order__user=request.user,
            product=product,
            order__status='delivered'
        ).exists()

        if not has_ordered:
            return Response({
                'success': False,
                'error': {'message': 'You can only review products you have purchased'}
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check if user already reviewed
        if Review.objects.filter(product=product, user=request.user).exists():
            return Response({
                'success': False,
                'error': {'message': 'You have already reviewed this product'}
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = CreateReviewSerializer(data=request.data)
        if serializer.is_valid():
            review = serializer.save(product=product, user=request.user)
            return Response({
                'success': True,
                'data': ReviewSerializer(review, context={'request': request}).data
            }, status=status.HTTP_201_CREATED)

        return Response({
            'success': False,
            'error': {'message': 'Invalid data', 'details': serializer.errors}
        }, status=status.HTTP_400_BAD_REQUEST)

    except Product.DoesNotExist:
        return Response({
            'success': False,
            'error': {'message': 'Product not found'}
        }, status=status.HTTP_404_NOT_FOUND)