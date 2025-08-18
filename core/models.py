from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username}'s profile"


class Listing(models.Model):
    RENTAL_CHOICES = [
        ('car', 'Car'),
        ('bike', 'Bike'),
        ('homestay', 'Homestay'),
    ]
    provider = models.ForeignKey(Profile, on_delete=models.CASCADE)
    rental_type = models.CharField(max_length=10, choices=RENTAL_CHOICES)
    title = models.CharField(max_length=100)
    description = models.TextField()
    price_per_day = models.DecimalField(max_digits=10, decimal_places=2)
    available = models.BooleanField(default=True)
    image = models.ImageField(upload_to='listing_images/', null=True, blank=True)

    def __str__(self):
        return self.title

class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    approved = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.listing.title} booked by {self.user.username}'

class BikeStation(models.Model):
    service_provider = models.ForeignKey('ServiceProvider', on_delete=models.CASCADE)  # NEW
    name = models.CharField(max_length=100)
    longitude = models.CharField(max_length=100)
    latitude = models.CharField(max_length=100)
    location = models.CharField(max_length=255)
    image = models.ImageField(upload_to='bike_stations/', null=True, blank=True)

    def __str__(self):
        return self.name

class Bike(models.Model):
    STATION_CHOICES = [
        ('scooter', 'Scooter'),
        ('offroad', 'Offroad Bike'),
        ('sports', 'Sports Bike'),
        ('normal', 'Normal Bike'),
    ]

    service_provider = models.ForeignKey('ServiceProvider', on_delete=models.CASCADE)
    station = models.ForeignKey('BikeStation', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    bike_type = models.CharField(max_length=100, choices=STATION_CHOICES)
    daily_rent_price = models.DecimalField(max_digits=8, decimal_places=2)
    image = models.ImageField(upload_to='bikes/', blank=True, null=True)

    def __str__(self):
        return self.name


class CarStation(models.Model):
    service_provider = models.ForeignKey('ServiceProvider', on_delete=models.CASCADE)  # NEW
    name = models.CharField(max_length=100)
    longitude = models.CharField(max_length=100)
    latitude = models.CharField(max_length=100)
    location = models.CharField(max_length=255)
    image = models.ImageField(upload_to='car_stations/', null=True, blank=True)

    def __str__(self):
        return self.name

class Car(models.Model):
    CAR_TYPES = [
        ('suv', 'SUV Car'),
        ('sedan', 'Sedan Car'),
        ('compact', 'Compact Car'),
        ('sports', 'Sports Car')
    ]
    station = models.ForeignKey(CarStation, on_delete=models.CASCADE)
    service_provider = models.ForeignKey('ServiceProvider', on_delete=models.CASCADE)  # NEW
    name = models.CharField(max_length=100)
    car_type = models.CharField(max_length=100, choices=CAR_TYPES)
    daily_rent_price = models.DecimalField(max_digits=8, decimal_places=2)
    image = models.ImageField(upload_to='cars/', blank=True, null=True)

    def __str__(self):
        return self.name

class Homestay(models.Model):
    PROPERTY_TYPES = [
        ('apartment', 'Apartment'),
        ('house', 'House'),
        ('flat', 'Flat')
    ]
    service_provider = models.ForeignKey('ServiceProvider', on_delete=models.CASCADE)  # NEW
    name = models.CharField(max_length=100)
    property_type = models.CharField(max_length=100, choices=PROPERTY_TYPES)
    location = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)
    image = models.ImageField(upload_to='homestays/', blank=True, null=True)

    def __str__(self):
        return self.name

class Room(models.Model):
    ROOM_TYPES = [
        ('single', 'Single Room'),
        ('double', 'Double Room'),
        ('luxury', 'Luxury Room')
    ]
    homestay = models.ForeignKey(Homestay, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    room_type = models.CharField(max_length=100, choices=ROOM_TYPES)
    night_rate = models.DecimalField(max_digits=8, decimal_places=2)
    description = models.TextField()
    image = models.ImageField(upload_to='rooms/', null=True, blank=True)

    def __str__(self):
        return self.name   

class BookingBike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    bike_station = models.ForeignKey('BikeStation', on_delete=models.CASCADE)
    bike = models.ForeignKey('Bike', on_delete=models.CASCADE)
    rent_date = models.DateField()
    return_date = models.DateField()
    status = models.CharField(max_length=20, default='Completed')
    rent_amount = models.DecimalField(max_digits=10, decimal_places=2)

class BookingCar(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    car_station = models.ForeignKey('CarStation', on_delete=models.CASCADE)
    car = models.ForeignKey('Car', on_delete=models.CASCADE)
    rent_date = models.DateField()
    return_date = models.DateField()
    status = models.CharField(max_length=20, default='Completed')
    rent_amount = models.DecimalField(max_digits=10, decimal_places=2)

class BookingHomestay(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, null=True, blank=True)
    check_in = models.DateField()
    check_out = models.DateField()
    status = models.CharField(max_length=20, default='Completed')
    rent_amount = models.DecimalField(max_digits=10, decimal_places=2)


class UserFeedback(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    feedback = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    bike_station = models.ForeignKey('BikeStation', null=True, blank=True, on_delete=models.CASCADE)
    car_station = models.ForeignKey('CarStation', null=True, blank=True, on_delete=models.CASCADE)
    homestay = models.ForeignKey('Homestay', null=True, blank=True, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user.username} - {self.feedback[:30]}"


class HomestayClick(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    homestay = models.ForeignKey('Homestay', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

class CarClick(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    car = models.ForeignKey('Car', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

class BikeClick(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    bike = models.ForeignKey('Bike', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

class ServiceProvider(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    business_name = models.CharField(max_length=100)
    contact_number = models.CharField(max_length=15)
    approved = models.BooleanField(default=False)  
    rejected = models.BooleanField(default=False)

    def __str__(self):
        return self.business_name
