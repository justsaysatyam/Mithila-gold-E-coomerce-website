from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='SiteSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('company_name', models.CharField(default='Jay Bn Poultry Farm and Feeding Point', max_length=200)),
                ('address', models.TextField(default='Belhwar, Madhubani, Bihar')),
                ('landmark', models.CharField(default='Near Belhwar Durga Mandir', max_length=200)),
                ('phone_jay', models.CharField(default='7546835444', max_length=20)),
                ('phone_bn', models.CharField(default='7544931599', max_length=20)),
                ('email', models.EmailField(blank=True, default='', max_length=254)),
                ('gst_number', models.CharField(default='10AAQFJ2396C1ZJ', max_length=50)),
                ('tagline', models.CharField(default='भरोसा आपका, क्वालिटी हमारी — Your Trust, Our Quality.', max_length=300)),
                ('maps_embed_url', models.URLField(blank=True, default='https://maps.google.com/maps?q=Belhwar+Durga+Mandir+Madhubani+Bihar&output=embed')),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'verbose_name': 'Site Settings', 'verbose_name_plural': 'Site Settings'},
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(choices=[('medicines', 'Animal Medicines'), ('feed', 'Chick Feed'), ('chicks', 'Healthy Chicks'), ('equipment', 'Poultry Equipment')], max_length=100, unique=True)),
                ('slug', models.SlugField(unique=True)),
                ('icon', models.CharField(default='🐔', max_length=100)),
            ],
            options={'verbose_name_plural': 'Categories', 'ordering': ['name']},
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('stock', models.PositiveIntegerField(default=0)),
                ('image', models.ImageField(blank=True, null=True, upload_to='products/')),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('category', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='products', to='store.category')),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='Farmer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phone', models.CharField(max_length=15, unique=True)),
                ('address', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='farmer_profile', to='auth.user')),
            ],
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('customer_name', models.CharField(max_length=200)),
                ('customer_phone', models.CharField(max_length=15)),
                ('customer_address', models.TextField()),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('processing', 'Processing'), ('shipped', 'Shipped'), ('delivered', 'Delivered'), ('cancelled', 'Cancelled')], default='pending', max_length=20)),
                ('total_amount', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('gst_amount', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('payment_mode', models.CharField(default='Cash', max_length=50)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('farmer', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='orders', to='auth.user')),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_name', models.CharField(max_length=200)),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('unit_price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='store.order')),
                ('product', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='store.product')),
            ],
        ),
        migrations.CreateModel(
            name='SalesRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('customer_name', models.CharField(max_length=200)),
                ('customer_phone', models.CharField(max_length=15)),
                ('customer_address', models.TextField(blank=True)),
                ('total_amount', models.DecimalField(decimal_places=2, max_digits=12)),
                ('gst_amount', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('payment_mode', models.CharField(choices=[('Cash', 'Cash'), ('UPI', 'UPI'), ('Bank Transfer', 'Bank Transfer')], default='Cash', max_length=20)),
                ('date', models.DateField(default=django.utils.timezone.now)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('added_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='auth.user')),
            ],
            options={'ordering': ['-date', '-created_at']},
        ),
        migrations.CreateModel(
            name='SalesItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_name', models.CharField(max_length=200)),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('unit_price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('sales_record', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='store.salesrecord')),
            ],
        ),
        migrations.CreateModel(
            name='PaymentReceipt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('receipt_number', models.CharField(blank=True, max_length=20, unique=True)),
                ('generated_at', models.DateTimeField(auto_now_add=True)),
                ('order', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='receipt', to='store.order')),
                ('sales_record', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='receipt', to='store.salesrecord')),
            ],
            options={'ordering': ['-generated_at']},
        ),
    ]
