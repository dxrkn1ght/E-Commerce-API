from django.urls import path
from . import views

urlpatterns = [
    path('authorize/', views.AuthorizeView.as_view(), name='authorize'),
    path('verify/', views.VerifyView.as_view(), name='verify'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('token/refresh/', views.RefreshTokenView.as_view(), name='token-refresh'),
    path('forgot-password/', views.ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/', views.ResetPasswordView.as_view(), name='reset-password'),
]