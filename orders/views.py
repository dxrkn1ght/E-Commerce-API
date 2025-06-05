from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from .models import Order
from .serializers import OrderListSerializer, OrderDetailSerializer, OrderCreateSerializer
from .filters import OrderFilter
from .pagination import OrderPagination


class OrderListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = OrderFilter
    pagination_class = OrderPagination

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return OrderCreateSerializer
        return OrderListSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()

        return Response({
            'success': True,
            'data': OrderDetailSerializer(order).data
        }, status=status.HTTP_201_CREATED)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated_response = self.get_paginated_response(serializer.data)
            return Response({
                'success': True,
                'data': paginated_response.data['results'],
                'meta': {
                    'pagination': {
                        'total': paginated_response.data['count'],
                        'count': len(paginated_response.data['results']),
                        'per_page': self.pagination_class.page_size,
                        'current_page': int(request.GET.get('page', 1)),
                        'total_pages': paginated_response.data['count'] // self.pagination_class.page_size + 1,
                        'links': {
                            'next': paginated_response.data['next'],
                            'prev': paginated_response.data['previous']
                        }
                    }
                }
            })

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })


class OrderDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderDetailSerializer

    def get_object(self):
        order = get_object_or_404(Order, id=self.kwargs['id'])
        if order.user != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Not authorized to view this order")
        return order

    def retrieve(self, request, *args, **kwargs):
        order = self.get_object()
        serializer = self.get_serializer(order)
        return Response({
            'success': True,
            'data': serializer.data
        })