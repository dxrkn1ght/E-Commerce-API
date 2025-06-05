from django.urls import path
from .views import OrderListCreateView, OrderDetailView

app_name = 'orders'

urlpatterns = [
    path('', OrderListCreateView.as_view(), name='order-list-create'),
    path('<int:id>/', OrderDetailView.as_view(), name='order-detail'),
]