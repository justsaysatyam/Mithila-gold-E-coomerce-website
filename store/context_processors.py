from .models import SiteSettings, Category


def site_settings(request):
    """Inject site settings into all templates."""
    return {'site_settings': SiteSettings.get_settings()}


def cart_count(request):
    """Inject cart item count into all templates."""
    cart = request.session.get('cart', {})
    count = sum(item.get('quantity', 0) for item in cart.values())
    return {'cart_count': count}


def categories_processor(request):
    """Inject categories into all templates for the navbar."""
    return {'categories': Category.objects.all()}
