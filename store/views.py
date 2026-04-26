from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db.models import Q, Sum
from django.views.decorators.cache import patch_cache_control
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.views.decorators.http import require_POST
import csv
import json

from .models import (
    Category, Product, ProductImage, Order, OrderItem,
    SalesRecord, SalesItem, SiteSettings, Farmer
)
from .forms import (
    FarmerRegisterForm, FarmerLoginForm,
    CheckoutForm, SiteSettingsForm
)
from .utils import generate_order_receipt_pdf, generate_sales_receipt_pdf


# ══════════════════════════════════════════════════════════════
#  Helper
# ══════════════════════════════════════════════════════════════

def is_admin(user):
    return user.is_staff or user.is_superuser


def get_cart(request):
    """Return the cart dict from session."""
    return request.session.get('cart', {})


def save_cart(request, cart):
    request.session['cart'] = cart
    request.session.modified = True


# ══════════════════════════════════════════════════════════════
#  PUBLIC PAGES
# ══════════════════════════════════════════════════════════════

def home(request):
    categories = Category.objects.all()
    featured = Product.objects.filter(is_active=True, stock__gt=0)[:8]
    context = {
        'categories': categories,
        'featured_products': featured,
        'page_title': 'Home',
    }
    return render(request, 'home.html', context)


def product_list(request):
    products = Product.objects.filter(is_active=True)
    categories = Category.objects.all()

    category_slug = request.GET.get('category', '')
    search_query = request.GET.get('q', '')

    if category_slug:
        products = products.filter(category__slug=category_slug)
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) | Q(description__icontains=search_query)
        )

    context = {
        'products': products,
        'categories': categories,
        'selected_category': category_slug,
        'search_query': search_query,
        'page_title': 'Products',
    }
    return render(request, 'products/product_list.html', context)


def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk, is_active=True)
    related = Product.objects.filter(category=product.category, is_active=True).exclude(pk=pk)[:4]
    context = {
        'product': product,
        'related_products': related,
        'page_title': product.name,
    }
    return render(request, 'products/product_detail.html', context)


def contact(request):
    settings = SiteSettings.get_settings()
    context = {
        'settings': settings,
        'page_title': 'Contact Us',
    }
    return render(request, 'contact.html', context)


# ══════════════════════════════════════════════════════════════
#  CART
# ══════════════════════════════════════════════════════════════

def cart_view(request):
    cart = get_cart(request)
    cart_items = []
    grand_total = 0

    for product_id, item in cart.items():
        try:
            product = Product.objects.get(pk=product_id)
            total = product.price * item['quantity']
            grand_total += total
            cart_items.append({
                'product': product,
                'quantity': item['quantity'],
                'total': total,
            })
        except Product.DoesNotExist:
            pass

    context = {
        'cart_items': cart_items,
        'grand_total': grand_total,
        'gst': round(float(grand_total) * 0.05, 2),
        'total_with_gst': round(float(grand_total) * 1.05, 2),
        'page_title': 'My Cart',
    }
    return render(request, 'cart.html', context)


@require_POST
def add_to_cart(request, pk):
    product = get_object_or_404(Product, pk=pk, is_active=True)
    cart = get_cart(request)

    quantity = int(request.POST.get('quantity', 1))
    if quantity < 1:
        quantity = 1

    key = str(pk)
    if key in cart:
        new_qty = cart[key]['quantity'] + quantity
        cart[key]['quantity'] = min(new_qty, product.stock)
    else:
        cart[key] = {'quantity': min(quantity, product.stock)}

    save_cart(request, cart)
    messages.success(request, f'✅ "{product.name}" added to cart!')

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        count = sum(i['quantity'] for i in cart.values())
        return JsonResponse({'success': True, 'cart_count': count})
    return redirect('store:cart')


