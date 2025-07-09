from django.shortcuts import render, redirect, get_object_or_404, HttpResponse
from .models import Order, Activity, Product, OrderItem
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils.timezone import now
from datetime import timedelta
from django.db.models import Sum, Count
from .serializers import ActivitySerializer, ProductSerializer, OrderSerializer
from django.db.models import F, Sum, FloatField, ExpressionWrapper
import uuid
import requests



@api_view(['GET'])
def dashboard_summary(request):
    today = now().date()
    yesterday = today - timedelta(days=1)

    # Revenue
    total_revenue = Order.objects.aggregate(total=Sum('total_amount'))['total'] or 0
    revenue_yesterday = Order.objects.filter(created_at__date=yesterday).aggregate(total=Sum('total_amount'))['total'] or 0
    revenue_growth = ((total_revenue - revenue_yesterday) / revenue_yesterday * 100) if revenue_yesterday else 0

    # Sales today
    sales_today = Order.objects.filter(created_at__date=today).aggregate(total=Sum('total_amount'))['total'] or 0
    sales_yesterday = Order.objects.filter(created_at__date=yesterday).aggregate(total=Sum('total_amount'))['total'] or 0
    sales_growth = ((sales_today - sales_yesterday) / sales_yesterday * 100) if sales_yesterday else 0

    # Customers
    customer_count = User.objects.filter(is_staff=False).count()
    customers_today = User.objects.filter(date_joined__date=today, is_staff=False).count()
    customers_yesterday = User.objects.filter(date_joined__date=yesterday, is_staff=False).count()
    customer_growth = ((customers_today - customers_yesterday) / customers_yesterday * 100) if customers_yesterday else 0

    return Response({
        'total_revenue': total_revenue,
        'sales_today': sales_today,
        'customer_count': customer_count,
        'revenue_growth': revenue_growth,
        'sales_growth': sales_growth,
        'customer_growth': customer_growth
    })

@login_required
def admin_dashboard(request):
    recent_orders = Order.objects.select_related('user').prefetch_related('items__product').order_by('-created_at')[:10]
    activities = Activity.objects.select_related('user').order_by('-timestamp')[:10]
    return render(request, 'index.html', {
        'recent_orders': recent_orders,
        'activities': activities
    })
def register_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        username = request.POST.get('username')
        password = request.POST.get('password')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered')
            return render(request, 'register.html')
        
        user = User.objects.create_user(username=username, password=password, email=email, first_name=name)
        login(request, user)
        return redirect('login')
    return render(request, 'register.html')
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            if user.is_staff:
                return redirect('admin_dashboard')
            else:
                return redirect('product_list')
        else:
            # 🔥 Show error on same page instead of redirecting
            return render(request, 'login.html', {'error': 'Invalid username or password'})
    
    return render(request, 'login.html')   
@login_required
def product_list_view(request):
    products = Product.objects.all()
    cart = request.session.get('cart', {})
    cart_count = sum(cart.values())
    return render(request, 'product_list.html', {'products': products, 'cart_count': cart_count})

def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = request.session.get('cart', {})

    if str(product_id) in cart:
        cart[str(product_id)] += 1
    else:
        cart[str(product_id)] = 1
    request.session['cart']= cart
    return redirect('product_list')
from django.contrib.auth.decorators import login_required
from .models import Product

@login_required
def cart_view(request):
    cart = request.session.get('cart', {})  # cart is a dict: {product_id: quantity}
    
    products_in_cart = []
    total_price = 0

    for product_id, quantity in cart.items():
        product = Product.objects.filter(id=product_id).first()
        if product:
            item_total = product.price * quantity
            total_price += item_total
            products_in_cart.append({
                'product': product,
                'quantity': quantity,
                'total': item_total,
            })

    context = {
        'products_in_cart': products_in_cart,
        'total_price': total_price,
    }
    return render(request, 'cart.html', context)
from .models import Order, OrderItem, Activity
from django.utils.timezone import now

