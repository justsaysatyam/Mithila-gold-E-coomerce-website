import os
import django
from django.conf import settings
from django.template import loader

# Setup django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'poultry_farm.settings')
django.setup()

from store.models import SiteSettings, Category, Product

def check_homepage():
    # Mock some data that context processors expect
    categories = Category.objects.all()
    site_settings = SiteSettings.get_settings()
    
    print(f"PROMO VIDEO: {site_settings.promo_video}")
    if site_settings.promo_video:
        print(f"PROMO VIDEO URL: {site_settings.promo_video.url}")
    
    # Render the template
    t = loader.get_template('home.html')
    # Mocking a basic context
    context = {
        'site_settings': site_settings,
        'categories': categories,
        'featured_products': Product.objects.all()[:8],
    }
    rendered = t.render(context)
    
    if 'ADVERTISEMENT VIDEO' in rendered:
        print("VIDEO SECTION FOUND IN RENDERED HTML")
        if 'video' in rendered:
            print("VIDEO TAG FOUND")
            # Extract src
            import re
            match = re.search(r'<video src="([^"]+)"', rendered)
            if match:
                print(f"VIDEO SRC: {match.group(1)}")
            else:
                print("VIDEO SRC NOT FOUND")
    else:
        print("VIDEO SECTION NOT FOUND IN RENDERED HTML")

if __name__ == "__main__":
    check_homepage()
