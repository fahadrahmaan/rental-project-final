from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Profile, Bike, BikeStation, Car, CarStation, Room, Homestay
from .models import ServiceProvider

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(label='Phone Number', max_length=20, required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'phone_number']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email is already in use.")
        return email

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if not phone.isdigit():
            raise forms.ValidationError("Phone number must contain only digits.")
        if len(phone) != 10:
            raise forms.ValidationError("Phone number must be exactly 10 digits.")
        return phone

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            # Save phone number to Profile
            Profile.objects.create(user=user, phone_number=self.cleaned_data['phone_number'])
        return user

class LoginForm(forms.Form):
    username = forms.CharField(label='Username')
    password = forms.CharField(label='Password', widget=forms.PasswordInput)

class BikeForm(forms.ModelForm):
    class Meta:
        model = Bike
        fields = ['station', 'name', 'bike_type', 'daily_rent_price', 'image']
        widgets = {
            'bike_type': forms.Select(choices=[
                ('scooter', 'Scooter'),
                ('offroad', 'Offroad Bike'),
                ('sports', 'Sports Bike'),
                ('normal', 'Normal Bike')
            ])
        }

class BikeStationForm(forms.ModelForm):
    class Meta:
        model = BikeStation
        fields = ['name', 'longitude', 'latitude', 'location', 'image']

class CarForm(forms.ModelForm):
    class Meta:
        model = Car
        fields = ['station', 'name', 'car_type', 'daily_rent_price', 'image']
        widgets = {
            'car_type': forms.Select(choices=[
                ('suv', 'SUV Car'),
                ('sedan', 'Sedan Car'),
                ('compact', 'Compact Car'),
                ('sports', 'Sports Car')
            ])
        }

class CarStationForm(forms.ModelForm):
    class Meta:
        model = CarStation
        fields = ['name', 'longitude', 'latitude', 'location', 'image']

class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['homestay', 'name', 'room_type', 'night_rate', 'description', 'image']
        widgets = {
            'room_type': forms.Select(choices=[
                ('single', 'Single Room'),
                ('double', 'Double Room'),
                ('luxury', 'Luxury Room')
            ])
        }

class HomestayForm(forms.ModelForm):
    class Meta:
        model = Homestay
        fields = ['name', 'property_type', 'location', 'phone_number', 'image']
        widgets = {
            'property_type': forms.Select(choices=[
                ('apartment', 'Apartment'),
                ('house', 'House'),
                ('flat', 'Flat')
            ])
        }  

class ServiceProviderUpdateForm(forms.ModelForm):
    class Meta:
        model = ServiceProvider
        fields = ['business_name', 'contact_number']

class CustomerUpdateForm(forms.ModelForm):
    phone_number = forms.CharField(label='Phone Number', max_length=20)

    class Meta:
        model = User
        fields = ['email']

    def __init__(self, *args, **kwargs):
        profile_instance = kwargs.pop('profile_instance', None)
        super().__init__(*args, **kwargs)

        if profile_instance:
            self.fields['phone_number'].initial = profile_instance.phone_number

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            profile = user.profile
            profile.phone_number = self.cleaned_data['phone_number']
            profile.save()
        return user


