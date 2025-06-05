# products/urls.py

from django.urls import path
from .views import (
    ProductListView,
    ProductDetailView,
    like_product,
    create_review,
)

urlpatterns = [
    path('', ProductListView.as_view(), name='product-list'),
    path('<int:pk>/', ProductDetailView.as_view(), name='product-detail'),
    path('<int:pk>/like/', like_product, name='product-like'),
    path('<int:pk>/review/', create_review, name='product-review'),

]