@require_POST
def update_cart(request, pk):
    cart = get_cart(request)
    key = str(pk)
    quantity = int(request.POST.get('quantity', 1))

    if quantity <= 0:
        cart.pop(key, None)
        messages.info(request, 'Item removed from cart.')
    else:
        if key in cart:
            product = get_object_or_404(Product, pk=pk)
            cart[key]['quantity'] = min(quantity, product.stock)

    save_cart(request, cart)
    return redirect('store:cart')


@require_POST
def remove_from_cart(request, pk):
    cart = get_cart(request)
    cart.pop(str(pk), None)
    save_cart(request, cart)
    messages.info(request, 'Item removed from cart.')
    return redirect('store:cart')


# ══════════════════════════════════════════════════════════════
#  CHECKOUT & ORDERS
# ══════════════════════════════════════════════════════════════

@login_required
def checkout(request):
    cart = get_cart(request)
    if not cart:
        messages.warning(request, 'Your cart is empty!')
        return redirect('store:cart')

    cart_items = []
    subtotal = 0
    for product_id, item in cart.items():
        try:
            product = Product.objects.get(pk=product_id)
            total = product.price * item['quantity']
            subtotal += total
            cart_items.append({'product': product, 'quantity': item['quantity'], 'total': total})
        except Product.DoesNotExist:
            pass

    gst = round(float(subtotal) * 0.05, 2)
    grand_total = round(float(subtotal) + gst, 2)

    initial = {}
    if hasattr(request.user, 'farmer_profile'):
        fp = request.user.farmer_profile
        initial = {
            'customer_name': request.user.get_full_name(),
            'customer_phone': fp.phone,
            'customer_address': fp.address,
        }

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            # Validate stock
            out_of_stock = []
            for product_id, item in cart.items():
                try:
                    p = Product.objects.get(pk=product_id)
                    if p.stock < item['quantity']:
                        out_of_stock.append(p.name)
                except Product.DoesNotExist:
                    pass

            if out_of_stock:
                messages.error(request, f'Sorry, insufficient stock for: {", ".join(out_of_stock)}')
            else:
                order = form.save(commit=False)
                order.farmer = request.user
                order.total_amount = grand_total
                order.gst_amount = gst
                order.save()

                # Create OrderItems and deduct stock
                for product_id, item in cart.items():
                    try:
                        product = Product.objects.get(pk=product_id)
                        OrderItem.objects.create(
                            order=order,
                            product=product,
                            product_name=product.name,
                            quantity=item['quantity'],
                            unit_price=product.price,
                        )
                        product.stock -= item['quantity']
                        product.save()
                    except Product.DoesNotExist:
                        pass

                # Clear cart
                request.session['cart'] = {}
                request.session.modified = True

                messages.success(request, f'🎉 Order #{order.pk} placed successfully!')
                return redirect('store:order_confirmation', pk=order.pk)
    else:
        form = CheckoutForm(initial=initial)

    context = {
        'form': form,
        'cart_items': cart_items,
        'subtotal': subtotal,
        'gst': gst,
        'grand_total': grand_total,
        'page_title': 'Checkout',
    }
    return render(request, 'checkout.html', context)


@login_required
def order_confirmation(request, pk):
    order = get_object_or_404(Order, pk=pk, farmer=request.user)
    context = {
        'order': order,
        'page_title': f'Order #{order.pk} Confirmed',
    }
    return render(request, 'order_confirmation.html', context)


@login_required
def my_orders(request):
    orders = Order.objects.filter(farmer=request.user).prefetch_related('items')
    context = {
        'orders': orders,
        'page_title': 'My Orders',
    }
    return render(request, 'orders/my_orders.html', context)


# ══════════════════════════════════════════════════════════════
#  PDF RECEIPTS
# ══════════════════════════════════════════════════════════════

