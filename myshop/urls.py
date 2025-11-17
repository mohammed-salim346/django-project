from django.urls import path
from . import views
app_name = 'myshop'
urlpatterns =[

    # path('',views.demo, name='demo'),
    path('',views.allProdCat, name='allProdCat'),
    path('add/', views.add, name='add'),
    path('<slug:c_slug>/', views.allProdCat, name='products_by_category'),
    path('<slug:c_slug>/<slug:product_slug>/', views.pro_detail, name='proCatdetail'),
]