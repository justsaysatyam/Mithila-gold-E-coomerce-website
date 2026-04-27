from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field, HTML
from .models import Farmer, SalesRecord, SalesItem, SiteSettings, Order


class FarmerRegisterForm(UserCreationForm):
    first_name = forms.CharField(max_length=100, required=True, label='First Name')
    last_name = forms.CharField(max_length=100, required=True, label='Last Name')
    email = forms.EmailField(required=False, label='Email (optional)')
    phone = forms.CharField(max_length=15, required=True, label='Phone Number')
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=True, label='Village / Address')

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'username', 'phone', 'address', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column('first_name', css_class='col-md-6'), Column('last_name', css_class='col-md-6')),
            'email',
            'username',
            'phone',
            'address',
            Row(Column('password1', css_class='col-md-6'), Column('password2', css_class='col-md-6')),
            Submit('submit', 'Register as Farmer', css_class='btn btn-success w-100 mt-3')
        )

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            Farmer.objects.create(
                user=user,
                phone=self.cleaned_data['phone'],
                address=self.cleaned_data['address']
            )
        return user


class FarmerLoginForm(forms.Form):
    username = forms.CharField(label='Username / Phone', max_length=150)
    password = forms.CharField(widget=forms.PasswordInput, label='Password')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'username',
            'password',
            Submit('submit', 'Login', css_class='btn btn-warning w-100 mt-3 fw-bold')
        )


class CheckoutForm(forms.ModelForm):
    PAYMENT_CHOICES = [
        ('Cash', 'Cash on Delivery'),
        ('UPI', 'UPI Transfer'),
        ('Bank Transfer', 'Bank Transfer'),
    ]
    payment_mode = forms.ChoiceField(choices=PAYMENT_CHOICES, widget=forms.RadioSelect)

    class Meta:
        model = Order
        fields = ['customer_name', 'customer_phone', 'customer_address', 'payment_mode', 'notes']
        widgets = {
            'customer_address': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Any special instructions?'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column('customer_name', css_class='col-md-6'), Column('customer_phone', css_class='col-md-6')),
            'customer_address',
            'payment_mode',
            'notes',
            Submit('submit', 'Place Order 🛒', css_class='btn btn-warning w-100 mt-3 fw-bold fs-5')
        )


class SalesRecordAdminForm(forms.ModelForm):
    class Meta:
        model = SalesRecord
        fields = '__all__'


class SalesItemInlineFormSet(forms.BaseInlineFormSet):
    pass


class SiteSettingsForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        fields = '__all__'
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
            'tagline': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'company_name',
            'tagline',
            'gst_number',
            Row(Column('email', css_class='col-md-6'),
                Column('phone_primary', css_class='col-md-3'),
                Column('phone_secondary', css_class='col-md-3')),
            'address',
            'landmark',
            'maps_embed_url',
            'promo_video',
            Submit('submit', 'Save Settings', css_class='btn btn-success mt-3')
        )