@login_required
def receipt_pdf(request, pk):
    order = get_object_or_404(Order, pk=pk)
    # Farmer can only see their own; staff/admin can see all
    if not (request.user.is_staff or order.farmer == request.user):
        messages.error(request, 'Access denied.')
        return redirect('store:my_orders')

    buffer = generate_order_receipt_pdf(order)
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    # Use a timestamp in filename to bust browser cache
    ts = timezone.now().strftime('%H%M%S')
    response['Content-Disposition'] = f'inline; filename="receipt_order_{pk}_{ts}.pdf"'
    patch_cache_control(response, no_cache=True, no_store=True, must_revalidate=True)
    return response


@user_passes_test(is_admin)
def sales_receipt_pdf(request, pk):
    sales_record = get_object_or_404(SalesRecord, pk=pk)
    buffer = generate_sales_receipt_pdf(sales_record)
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    ts = timezone.now().strftime('%H%M%S')
    response['Content-Disposition'] = f'inline; filename="receipt_sale_{pk}_{ts}.pdf"'
    patch_cache_control(response, no_cache=True, no_store=True, must_revalidate=True)
    return response


# ══════════════════════════════════════════════════════════════
#  AUTH
# ══════════════════════════════════════════════════════════════

def farmer_register(request):
    if request.user.is_authenticated:
        return redirect('store:home')

    if request.method == 'POST':
        form = FarmerRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'🌾 Welcome, {user.first_name}! Your account has been created.')
            return redirect('store:home')
    else:
        form = FarmerRegisterForm()

    return render(request, 'auth/register.html', {'form': form, 'page_title': 'Register'})


def farmer_login(request):
    if request.user.is_authenticated:
        return redirect('store:home')

    if request.method == 'POST':
        form = FarmerLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                messages.success(request, f'🌾 Welcome back, {user.first_name or user.username}!')
                next_url = request.GET.get('next', 'store:home')
                return redirect(next_url)
            else:
                messages.error(request, '❌ Invalid username or password. Please try again.')
    else:
        form = FarmerLoginForm()

    return render(request, 'auth/login.html', {'form': form, 'page_title': 'Login'})


