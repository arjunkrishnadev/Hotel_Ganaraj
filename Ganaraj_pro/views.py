from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
import json
import urllib.request
from decimal import Decimal
from django.db.models import Sum, Count
from django.db.models.functions import TruncDate
import datetime
from admin_app.models import Category, Product
from user_app.models import Customer, Order, OrderItem
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib import messages
import razorpay
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID,
                                        settings.RAZORPAY_KEY_SECRET))


@login_required
def checkout(request):
    try:
        customer = request.user.customer
    except Customer.DoesNotExist:
        return redirect('login')

    order, created = Order.objects.get_or_create(customer=customer, complete=False)
    items = order.orderitem_set.all()

    # Read offer info from session
    offer_product_id = request.session.get('offer_product_id')
    offer_price_str = request.session.get('offer_price')

    if offer_product_id and offer_price_str:
        offer_price = Decimal(offer_price_str)
        for item in items:
            if item.product.id == offer_product_id:
                item.discounted_price = offer_price
                item.discounted_total = (offer_price * item.quantity).quantize(Decimal('0.01'))
            else:
                item.discounted_price = None

    # Calculate final cart total
    cart_total = Decimal('0.00')
    for item in items:
        if getattr(item, 'discounted_price', None):
            cart_total += item.discounted_total
        else:
            cart_total += Decimal(item.get_total)

    if cart_total == 0:
        messages.info(request, "Your cart is empty")
        return redirect('cart')

    # Create Razorpay Order
    amount_in_paise = int(cart_total * 100)
    currency = 'INR'
    
    razorpay_order = razorpay_client.order.create(dict(
        amount=amount_in_paise,
        currency=currency,
        payment_capture='1'
    ))

    razorpay_order_id = razorpay_order['id']
    order.razorpay_order_id = razorpay_order_id
    order.save()

    context = {
        'items': items,
        'order': order,
        'cart_total': cart_total,
        'razorpay_order_id': razorpay_order_id,
        'razorpay_merchant_key': settings.RAZORPAY_KEY_ID,
        'razorpay_amount': amount_in_paise,
        'currency': currency,
        'callback_url': '/payment_success/'
    }
    
    return render(request, 'checkout.html', context)

@csrf_exempt
def payment_success(request):
    if request.method == "POST":
        try:
            payment_id = request.POST.get('razorpay_payment_id', '')
            razorpay_order_id = request.POST.get('razorpay_order_id', '')
            signature = request.POST.get('razorpay_signature', '')
            
            params_dict = {
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            }

            # Verify signature
            result = razorpay_client.utility.verify_payment_signature(params_dict)

            if result is not None:
                # Payment Successful
                try:
                    order = Order.objects.get(razorpay_order_id=razorpay_order_id)
                    order.complete = True
                    order.razorpay_payment_id = payment_id
                    order.save()
                    
                    # Clear offer session
                    if 'offer_product_id' in request.session:
                        del request.session['offer_product_id']
                    if 'offer_price' in request.session:
                        del request.session['offer_price']
                    if 'offer_discount' in request.session:
                        del request.session['offer_discount']

                    messages.success(request, "Payment Successful! Your order has been placed.")
                    return redirect('orders')
                except Order.DoesNotExist:
                    messages.error(request, "Order not found.")
                    return redirect('cart')
            else:
                messages.error(request, "Payment Verification Failed.")
                return redirect('cart')
                
        except Exception as e:
            messages.error(request, f"Error processing payment: {str(e)}")
            return redirect('cart')
            
    return redirect('cart')



def index(request):
    offer_products = Product.objects.filter(is_homepage_offer=True)
    return render(request, 'index.html', {'offer_products': offer_products})


def about(request):
    return render(request, 'about.html')


def menu(request):
    categories = Category.objects.all()
    products = Product.objects.all()

    # Filter by Category
    category_slug = request.GET.get('category')
    if category_slug and category_slug != 'all':
        products = products.filter(category__slug=category_slug)

    # Filter by Search Query
    query = request.GET.get('q')
    if query:
        products = products.filter(name__icontains=query)

    context = {
        'categories': categories, 
        'products': products, 
        'body_class': 'sub_page',
        'active_category': category_slug or 'all',
        'search_query': query or ''
    }
    return render(request, 'menu.html', context)


