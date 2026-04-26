from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    # Public
    path('', views.home, name='home'),
    path('products/', views.product_list, name='product_list'),
    path('products/<int:pk>/', views.product_detail, name='product_detail'),
    path('contact/', views.contact, name='contact'),

    # Cart
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:pk>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:pk>/', views.update_cart, name='update_cart'),
    path('cart/remove/<int:pk>/', views.remove_from_cart, name='remove_from_cart'),

    # Checkout & Orders
    path('checkout/', views.checkout, name='checkout'),
    path('orders/confirmation/<int:pk>/', views.order_confirmation, name='order_confirmation'),
    path('orders/', views.my_orders, name='my_orders'),

    # PDF Receipts
    path('receipt/<int:pk>/pdf/', views.receipt_pdf, name='receipt_pdf'),
    path('receipt/sales/<int:pk>/pdf/', views.sales_receipt_pdf, name='sales_receipt_pdf'),

    # Auth
    path('register/', views.farmer_register, name='register'),
    path('login/', views.farmer_login, name='login'),
    path('logout/', views.farmer_logout, name='logout'),

    # Custom Admin Views
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/orders/', views.admin_orders_list, name='admin_orders_list'),
    path('dashboard/orders/<int:pk>/', views.admin_order_detail, name='admin_order_detail'),
    path('dashboard/sales/', views.admin_sales_list, name='admin_sales_list'),
    path('dashboard/sales/add/', views.admin_sales_add, name='admin_sales_add'),
    path('dashboard/settings/', views.admin_site_settings, name='admin_settings'),

    # Category Management (Admin)
    path('dashboard/categories/', views.admin_categories_list, name='admin_categories_list'),
    path('dashboard/categories/add/', views.admin_categories_add, name='admin_categories_add'),
    path('dashboard/categories/<int:pk>/edit/', views.admin_categories_edit, name='admin_categories_edit'),
    path('dashboard/categories/<int:pk>/delete/', views.admin_categories_delete, name='admin_categories_delete'),

    # Product Management (Admin)
    path('dashboard/products/', views.admin_products_list, name='admin_products_list'),
    path('dashboard/products/add/', views.admin_products_add, name='admin_products_add'),
    path('dashboard/products/<int:pk>/edit/', views.admin_products_edit, name='admin_products_edit'),
    path('dashboard/products/<int:pk>/delete/', views.admin_products_delete, name='admin_products_delete'),
]
