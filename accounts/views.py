from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from cart.views import merge_session_cart, _cart_id
from cart.models import CartItem
import pprint


def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
        else:
            user = User.objects.create_user(
                username=username,
                password=password,
                email=email
            )
            user.save()
            messages.success(request, "User registered successfully")
            return redirect('accounts:login')
    return render(request, 'register.html')

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(username=username, password=password)
        # pprint.pprint(request.session.get('cart'))
        if user:   
            # old_session_key = request.session.session_key
            login(request, user)

            # request.session.save()
        
        # if old_session_key:
        #     request.session['cart_id'] = old_session_key
            try:
                merge_session_cart(request, user)
            except Exception as e:
                print('Error during merge: {e}')
            response = redirect('cart:cart_detail')
            response.delete_cookie('temp_cart_id')
            return response
        else:
            return render(request, 'login.html', {'error':'Invalid credentials'})
    

            # login(request, user)
            # merge_session_cart(request, user)
            
            # return redirect('cart:cart_detail')
        
    return render(request, 'login.html')

def user_logout(request):
    logout(request)
    return redirect('myshop:allProdCat')

def profile(request):
    return render(request,'profile.html')