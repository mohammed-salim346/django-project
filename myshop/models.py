from django.db import models
from django.urls import reverse

# Create your models here.
class Category(models.Model):
    name = models.CharField(max_length=250, unique=True)
    slug = models.SlugField(max_length=250, unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='category', blank=True)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    class Meta:
        ordering = ('name',)
        verbose_name = 'category'
        verbose_name_plural = 'categories'

    def get_url(self):
        return reverse('myshop:products_by_category',args=[self.slug])

    def __str__(self):
        return '{}'.format(self.name)
    
    
    
class Product(models.Model):
    name = models.CharField(max_length=250, unique=True)
    slug = models.SlugField(max_length=250, unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='product', blank=True)
    stock = models.IntegerField()
    available = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    class Meta:
        ordering = ('name',)
        verbose_name = 'product'
        verbose_name_plural = 'products'

    def get_url(self):
        return reverse('myshop:proCatdetail', args=[self.category.slug, self.slug])

    def __str__(self):
        return '{}'.format(self.name)
    
    def get_final_price(self):
        category_discount = self.category.discount_percentage or 0
        product_discount = self.discount_percentage or 0

        best_discount = max(category_discount, product_discount)

        discount_amount = float(best_discount / 100) * float(self.price) 
        final_price = float(self.price) - float(discount_amount)
        return round(final_price, 2)
    def get_discount_info(self):
        category_discount = self.category.discount_percentage 
        product_discount = self.discount_percentage
        if product_discount >= category_discount:
            return f"{product_discount}% (Product offer)"
        else:
            return f"{category_discount}% (Category offer)"