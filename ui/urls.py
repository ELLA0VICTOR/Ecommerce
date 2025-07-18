from django.urls import path
from . import views

urlpatterns = [
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('products/', views.product_list_view, name='product_list'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart_view, name='cart'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('remove-one/<int:product_id>/', views.remove_one_from_cart, name='remove_one_from_cart'),
    path('remove-all/<int:product_id>/', views.remove_all_from_cart, name='remove_all_from_cart'),
    path('contact/', views.contact_view, name='contact'),
    path('profile/', views.user_view, name='user'),
    path('faq/', views.faq_view, name='faq'),
    path('error_404/', views.error_view, name='error'),
    path('blank/', views.blank_view, name='blank'),

   

    
    # ✅ New payment verify URL
    path('payment-verify/', views.payment_verify, name='payment_verify'),
    path('thanks/', views.thanks_view, name='thanks'),


    # ✅ Existing API endpoints
    path('api/activities/', views.recent_activities, name='api_activities'),
    path('api/sales-today/', views.sales_today, name='api_sales_today'),
    path('api/top-products/', views.top_selling_products, name='api_top_products'),
    path('api/budget-report/', views.budget_report, name='api_budget_report'),
    path('api/summary/', views.dashboard_summary, name='api_summary'),
]
