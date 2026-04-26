from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid


class SiteSettings(models.Model):
    """Singleton model for company/site-wide settings configurable by admin."""
    company_name = models.CharField(max_length=200, default='Mithila Gold')
    address = models.TextField(default='Darbhanga, Mithila, Bihar')
    landmark = models.CharField(max_length=200, default='')
    phone_primary = models.CharField(max_length=20, default='6202822415', verbose_name='Phone (Satyan Jha)')
    phone_secondary = models.CharField(max_length=20, default='', blank=True, null=True)
    email = models.EmailField(blank=True, default='')
    gst_number = models.CharField(max_length=50, default='10AAQFJ2396C1ZJ')
    tagline = models.CharField(max_length=300, default='मिथिला की धरोहर — हर कौर में।')
    maps_embed_url = models.URLField(
        blank=True,
        default='https://maps.google.com/maps?q=Belhwar+Durga+Mandir+Madhubani+Bihar&output=embed'
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Site Settings'
        verbose_name_plural = 'Site Settings'

    def __str__(self):
        return 'Site Settings'

    def save(self, *args, **kwargs):
        # Enforce singleton
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_settings(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    description = models.CharField(max_length=200, blank=True)
    icon = models.CharField(max_length=100, default='📌')  # emoji icon for display

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    @property
    def in_stock(self):
        return self.stock > 0

    @property
    def image_url(self):
        if self.image:
            return self.image.url
        # Fallback to first gallery image if main image is missing
        gallery_image = self.images.first()
        if gallery_image:
            return gallery_image.image.url
        return '/static/img/product_placeholder.svg'

    def get_all_images(self):
        return self.images.all()


class ProductImage(models.Model):
    """Additional images for a product gallery."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/gallery/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Gallery image for {self.product.name}"


class Farmer(models.Model):
    """Extended profile for registered farmers."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='farmer_profile')
    phone = models.CharField(max_length=15, unique=True)
    address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} — {self.phone}"


class Order(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_PROCESSING = 'processing'
    STATUS_SHIPPED = 'shipped'
    STATUS_DELIVERED = 'delivered'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_PROCESSING, 'Processing'),
        (STATUS_SHIPPED, 'Shipped'),
        (STATUS_DELIVERED, 'Delivered'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    STATUS_COLORS = {
        STATUS_PENDING: 'warning',
        STATUS_PROCESSING: 'info',
        STATUS_SHIPPED: 'primary',
        STATUS_DELIVERED: 'success',
        STATUS_CANCELLED: 'danger',
    }

    farmer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='orders')
    customer_name = models.CharField(max_length=200)
    customer_phone = models.CharField(max_length=15)
    customer_address = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gst_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_mode = models.CharField(max_length=50, default='Cash')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.pk} — {self.customer_name}"

    @property
    def subtotal(self):
        return self.total_amount - self.gst_amount

    def get_status_color(self):
        return self.STATUS_COLORS.get(self.status, 'secondary')


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    product_name = models.CharField(max_length=200)  # stored at time of order
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product_name} x{self.quantity}"

    @property
    def total(self):
        return self.quantity * self.unit_price


class SalesRecord(models.Model):
    """Manual sales record for walk-in / offline sales."""
    PAYMENT_CASH = 'Cash'
    PAYMENT_UPI = 'UPI'
    PAYMENT_BANK = 'Bank Transfer'

    PAYMENT_CHOICES = [
        (PAYMENT_CASH, 'Cash'),
        (PAYMENT_UPI, 'UPI'),
        (PAYMENT_BANK, 'Bank Transfer'),
    ]

    customer_name = models.CharField(max_length=200)
    customer_phone = models.CharField(max_length=15)
    customer_address = models.TextField(blank=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    gst_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_mode = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default=PAYMENT_CASH)
    date = models.DateField(default=timezone.now)
    notes = models.TextField(blank=True)
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"Sale #{self.pk} — {self.customer_name} — ₹{self.total_amount}"

    @property
    def subtotal(self):
        return self.total_amount - self.gst_amount


class SalesItem(models.Model):
    """Line items within a SalesRecord."""
    sales_record = models.ForeignKey(SalesRecord, on_delete=models.CASCADE, related_name='items')
    product_name = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product_name} x{self.quantity}"

    @property
    def total(self):
        return self.quantity * self.unit_price


class PaymentReceipt(models.Model):
    """Generated PDF receipt — linked to either an Order or SalesRecord."""
    receipt_number = models.CharField(max_length=20, unique=True, blank=True)
    order = models.OneToOneField(Order, on_delete=models.CASCADE, null=True, blank=True, related_name='receipt')
    sales_record = models.OneToOneField(SalesRecord, on_delete=models.CASCADE, null=True, blank=True, related_name='receipt')
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-generated_at']

    def __str__(self):
        return f"Receipt #{self.receipt_number}"

    def save(self, *args, **kwargs):
        if not self.receipt_number:
            # Auto-generate receipt number
            last = PaymentReceipt.objects.order_by('-pk').first()
            next_num = (last.pk + 1) if last else 1
            self.receipt_number = f'RCP{next_num:05d}'
        super().save(*args, **kwargs)
