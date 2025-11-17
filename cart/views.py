from decimal import Decimal
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect, render
from myshop.models import Product
from .models import Cart, CartItem, Order
# import logging
from django.db import IntegrityError, transaction
import razorpay # type: ignore

# Create your views here.
# def fun(request):
#     return render(request, 'home.html')

def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        request.session.create()
        cart = request.session.session_key
    return cart

def add_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.user.is_authenticated:
        cart_item, created = CartItem.objects.get_or_create(
            user = request.user, product = product, defaults={'quantity':1}
        )
        if not created:
            cart_item.quantity += 1
            cart_item.save()
        response = redirect('cart:cart_detail')
    else: 
        cart_id = _cart_id(request)
        cart, created = Cart.objects.get_or_create(cart_id=cart_id)
        
        print(f"Using session cart: {cart.cart_id} (created={created})")
        cart_item, created = CartItem.objects.get_or_create(
            product = product, cart = cart, defaults={'quantity':1}
        )
        if not created:
            cart_item.quantity += 1
            cart_item.save()
        print(f"Added {product} x {cart_item.quantity} to session cart")
        response = redirect('cart:cart_detail')
        response.set_cookie('temp_cart_id', cart_id)
    return response

    

def cart_detail(request, total=0, counter=0, cart_items=None):
    try:
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, active=True)

        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, active=True)
        for item in cart_items:
            total += (item.product.get_final_price() * item.quantity)
            counter += item.quantity
    except Cart.DoesNotExist:
        cart_items = []
    return render(request, 'cart.html', dict(cart_items=cart_items, total=total, counter=counter))
    
def cart_remove(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.user.is_authenticated:
        try:
            cart_item = CartItem.objects.get(product=product, user=request.user)
        except CartItem.DoesNotExist:
            return redirect('cart:cart_detail')
    else:
        cart = Cart.objects.get(cart_id=_cart_id(request))
    
        cart_item = CartItem.objects.get(product=product, cart=cart)
    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()
    else:
        cart_item.delete()
    return redirect('cart:cart_detail')

def full_remove(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if request.user.is_authenticated:
        CartItem.objects.filter(product=product, user=request.user).delete()
    else:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_item = CartItem.objects.get(product=product, cart=cart)
        cart_item.delete()
    return redirect('cart:cart_detail')


def merge_session_cart(request,user):
    cart_id = request.COOKIES.get('temp_cart_id') or request.session.get('cart_id') or _cart_id(request)
    print(f"Session cart id: {cart_id}")
    if not cart_id:
        print("No session cart_id found at all")
        return
    try:
        session_cart = Cart.objects.get(cart_id = cart_id)
        session_cart_items = CartItem.objects.filter(cart=session_cart)
        print(f"Found {session_cart_items.count()} session items")
    except Cart.DoesNotExist:
        print("No session cart found")
        return 
    if not session_cart_items:
        print("Session cart has no items")
        return
   
    for item in session_cart_items:
        try:
            print(f"Merging {item.product} x{item.quantity}")
            existing_item = CartItem.objects.filter(user=user, product=item.product).first()
            if existing_item:
                existing_item.quantity += item.quantity
                existing_item.save()
                print(f"Updated existing item: {existing_item.product} ({existing_item.quantity})")
            else:
                item.user = user
                item.cart = None
                item.save()
                print(f"Moved {item.product} to new cart")
        except IntegrityError as e:
            print(f'Integrity errormerging item {item.id}')
        session_cart.delete()
       
        print("Session cart merged successfully!")


def checkout(request):
    total=0 
    counter=0
    cart_items = []
    user =  request.user
    print(f"Checkout initiated by user: {request.user.username}")
    try:
        if request.user.is_authenticated:
            cart, created = Cart.objects.get_or_create(user=user)
            cart_items = CartItem.objects.filter(user=user, active=True)
            print(f"Using user cart: {cart.cart_id}")
        else:
            cart, created = Cart.objects.get_or_create(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, active=True)
            print(f"Using session cart: {cart.cart_id}")
    
        if not user.is_authenticated:
            return redirect('accounts:login')

    except Cart.DoesNotExist:
        cart_items = []
        print("No cart found during checkout")
    if not cart_items.exists():
        print("No items in cart during checkout")
        return redirect('cart:cart_detail')
    for cart_item in cart_items:
        total += (cart_item.product.get_final_price() * cart_item.quantity)
        counter += cart_item.quantity
    print(f"Total:{total},counter: {counter}")
    amount_paise = int(total * 100)  # Convert to paise
    
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    payment = client.order.create({'amount': amount_paise, 'currency': 'INR', 'payment_capture':'1'})
    order = Order.objects.create(user=user, total_amount=total, razorpay_order_id=payment['id'])
    context = {
            'cart_items': cart_items,
            'total': total,
            'counter': counter,
            'razorpay_key_id': settings.RAZORPAY_KEY_ID,
            'payment': amount_paise,
            'user': user,
            'cart_id': cart.cart_id,
            'order': order,
        }
    
    return render(request, 'payment.html', context)

def payment_success(request):
   
    order_id = request.GET.get('order_id')
    payment_id = request.GET.get('payment_id')
    signature = request.GET.get('signature')
    order = Order.objects.get(id = order_id)
    order.razorpay_signature = signature
    order.paid = True
    order.save()
    Cart.objects.filter(user=order.user).delete()
    return render(request, 'success.html', {'order': order})