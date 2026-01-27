"""
URL configuration for Ganaraj_pro project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from . import views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('menu/', views.menu, name='menu'),
    path('book/', views.book, name='book'),
    path('admin_register/', views.admin_register, name='admin_register'),
    path('user_register/', views.user_register, name='user_register'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('cart/', views.cart, name='cart'),
    path('update_item/', views.update_item, name='update_item'),
    path('orders/', views.orders, name='orders'),
    path("apply-offer/<int:product_id>/<int:discount>/", views.apply_offer, name="apply_offer"),
    path('checkout/', views.checkout, name='checkout'),
    path('payment_success/', views.payment_success, name='payment_success'),
    path('get_location/', views.get_location, name='get_location'),
    path('dashboard/', views.dashboard, name='dashboard'),

] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