@login_required
def dashboard(request):
    # Ensure only staff/admin can access
    if not request.user.is_staff:
        messages.error(request, "Access Denied. Admin only.")
        return redirect('index')

    # 1. Total Stats
    total_orders = Order.objects.filter(complete=True).count()
    
    # Calculate revenue manually to be safe with model properties if needed, 
    # but efficient query is best. 
    # Since 'get_cart_total' is a property, we might need to rely on summing OrderItems if we want pure SQL,
    # or just iter over completed orders (slow for huge data, fine for now).
    
    completed_orders = Order.objects.filter(complete=True)
    total_revenue = sum([order.get_cart_total for order in completed_orders])
    
    pending_orders = Order.objects.filter(complete=True, date_ordered__gte=datetime.date.today()).count() # Using today for "active/recent" proxy or just count all

    # 2. Recent Orders
    recent_orders = Order.objects.filter(complete=True).order_by('-date_ordered')[:5]

    # 3. Chart Data (Last 7 Days)
    # Group by date
    today = datetime.date.today()
    last_7_days = today - datetime.timedelta(days=7)
    
    # This queries aggregations per day. 
    # Note: SQLite/MySQL date truncation syntax varies, Django handles mostly.
    daily_sales = Order.objects.filter(complete=True, date_ordered__gte=last_7_days)\
        .annotate(date=TruncDate('date_ordered'))\
        .values('date')\
        .annotate(count=Count('id'))\
        .order_by('date')
        
    # Format for Chart.js
    dates = []
    counts = []
    
    for entry in daily_sales:
        dates.append(entry['date'].strftime('%Y-%m-%d'))
        counts.append(entry['count'])

    context = {
        'total_revenue': total_revenue,
        'pending_orders': pending_orders,
        'recent_orders': recent_orders,
        'body_class': 'sub_page',
        'chart_dates': json.dumps(dates),
        'chart_dates': json.dumps(dates),
        'chart_counts': json.dumps(counts),
    }
    return render(request, 'dashboard.html', context)


def book(request):
    return render(request, 'book.html')


def admin_register(request):
    return render(request, 'admin_register.html')


def user_register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']

        if User.objects.filter(username=username).exists():
            messages.info(request, 'Username taken')
            return redirect('user_register')

        if User.objects.filter(email=email).exists():
            messages.info(request, 'Email taken')
            return redirect('user_register')

        user = User.objects.create_user(username=username, email=email, password=password)
        user.save()

        Customer.objects.create(user=user, name=username, email=email)

        auth_login(request, user)
        return redirect('index')

    return render(request, 'user_register.html')


def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            auth_login(request, user)
            return redirect('index')
        else:
            messages.info(request, 'Invalid credentials')
            return redirect('login')

    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    return redirect('index')


@login_required
def update_item(request):
    try:
        data = json.loads(request.body)
        product_id = data['productId']
        action = data['action']
    except (KeyError, json.JSONDecodeError):
        return JsonResponse({'error': 'Invalid data'}, status=400)

    try:
        customer = request.user.customer
    except Customer.DoesNotExist:
        # Create customer if missing
        customer = Customer.objects.create(
            user=request.user,
            name=request.user.username,
            email=request.user.email
        )

    product = get_object_or_404(Product, id=product_id)

    order, created = Order.objects.get_or_create(customer=customer, complete=False)
    orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)

    if action == 'add':
        orderItem.quantity += 1
    elif action == 'remove':
        orderItem.quantity -= 1

    if orderItem.quantity <= 0:
        orderItem.delete()
    else:
        orderItem.save()

    return JsonResponse('Item was added', safe=False)


@login_required
def orders(request):
    try:
        customer = request.user.customer
        orders = Order.objects.filter(customer=customer).order_by('-date_ordered')
    except Customer.DoesNotExist:
        orders = []

    return render(request, 'order.html', {'orders': orders})


@login_required
def apply_offer(request, product_id, discount):

    product = get_object_or_404(Product, id=product_id)

    # Ensure Decimal math
    price = product.price
    discount_decimal = Decimal(discount) / Decimal(100)
    final_price = (price - (price * discount_decimal)).quantize(Decimal('0.01'))

    # Fetch or create order
    customer = request.user.customer
    order, created = Order.objects.get_or_create(customer=customer, complete=False)

    # Auto add product to cart with 1 quantity
    order_item, created = OrderItem.objects.get_or_create(order=order, product=product)
    order_item.quantity += 1
    order_item.save()

    # Save offer data as strings (safe for session)
    request.session['offer_product_id'] = product.id
    request.session['offer_discount'] = int(discount)
    request.session['offer_price'] = str(final_price)

    messages.success(request, f"{discount}% Offer Applied Successfully on {product.name}")

    return redirect('cart')


