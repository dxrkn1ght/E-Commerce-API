from django.urls import path
from . import views

urlpatterns = [
    path('cart/', views.cart_view, name='cart'),
    path('cart/<int:product_id>/', views.remove_from_cart, name='remove-from-cart'),
]