@csrf_exempt
def farmer_logout(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('store:home')


# ══════════════════════════════════════════════════════════════
#  CUSTOM ADMIN VIEWS
# ══════════════════════════════════════════════════════════════

@login_required
def admin_sales_list(request):
    """Custom admin view: list all sales records with export."""
    if not request.user.is_staff:
        return render(request, 'admin_custom/access_denied.html', status=403)
    sales = SalesRecord.objects.prefetch_related('items').all()

    # CSV export
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="sales_{timezone.now().date()}.csv"'
        writer = csv.writer(response)
        writer.writerow(['ID', 'Customer', 'Phone', 'Address', 'Total (₹)', 'GST (₹)', 'Payment Mode', 'Date'])
        for record in sales:
            writer.writerow([
                record.pk, record.customer_name, record.customer_phone,
                record.customer_address, record.total_amount, record.gst_amount,
                record.payment_mode, record.date
            ])
        return response

    # Filter
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    payment = request.GET.get('payment', '')

    if date_from:
        sales = sales.filter(date__gte=date_from)
    if date_to:
        sales = sales.filter(date__lte=date_to)
    if payment:
        sales = sales.filter(payment_mode=payment)

    total_revenue = sales.aggregate(total=Sum('total_amount'))['total'] or 0

    context = {
        'sales': sales,
        'total_revenue': total_revenue,
        'payment_choices': SalesRecord.PAYMENT_CHOICES,
        'page_title': 'Sales Records',
    }
    return render(request, 'admin_custom/sales_list.html', context)


@login_required
def admin_sales_add(request):
    """Custom admin view: add a manual sales record."""
    if not request.user.is_staff:
        return render(request, 'admin_custom/access_denied.html', status=403)
    from .forms import SalesRecordAdminForm

    if request.method == 'POST':
        customer_name = request.POST.get('customer_name', '').strip()
        customer_phone = request.POST.get('customer_phone', '').strip()
        customer_address = request.POST.get('customer_address', '').strip()
        payment_mode = request.POST.get('payment_mode', 'Cash')
        date = request.POST.get('date') or timezone.now().date()
        notes = request.POST.get('notes', '')
        gst_rate = float(request.POST.get('gst_rate', 0)) / 100

        # Parse items
        product_names = request.POST.getlist('product_name[]')
        quantities = request.POST.getlist('quantity[]')
        unit_prices = request.POST.getlist('unit_price[]')

        items = []
        subtotal = 0
        for i in range(len(product_names)):
            try:
                pname = product_names[i].strip()
                qty = int(quantities[i])
                price = float(unit_prices[i])
                if pname and qty > 0 and price >= 0:
                    items.append({'name': pname, 'qty': qty, 'price': price})
                    subtotal += qty * price
            except (ValueError, IndexError):
                pass

        if not customer_name or not items:
            messages.error(request, 'Customer name and at least one item are required.')
        else:
            gst_amount = round(subtotal * gst_rate, 2)
            grand_total = round(subtotal + gst_amount, 2)

            record = SalesRecord.objects.create(
                customer_name=customer_name,
                customer_phone=customer_phone,
                customer_address=customer_address,
                payment_mode=payment_mode,
                date=date,
                notes=notes,
                total_amount=grand_total,
                gst_amount=gst_amount,
                added_by=request.user,
            )
            for item in items:
                SalesItem.objects.create(
                    sales_record=record,
                    product_name=item['name'],
                    quantity=item['qty'],
                    unit_price=item['price'],
                )
            messages.success(request, f'✅ Sales record #{record.pk} added for {customer_name}!')
            return redirect('store:admin_sales_list')

    products = Product.objects.filter(is_active=True)
    context = {
        'payment_choices': SalesRecord.PAYMENT_CHOICES,
        'products': products,
        'today': timezone.now().date(),
        'page_title': 'Add Sales Record',
    }
    return render(request, 'admin_custom/sales_add.html', context)


@login_required
def admin_site_settings(request):
    if not request.user.is_staff:
        return render(request, 'admin_custom/access_denied.html', status=403)
    settings_obj = SiteSettings.get_settings()
    if request.method == 'POST':
        form = SiteSettingsForm(request.POST, instance=settings_obj)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Site settings updated successfully!')
            return redirect('store:admin_settings')
    else:
        form = SiteSettingsForm(instance=settings_obj)

    context = {
        'form': form,
        'page_title': 'Site Settings',
    }
    return render(request, 'admin_custom/settings.html', context)


@login_required
def admin_products_list(request):
    """Custom admin view: list all products with search/filter."""
    if not request.user.is_staff:
        return render(request, 'admin_custom/access_denied.html', status=403)
    products = Product.objects.select_related('category').all()
    categories = Category.objects.all()

    category_slug = request.GET.get('category', '')
    search_query = request.GET.get('q', '')

    if category_slug:
        products = products.filter(category__slug=category_slug)
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) | Q(description__icontains=search_query)
        )

    context = {
        'products': products,
        'categories': categories,
        'current_category': category_slug,
        'search_query': search_query,
        'page_title': 'Products',
    }
    return render(request, 'admin_custom/products_list.html', context)


@login_required
def admin_products_add(request):
    """Custom admin view: add a new product."""
    if not request.user.is_staff:
        return render(request, 'admin_custom/access_denied.html', status=403)
    categories = Category.objects.all()
    form_data = None

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        category_id = request.POST.get('category', '')
        price = request.POST.get('price', '')
        stock = request.POST.get('stock', 0)
        is_active = request.POST.get('is_active') == 'on'
        image = request.FILES.get('image')

        errors = []
        if not name:
            errors.append('Product name is required.')
        if not description:
            errors.append('Description is required.')
        if not category_id:
            errors.append('Category is required.')
        try:
            price = float(price)
            if price < 0:
                errors.append('Price cannot be negative.')
        except (ValueError, TypeError):
            errors.append('Enter a valid price.')
        try:
            stock = int(stock)
        except (ValueError, TypeError):
            stock = 0

        if errors:
            for e in errors:
                messages.error(request, e)
        else:
            category = get_object_or_404(Category, pk=category_id)
            product = Product(
                name=name,
                description=description,
                category=category,
                price=price,
                stock=stock,
                is_active=is_active,
            )
            if image:
                product.image = image
            product.save()

            # Handle gallery images (up to 10)
            gallery_images = request.FILES.getlist('gallery_images')
            for img in gallery_images[:10]:
                ProductImage.objects.create(product=product, image=img)

            messages.success(request, f'✅ Product "{name}" added successfully with gallery!')
            return redirect('store:admin_products_list')

    context = {
        'categories': categories,
        'form': form_data,
        'page_title': 'Add Product',
    }
    return render(request, 'admin_custom/products_add.html', context)


