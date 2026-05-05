"""
Management command: python manage.py seed_data
Seeds the database with initial categories and sample products for Jay Bn Poultry Farm.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from store.models import Category, Product, SiteSettings


class Command(BaseCommand):
    help = 'Seed the database with initial categories, sample products, and site settings.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('Seeding Mithila White Gold data...'))

        # ── Site Settings (singleton) ────────────────────────────
        settings, created = SiteSettings.objects.get_or_create(pk=1)
        if created:
            self.stdout.write('  [+] Created SiteSettings')
        else:
            self.stdout.write('  [-] SiteSettings already exists, skipping.')

        # ── Categories ───────────────────────────────────────────
        categories_data = [
            {'name': 'Roasted Makhana', 'slug': 'roasted', 'icon': '🔥'},
            {'name': 'Plain Makhana',      'slug': 'plain',      'icon': '⚪'},
            {'name': 'Flavoured Makhana',    'slug': 'flavoured',    'icon': '🌶️'},
            {'name': 'Gift Packs', 'slug': 'gift', 'icon': '🎁'},
        ]
        categories = {}
        for cat_data in categories_data:
            cat, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={'slug': cat_data['slug'], 'icon': cat_data['icon']}
            )
            categories[cat_data['name']] = cat
            status = '[+] Created' if created else '[-] Already exists'
            self.stdout.write(f'  {status}: Category "{cat.name}"')

        # ── Products ─────────────────────────────────────────────
        products_data = [
            # Removed old poultry products
        ]

        product_count = 0
        for pdata in products_data:
            cat = categories.get(pdata.pop('category'))
            prod, created = Product.objects.get_or_create(
                name=pdata['name'],
                defaults={**pdata, 'category': cat}
            )
            if created:
                product_count += 1
                self.stdout.write(f"  [+] Created product: {prod.name}")
            else:
                self.stdout.write(f"  – Product already exists: {prod.name}")

        # ── Superuser ─────────────────────────────────────────────
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@jaybnjha.com', 'admin@123')
            self.stdout.write(self.style.SUCCESS('\n  [+] Superuser created: admin / admin@123'))
        else:
            self.stdout.write('\n  [-] Superuser "admin" already exists.')

        self.stdout.write(self.style.SUCCESS(
            f'\nSeed complete! {product_count} new products added across 4 categories.\n'
            '🌐 Run: python manage.py runserver\n'
            '🔑 Admin login: admin / admin@123\n'
        ))
