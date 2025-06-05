from django.urls import path
from .views import ProductReviewCreateView, ProductLikeToggleView

urlpatterns = [

    path('products/<int:id>/reviews/', ProductReviewCreateView.as_view(), name='product-review-create'),


    path('products/<int:id>/like-toggle/', ProductLikeToggleView.as_view(), name='product-like-toggle'),
]
