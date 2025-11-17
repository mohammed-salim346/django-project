from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from myshop.models import Category, Product

# Create your views here.
# def demo(request):
#     # return HttpResponse ("<h1>Hellooo<h1>")
#     # return render(request, 'home.html')
#     return render(request, 'index.html')

def add(request):
    val1 = int(request.GET['num1'])
    val2 = int(request.GET['num2'])
    res = val1+val2
    sub_res = val1-val2
    mul_res = val1*val2
    div_res = val1/val2
    return render(request, 'result.html', {'result':res,'sub_result':sub_res,'mul_result':mul_res, 'div_result':div_res})

def allProdCat(request,c_slug=None):
    c_page = None
    products_list = None
    if c_slug != None:
        c_page = get_object_or_404(Category, slug=c_slug)
        products_list = Product.objects.all().filter(category= c_page, available=True)
    else:
        products_list = Product.objects.all().filter(available=True)
    paginator = Paginator(products_list, 6)
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)
    
    
    return render(request, 'category.html', {'category':c_page, 'products':products})

def pro_detail(request, c_slug, product_slug):
    try:
        product = Product.objects.get(category__slug=c_slug, slug=product_slug)
    except Exception as e:
        raise e
    return render(request, 'product.html',{'product':product})

        