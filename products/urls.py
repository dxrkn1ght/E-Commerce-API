from django.urls import path
from . import views

urlpatterns = [
    path('products/', views.ProductListView.as_view(), name='product-list'),
    path('products/<int:pk>/', views.ProductDetailView.as_view(), name='product-detail'),
    path('products/<int:pk>/like/', views.like_product, name='product-like'),
    path('products/<int:pk>/review/', views.create_review, name='product-review'),
]