import os
import django
import sys
from pathlib import Path

# Setup Django environment
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'poultry_farm.settings')
django.setup()

from django.core.files import File
from store.models import Product, ProductImage, SiteSettings, DynamicMedia, upload_to_db

def migrate_media():
    print("Starting Media Migration to Database...")

    # 1. Migrate SiteSettings
    print("\n--- Migrating SiteSettings ---")
    settings = SiteSettings.get_settings()
    if settings.promo_video and not settings.promo_video_db:
        print(f"Migrating promo video: {settings.promo_video.name}")
        media = upload_to_db(settings.promo_video)
        if media:
            settings.promo_video_db = media
            settings.save()
            print("OK: Promo video migrated.")
    else:
        print("Skipped SiteSettings (already migrated or no file).")

    # 2. Migrate Products
    print("\n--- Migrating Products ---")
    products = Product.objects.all()
    for p in products:
        updated = False
        if p.image and not p.image_db:
            print(f"Migrating image for {p.name}: {p.image.name}")
            media = upload_to_db(p.image)
            if media:
                p.image_db = media
                updated = True
        
        if p.video_file and not p.video_db:
            print(f"Migrating video for {p.name}: {p.video_file.name}")
            media = upload_to_db(p.video_file)
            if media:
                p.video_db = media
                updated = True
        
        if updated:
            p.save()
            print(f"OK: Product {p.name} updated.")
        else:
            print(f"Skipped Product {p.name}.")

    # 3. Migrate ProductImages (Gallery)
    print("\n--- Migrating Gallery Images ---")
    gallery_images = ProductImage.objects.all()
    for gi in gallery_images:
        if gi.image and not gi.image_db:
            print(f"Migrating gallery image for {gi.product.name}: {gi.image.name}")
            media = upload_to_db(gi.image)
            if media:
                gi.image_db = media
                gi.save()
                print("OK: Gallery image migrated.")
        else:
            print(f"Skipped gallery image for {gi.product.name}.")

    print("\nMigration Completed!")

if __name__ == "__main__":
    migrate_media()
