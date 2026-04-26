import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'poultry_farm.settings')
django.setup()

from django.contrib.auth.models import User

user = User.objects.filter(username='admin').first()
if user:
    print(f"User: {user.username}")
    print(f"Is Staff: {user.is_staff}")
    print(f"Is Superuser: {user.is_superuser}")
    
    # If not staff, make them staff
    if not user.is_staff:
        user.is_staff = True
        user.save()
        print("Updated user to staff.")
else:
    print("User 'admin' not found.")