@login_required
def admin_products_edit(request, pk):
    """Custom admin view: edit an existing product."""
    if not request.user.is_staff:
        return render(request, 'admin_custom/access_denied.html', status=403)
    product = get_object_or_404(Product, pk=pk)
    categories = Category.objects.all()

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        category_id = request.POST.get('category', '')
        price = request.POST.get('price', '')
        stock = request.POST.get('stock', 0)
        is_active = request.POST.get('is_active') == 'on'
        image = request.FILES.get('image')
        clear_image = request.POST.get('clear_image') == 'on'

        errors = []
        if not name:
            errors.append('Product name is required.')
        if not description:
            errors.append('Description is required.')
        if not category_id:
            errors.append('Category is required.')
        try:
            price = float(price)
        except (ValueError, TypeError):
            errors.append('Enter a valid price.')
        try:
            stock = int(stock)
        except (ValueError, TypeError):
            stock = 0

        if errors:
            for e in errors:
                messages.error(request, e)
        else:
            product.name = name
            product.description = description
            product.category = get_object_or_404(Category, pk=category_id)
            product.price = price
            product.stock = stock
            product.is_active = is_active
            if clear_image:
                product.image = None
            if image:
                product.image = image
            product.save()

            # Handle gallery deletions
            delete_gallery_ids = request.POST.getlist('delete_gallery')
            if delete_gallery_ids:
                ProductImage.objects.filter(pk__in=delete_gallery_ids, product=product).delete()

            # Handle new gallery images (up to 10 total)
            current_count = product.images.count()
            new_gallery_images = request.FILES.getlist('gallery_images')
            for img in new_gallery_images[:(10 - current_count)]:
                ProductImage.objects.create(product=product, image=img)

            messages.success(request, f'✅ Product "{name}" updated successfully!')
            return redirect('store:admin_products_list')

    context = {
        'product': product,
        'categories': categories,
        'form': None,
        'page_title': f'Edit — {product.name}',
    }
    return render(request, 'admin_custom/products_edit.html', context)


@login_required
def admin_products_delete(request, pk):
    """Custom admin view: delete a product."""
    if not request.user.is_staff:
        return render(request, 'admin_custom/access_denied.html', status=403)
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        name = product.name
        product.delete()
        messages.success(request, f'🗑️ Product "{name}" deleted.')
    return redirect('store:admin_products_list')


@login_required
def admin_dashboard(request):
    """Custom unified Admin Dashboard using standard UI."""
    if not request.user.is_staff:
        return render(request, 'admin_custom/access_denied.html', status=403)
    online_sales = Order.objects.aggregate(total=Sum('total_amount'))['total'] or 0
    walkin_sales = SalesRecord.objects.aggregate(total=Sum('total_amount'))['total'] or 0
    total_revenue = online_sales + walkin_sales

    total_orders = Order.objects.count()
    total_walkins = SalesRecord.objects.count()
    total_farmers = Farmer.objects.count()
    
    recent_orders = Order.objects.all().order_by('-created_at')[:5]

    context = {
        'page_title': 'Admin Dashboard',
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'total_walkins': total_walkins,
        'total_farmers': total_farmers,
        'recent_orders': recent_orders,
    }
    return render(request, 'admin_custom/dashboard.html', context)


