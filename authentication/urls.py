from django.urls import path
from . import views

urlpatterns = [
    path('authorize/', views.authorize, name='authorize'),
    path('verify-code/', views.verify_code, name='verify_code'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('token/refresh/', views.refresh_token, name='token_refresh'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/', views.reset_password, name='reset_password'),
]