@login_required
def profile(request):
    try:
        customer = request.user.customer
    except Customer.DoesNotExist:
        customer = Customer.objects.create(
            user=request.user,
            name=request.user.username,
            email=request.user.email
        )

    if request.method == 'POST':
        customer.name = request.POST.get('name')
        customer.email = request.POST.get('email')
        customer.phone = request.POST.get('phone')
        
        # Handle Address Construction
        address_line = request.POST.get('address_line', '')
        city = request.POST.get('city', '')
        state = request.POST.get('state', '')
        pincode = request.POST.get('pincode', '')
        country = request.POST.get('country', '')
        
        # Combine into a single string for storage
        full_address = f"{address_line}, {city}, {state}, {pincode}, {country}".strip(', ')
        customer.address = full_address

        if 'image' in request.FILES:
            customer.image = request.FILES['image']

        customer.save()
        messages.success(request, 'Profile updated successfully')
        return redirect('profile')

    # Try to parse existing address to pre-fill fields if possible
    # This is a basic split, it might not be perfect for old data but helpful
    address_parts = customer.address.split(', ') if customer.address else []
    # Assign defaults if split fails or is empty
    context = {
        'customer': customer,
        'address_line': address_parts[0] if len(address_parts) > 0 else '',
        'city': address_parts[1] if len(address_parts) > 1 else '',
        'state': address_parts[2] if len(address_parts) > 2 else '',
        'pincode': address_parts[3] if len(address_parts) > 3 else '',
        'country': address_parts[4] if len(address_parts) > 4 else ''
    }
    return render(request, 'profile.html', context)

def get_location(request):
    lat = request.GET.get('lat')
    lon = request.GET.get('lon')
    
    if not lat or not lon:
        return JsonResponse({'error': 'Missing coordinates'}, status=400)
    
    try:
        # User-Agent is required by Nominatim usage policy
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}&addressdetails=1"
        req = urllib.request.Request(url, headers={'User-Agent': 'GanarajWebPro/1.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            
        address = data.get('address', {})
        
        return JsonResponse({
            'road': address.get('road', '') or address.get('suburb', '') or address.get('residential', ''),
            'city': address.get('city', '') or address.get('town', '') or address.get('village', ''),
            'state': address.get('state', ''),
            'postcode': address.get('postcode', ''),
            'country': address.get('country', '')
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def cart(request):
    if request.user.is_authenticated:

        # Fetch or create customer object safely
        try:
            customer = request.user.customer
        except Customer.DoesNotExist:
            customer = Customer.objects.create(
                user=request.user,
                name=request.user.username,
                email=request.user.email
            )

        order, created = Order.objects.get_or_create(customer=customer, complete=False)
        items = order.orderitem_set.all()

        # Read offer info from session
        offer_product_id = request.session.get('offer_product_id')
        offer_price_str = request.session.get('offer_price')

        if offer_product_id and offer_price_str:
            offer_price = Decimal(offer_price_str)  # Convert back to Decimal

            for item in items:
                if item.product.id == offer_product_id:
                    item.discounted_price = offer_price
                    item.discounted_total = (offer_price * item.quantity).quantize(Decimal('0.01'))
                    item.discount_percent = request.session.get('offer_discount')
                else:
                    item.discounted_price = None

        # Calculate final cart total correctly using Decimal
        cart_total = Decimal('0.00')
        for item in items:
            if getattr(item, 'discounted_price', None):
                cart_total += item.discounted_total
            else:
                cart_total += Decimal(item.get_total)

    else:
        items = []
        order = {'get_cart_total': 0, 'get_cart_items': 0}
        cart_total = Decimal('0.00')

    context = {
        'items': items,
        'order': order,
        'cart_total': cart_total,
        'offer_product_id': request.session.get('offer_product_id'),
        'offer_price': request.session.get('offer_price'),
        'offer_discount': request.session.get('offer_discount')
    }
    return render(request, 'cart.html', context)
