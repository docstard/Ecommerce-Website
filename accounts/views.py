from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.forms import inlineformset_factory
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group

from django.contrib import messages

from .models import *
from .forms import OrderForm, CreateUserForm, CustumerForm
from .filters import OrderFilter
from .decorators import unauthenticated_user, users_allowed, only_admin

# Create your views here.

@unauthenticated_user
def registerPage(request):

    form = CreateUserForm()
    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')

            group = Group.objects.get(name='customer')
            user.groups.add(group)

            Customer.objects.create(
                user=user,
            )

            messages.success(request, 'Account for created for ' + username)

            return redirect('login')
    para = {'form':form}
    return render(request, 'accounts/register.html', para)

@unauthenticated_user
def loginPage(request):
    if request.method=='POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password = password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.info(request, 'Username or Password is incorrect')

    para = {}
    return render(request, 'accounts/login.html', para)

def logoutUser(request):
    logout(request)
    return redirect('login')

@login_required(login_url='login')
@only_admin
def home(request):
    orders = Order.objects.all()
    customers = Customer.objects.all()

    total_customers = customers.count()

    total_orders = orders.count()
    delivered = orders.filter(status='Delivered').count()
    pending = orders.filter(status='Pending').count()

    param = {'orders':orders, 'customers': customers, 'total_customers':total_customers, 
    'total_orders':total_orders, 'delivered':delivered,'pending':pending }

    return render(request, 'accounts/dashboard.html', param)

@login_required(login_url='login')
@users_allowed(roles_allowed=['customer'])
def userPage(request):
    orders = request.user.customer.order_set.all()

    total_orders = orders.count()
    delivered = orders.filter(status='Delivered').count()
    pending = orders.filter(status='Pending').count()
    
    para = {'orders' : orders, 'total_orders':total_orders, 'delivered':delivered,'pending':pending}      
    return render(request, 'accounts/user.html', para)


@login_required(login_url='login')
@users_allowed(roles_allowed=['customer'])
def accountSettings(request):
	customer = request.user.customer
	form = CustumerForm(instance=customer)

	if request.method == 'POST':
		form = CustumerForm(request.POST, request.FILES,instance=customer)
		if form.is_valid():
			form.save()


	context = {'form':form}
	return render(request, 'accounts/account_settings.html', context)


@login_required(login_url='login')
@users_allowed(roles_allowed=['admin'])
def product(request):
    products = Product.objects.all()
    return render(request, 'accounts/products.html',{'products':products})


@login_required(login_url='login')
@users_allowed(roles_allowed=['admin'])
def customer(request, pkey):
    customer = Customer.objects.get(id=pkey)

    orders = customer.order_set.all()
    order_count = orders.count()

    myFilter = OrderFilter(request.GET, queryset=orders)
    orders = myFilter.qs

    param = {'customer':customer,'orders':orders, 'order_count':order_count,'myFilter':myFilter}
    return render(request, 'accounts/customer.html',param)


@login_required(login_url='login')
@users_allowed(roles_allowed=['admin'])
def createOrder(request, pk):
    OrderFormSet = inlineformset_factory(Customer, Order, fields=('product','status'), extra=5)
    customer = Customer.objects.get(id=pk)
    formset = OrderFormSet(queryset=Order.objects.none() ,instance=customer)
    # form = OrderForm(initial={'customer':customer})
    if request.method == 'POST':
        # form = OrderForm(request.method)
        formset = OrderFormSet(request.POST ,instance=customer)
        if formset.is_valid():
            formset.save()
            return redirect('/')

    para = {'formset':formset}
    return render(request, 'accounts/order_form.html', para)


@login_required(login_url='login')
@users_allowed(roles_allowed=['admin'])
def updateOrder(request,pk):
    order = Order.objects.get(id=pk)
    form = OrderForm(instance=order)
    if request.method == 'POST':
        form = OrderForm(request.method, instance=order)
        if form.is_valid():
            form.save()
            return redirect('/')

    param = {'form':form}
    return render(request, 'accounts/order_form.html', param)


@login_required(login_url='login')
@users_allowed(roles_allowed=['admin'])
def deleteOrder(request, pk):
    order = Order.objects.get(id=pk)

    if request.method == 'POST':
        order.delete()
        redirect('/')

    param = {'item':order}
    return render(request, 'accounts/delete.html', param)