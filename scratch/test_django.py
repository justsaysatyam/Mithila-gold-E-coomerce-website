import os
import django
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'poultry_farm.settings')
django.setup()

from store.models import Product
print(f"Django setup OK. Products count: {Product.objects.count()}")
