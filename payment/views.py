from django.shortcuts import render, redirect
from cart.cart import Cart
from payment.forms import ShippingForm, PaymentForm
from payment.models import ShippingAddress, Order, OrderItem
from django.contrib.auth.models import User
from django.contrib import messages
from store.models import Product, Profile
import datetime

def orders(request, pk):
    if request.user.is_authenticated and request.user.is_superuser:
        order = Order.objects.get(id=pk)
        items = OrderItem.objects.filter(order=pk)

        if request.POST:
            status = request.POST['shipping_status']
            now = datetime.datetime.now()
            Order.objects.filter(id=pk).update(shipped=status == "true", date_shipped=now if status == "true" else None)
            messages.success(request, "Shipping Status Updated")
            return redirect('home')

        return render(request, 'payment/orders.html', {"order": order, "items": items})
    
    messages.success(request, "Access Denied")
    return redirect('home')

def not_shipped_dash(request):
    if request.user.is_authenticated and request.user.is_superuser:
        orders = Order.objects.filter(shipped=False)
        if request.POST:
            num = request.POST['num']
            now = datetime.datetime.now()
            Order.objects.filter(id=num).update(shipped=True, date_shipped=now)
            messages.success(request, "Shipping Status Updated")
            return redirect('home')

        return render(request, "payment/not_shipped_dash.html", {"orders": orders})
    
    messages.success(request, "Access Denied")
    return redirect('home')

def shipped_dash(request):
    if request.user.is_authenticated and request.user.is_superuser:
        orders = Order.objects.filter(shipped=True)
        if request.POST:
            num = request.POST['num']
            Order.objects.filter(id=num).update(shipped=False)
            messages.success(request, "Shipping Status Updated")
            return redirect('home')

        return render(request, "payment/shipped_dash.html", {"orders": orders})
    
    messages.success(request, "Access Denied")
    return redirect('home')

def process_order(request):
    if request.POST:
        cart = Cart(request)
        cart_products = cart.get_prods
        quantities = cart.get_quants
        totals = cart.cart_total()
        my_shipping = request.session.get('my_shipping')

        full_name = my_shipping['shipping_full_name']
        email = my_shipping['shipping_email']
        shipping_address = f"{my_shipping['shipping_address1']}\n{my_shipping['shipping_address2']}\n{my_shipping['shipping_city']}\n{my_shipping['shipping_state']}\n{my_shipping['shipping_zipcode']}\n{my_shipping['shipping_country']}"
        amount_paid = totals

        create_order = Order(user=request.user if request.user.is_authenticated else None,
                             full_name=full_name, email=email,
                             shipping_address=shipping_address, amount_paid=amount_paid)
        create_order.save()
        order_id = create_order.pk

        for product in cart_products():
            price = product.sale_price if product.is_sale else product.price
            for key, value in quantities().items():
                if int(key) == product.id:
                    OrderItem.objects.create(order_id=order_id, product_id=product.id, 
                                             user=request.user if request.user.is_authenticated else None, 
                                             quantity=value, price=price)

        for key in list(request.session.keys()):
            if key == "session_key":
                del request.session[key]

        if request.user.is_authenticated:
            Profile.objects.filter(user__id=request.user.id).update(old_cart="")

        messages.success(request, "Order Placed!")
        return redirect('home')
    
    messages.success(request, "Access Denied")
    return redirect('home')

def billing_info(request):
    if request.POST:
        cart = Cart(request)
        cart_products = cart.get_prods
        quantities = cart.get_quants
        totals = cart.cart_total()
        request.session['my_shipping'] = request.POST
        billing_form = PaymentForm()
        return render(request, "payment/billing_info.html", {"cart_products": cart_products, "quantities": quantities, "totals": totals, "shipping_info": request.POST, "billing_form": billing_form})
    
    messages.success(request, "Access Denied")
    return redirect('home')

def checkout(request):
    cart = Cart(request)
    cart_products = cart.get_prods
    quantities = cart.get_quants
    totals = cart.cart_total()

    if request.user.is_authenticated:
        shipping_user = ShippingAddress.objects.get(user__id=request.user.id)
        shipping_form = ShippingForm(request.POST or None, instance=shipping_user)
    else:
        shipping_form = ShippingForm(request.POST or None)
    
    return render(request, "payment/checkout.html", {"cart_products": cart_products, "quantities": quantities, "totals": totals, "shipping_form": shipping_form})

def payment_success(request):
    return render(request, "payment/payment_success.html", {})

def payment_failed(request):
    return render(request, "payment/payment_failed.html", {})