@login_required
def admin_orders_list(request):
    """Custom view for listing all online orders."""
    if not request.user.is_staff:
        return render(request, 'admin_custom/access_denied.html', status=403)
    orders = Order.objects.prefetch_related('items').all()
    
    status_filter = request.GET.get('status', '')
    if status_filter:
        orders = orders.filter(status=status_filter)
        
    context = {
        'orders': orders,
        'status_choices': Order.STATUS_CHOICES,
        'current_status': status_filter,
        'page_title': 'Online Orders',
    }
    return render(request, 'admin_custom/orders_list.html', context)


@user_passes_test(is_admin)
def admin_order_detail(request, pk):
    """Custom view for managing a specific online order."""
    order = get_object_or_404(Order, pk=pk)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            order.save()
            messages.success(request, f'Order #{order.pk} status updated to {order.get_status_display()}.')
            return redirect('store:admin_order_detail', pk=order.pk)
            
    context = {
        'order': order,
        'status_choices': Order.STATUS_CHOICES,
        'page_title': f'Manage Order #{order.pk}',
    }
    return render(request, 'admin_custom/order_detail.html', context)


# ══════════════════════════════════════════════════════════════
#  CATEGORY MANAGEMENT (ADMIN)
# ══════════════════════════════════════════════════════════════

@login_required
def admin_categories_list(request):
    """Custom view for listing all categories."""
    if not request.user.is_staff:
        return render(request, 'admin_custom/access_denied.html', status=403)
    categories = Category.objects.all()

    context = {
        'categories': categories,
        'page_title': 'Categories',
    }
    return render(request, 'admin_custom/categories_list.html', context)


@login_required
def admin_categories_add(request):
    """Custom admin view: add a new category."""
    if not request.user.is_staff:
        return render(request, 'admin_custom/access_denied.html', status=403)
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        from django.utils.text import slugify
        slug = request.POST.get('slug', '').strip() or slugify(name)
        description = request.POST.get('description', '').strip()
        icon = request.POST.get('icon', '📌').strip()

        if not name:
            messages.error(request, 'Category name is required.')
        elif Category.objects.filter(slug=slug).exists():
            messages.error(request, 'A category with this name/slug already exists.')
        else:
            Category.objects.create(name=name, slug=slug, description=description, icon=icon)
            messages.success(request, f'✅ Category "{name}" added successfully!')
            return redirect('store:admin_categories_list')

    context = {
        'page_title': 'Add Category',
    }
    return render(request, 'admin_custom/categories_add.html', context)


@login_required
def admin_categories_edit(request, pk):
    """Custom admin view: edit an existing category."""
    if not request.user.is_staff:
        return render(request, 'admin_custom/access_denied.html', status=403)
    
    category = get_object_or_404(Category, pk=pk)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        slug = request.POST.get('slug', '').strip()
        description = request.POST.get('description', '').strip()
        icon = request.POST.get('icon', '').strip()

        if not name or not slug:
            messages.error(request, 'Category name and slug are required.')
        elif Category.objects.exclude(pk=pk).filter(slug=slug).exists():
            messages.error(request, 'A category with this slug already exists.')
        else:
            category.name = name
            category.slug = slug
            category.description = description
            category.icon = icon
            category.save()
            messages.success(request, f'✅ Category "{name}" updated successfully!')
            return redirect('store:admin_categories_list')

    context = {
        'category': category,
        'page_title': f'Edit Category — {category.name}',
    }
    return render(request, 'admin_custom/categories_edit.html', context)


@login_required
def admin_categories_delete(request, pk):
    """Custom admin view: delete a category."""
    if not request.user.is_staff:
        return render(request, 'admin_custom/access_denied.html', status=403)
    
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        name = category.name
        category.delete()
        messages.success(request, f'🗑️ Category "{name}" deleted.')
    return redirect('store:admin_categories_list')