@login_required
@login_required
def checkout_view(request):
    if request.method == 'POST':
        cart = request.session.get('cart', {})
        if not cart:
            return redirect('cart')

        total_amount = 0
        for product_id, quantity in cart.items():
            product = Product.objects.get(id=product_id)
            total_amount += product.price * quantity

        transaction_ref = str(uuid.uuid4())  # unique ref

        order = Order.objects.create(
            user=request.user,
            total_amount=total_amount,
            status='pending',
            transaction_ref=transaction_ref
        )

        for product_id, quantity in cart.items():
            product = Product.objects.get(id=product_id)
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity
            )

        Activity.objects.create(
            user=request.user,
            details=f"{request.user.username} started payment worth ₦{total_amount}",
            activity_type="purchase"
        )

        # Keep cart intact until payment is verified
        return render(request, 'paystack_checkout.html', {
            'order': order,
            'paystack_public_key': 'pk_test_5dba66246c3020b4258dbecd34f6693258ff2439'
        })

    return redirect('cart')

@api_view(['GET'])
def recent_activities(request):
    activities = Activity.objects.select_related('user').order_by('-timestamp')[:10]
    serializer = ActivitySerializer(activities, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def sales_today(request):
    today = now().date()
    orders = Order.objects.filter(created_at__date=today).order_by('-created_at')
    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data)
@api_view(['GET'])
def top_selling_products(request):
    product_sales = (
        OrderItem.objects
        .values(
            name=F('product__name'),
            price=F('product__price'),
            image=F('product__image'),
        )
        .annotate(
            total_quantity=Sum('quantity'),
            total_revenue=Sum(
                ExpressionWrapper(F('quantity') * F('product__price'), output_field=FloatField())
            )
        )
        .order_by('-total_quantity')[:5]
    )

    # Fix image to be a full URL
    for item in product_sales:
        if item['image']:
            item['image'] = request.build_absolute_uri(f"/media/{item['image']}")

    return Response(product_sales)

@api_view(['GET'])
def budget_report(request):
    total_sales = Order.objects.aggregate(total=Sum('total_amount'))['total'] or 0
    order_count = Order.objects.count()
    return Response({
        'total_sales': total_sales,
        'total_orders': order_count,

    })

@login_required
def payment_verify(request):
    ref = request.GET.get('ref')
    headers = {"Authorization": "Bearer sk_test_fd756668f87f3bc0b138cd34b76a5d59132da373"}
    url = f"https://api.paystack.co/transaction/verify/{ref}"

    response = requests.get(url, headers=headers).json()

    if response['data']['status'] == 'success':
        order = Order.objects.get(transaction_ref=ref)
        order.status = 'completed'
        order.save()

        request.session['cart'] = {}  # clear cart

        Activity.objects.create(
            user=request.user,
            details=f"{request.user.username} payment verified for ₦{order.total_amount}",
            activity_type="purchase"
        )

        return redirect('thanks')
    else:
        return HttpResponse("Payment failed. Please try again.", status=400)
from django.contrib.auth.decorators import login_required

@login_required
def thanks_view(request):
    return render(request, 'thanks.html')
@login_required
def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})
    if str(product_id) in cart:
        del cart[str(product_id)]
        request.session['cart'] = cart
    return redirect('cart')
@login_required
def remove_one_from_cart(request, product_id):
    cart = request.session.get('cart', {})
    pid = str(product_id)
    if pid in cart:
        if cart[pid] > 1:
            cart[pid] -= 1
        else:
            del cart[pid]
    request.session['cart'] = cart
    return redirect('cart')

@login_required
def remove_all_from_cart(request, product_id):
    cart = request.session.get('cart', {})
    pid = str(product_id)
    if pid in cart:
        del cart[pid]
    request.session['cart'] = cart
    return redirect('cart')

@login_required
def contact_view(request):
    return render(request, 'pages-contact.html')

@login_required
def user_view(request):
    return render(request, 'profile.html')

@login_required
def faq_view(request):
    return render(request, 'faq.html')

@login_required
def error_view(request):
    return render(request, 'error404.html')

@login_required
def blank_view(request):
    return render(request, 'blank.html')