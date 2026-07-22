from django.urls import path

from .views import MeView, RegisterView

urlpatterns = [
    path('accounts/register/', RegisterView.as_view(), name='register'),
    path('accounts/me/', MeView.as_view(), name='me'),
]
