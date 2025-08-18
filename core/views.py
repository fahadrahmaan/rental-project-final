from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .forms import UserRegisterForm, LoginForm, BikeForm, BikeStationForm, CarForm, CarStationForm, RoomForm, HomestayForm
from .models import Profile, Bike, BikeStation, Car, CarStation, Room, Homestay, BookingBike, BookingCar, BookingHomestay, UserFeedback, Booking
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from datetime import datetime, timedelta
from django.utils import timezone
from decimal import Decimal
from django.urls import reverse
from django.db.models import Q
from .utils import get_similar_homestays
import random
from .models import HomestayClick
from .models import CarClick, BikeClick
from django.utils.timezone import now
from .models import ServiceProvider  
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import logout
from django.contrib.auth.decorators import user_passes_test
from .forms import ServiceProviderUpdateForm
from .forms import CustomerUpdateForm
from django.db.models import Sum
from decimal import Decimal

def home(request):
    return render(request, 'core/home.html')

def about(request):
    return render(request, 'core/about.html')

def services(request):
    return render(request, 'core/services.html')

def contact(request):
    return render(request, 'core/contact.html')

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=True)
            user.is_superuser = False
            user.is_staff = False
            user.save()
            # Profile is already created inside form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! Please log in.')
            return redirect('login')
        else:
            messages.error(request, 'Error creating account. Please check the form below.')
    else:
        form = UserRegisterForm()
    return render(request, 'core/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)

            if user:
                login(request, user)

                if user.is_superuser:
                    return redirect('admin_dashboard')

                elif hasattr(user, 'serviceprovider'):
                    provider = user.serviceprovider

                    if provider.rejected:
                        logout(request)
                        messages.error(request, "Your provider registration was rejected by admin.")
                        return redirect('login')

                    if not provider.approved:
                        logout(request)
                        messages.warning(request, "Your provider account is pending admin approval.")
                        return redirect('login')

                    return redirect('provider_dashboard')

                # Normal customer
                return redirect('customer_dashboard')
            else:
                messages.error(request, 'Invalid credentials')
    else:
        form = LoginForm()
    
    return render(request, 'core/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def admin_dashboard(request):
    return render(request, 'core/admin_dashboard.html')

@login_required
def customer_dashboard(request):
    user = request.user

    # ✅ HOMESTAYS
    homestay_clicks = HomestayClick.objects.filter(user=user).order_by('-timestamp').values_list('homestay_id', flat=True)
    homestay_bookings = BookingHomestay.objects.filter(user=user).order_by('-check_in').values_list('room__homestay_id', flat=True)
    homestay_ids = list(dict.fromkeys(list(homestay_clicks) + list(homestay_bookings)))[:3]

    if homestay_ids:
        suggested_homestays = [{'item': hs, 'tag': '🔥 Based on your activity'} for hs in Homestay.objects.filter(id__in=homestay_ids)]
    else:
        all_homestays = list(Homestay.objects.all())
        fallback = random.sample(all_homestays, min(3, len(all_homestays)))
        suggested_homestays = [{'item': hs, 'tag': '✨ Popular pick'} for hs in fallback]

    # ✅ CARS
    car_clicks = CarClick.objects.filter(user=user).order_by('-timestamp').values_list('car_id', flat=True)
    car_bookings = BookingCar.objects.filter(user=user).order_by('-rent_date').values_list('car_id', flat=True)
    car_ids = list(dict.fromkeys(list(car_clicks) + list(car_bookings)))[:3]

    if car_ids:
        suggested_cars = [{'item': car, 'tag': '🔥 Based on your activity'} for car in Car.objects.filter(id__in=car_ids)]
    else:
        all_cars = list(Car.objects.all())
        fallback = random.sample(all_cars, min(3, len(all_cars)))
        suggested_cars = [{'item': car, 'tag': '✨ Popular pick'} for car in fallback]

    # ✅ BIKES
    bike_clicks = BikeClick.objects.filter(user=user).order_by('-timestamp').values_list('bike_id', flat=True)
    bike_bookings = BookingBike.objects.filter(user=user).order_by('-rent_date').values_list('bike_id', flat=True)
    bike_ids = list(dict.fromkeys(list(bike_clicks) + list(bike_bookings)))[:3]

    if bike_ids:
        suggested_bikes = [{'item': bike, 'tag': '🔥 Based on your activity'} for bike in Bike.objects.filter(id__in=bike_ids)]
    else:
        all_bikes = list(Bike.objects.all())
        fallback = random.sample(all_bikes, min(3, len(all_bikes)))
        suggested_bikes = [{'item': bike, 'tag': '✨ Popular pick'} for bike in fallback]

    return render(request, 'core/customer_dashboard.html', {
        'suggested_homestays': suggested_homestays,
        'suggested_cars': suggested_cars,
        'suggested_bikes': suggested_bikes,
    })

@login_required
def admin_home(request):
    if not request.user.is_superuser:
        return redirect('home')
    return render(request, 'core/admin_home.html')

@login_required
def user_details(request):
    provider_users = User.objects.filter(serviceprovider__isnull=False).order_by('date_joined')
    admin_users = User.objects.filter(is_superuser=True).order_by('date_joined')
    customer_users = User.objects.exclude(
        id__in=provider_users
    ).exclude(
        is_superuser=True
    ).order_by('date_joined')

    return render(request, 'core/user_details.html', {
        'customer_users': customer_users,
        'provider_users': provider_users,
        'admin_users': admin_users,
    })

@login_required
def user_feedback(request):
    feedback_list = UserFeedback.objects.select_related('user').order_by('-submitted_at')
    return render(request, 'core/user_feedback.html', {'feedback_list': feedback_list})

# Homestay listing and booking
@login_required
def homestay_list(request):
    homestays = Homestay.objects.all()
    return render(request, 'core/homestay_list.html', {'homestays': homestays})

@login_required
def homestay_rooms(request, homestay_id):
    homestay = get_object_or_404(Homestay, id=homestay_id)
    rooms = Room.objects.filter(homestay=homestay)

    # ✅ Log the user's view (click)
    HomestayClick.objects.create(user=request.user, homestay=homestay)

    # 🧠 Keep using your similarity logic
    recommended = get_similar_homestays(homestay_id)

    return render(request, 'core/homestay_rooms.html', {
        'homestay': homestay,
        'rooms': rooms,
        'recommended_homestays': recommended,
    })

@login_required
def homestay_booking(request, room_id):
    room = get_object_or_404(Room, id=room_id)

    if request.method == 'POST':
        number_of_nights = int(request.POST.get('number_of_nights'))
        check_in_day = request.POST.get('check_in_day')

        from datetime import datetime, timedelta
        check_in_date = datetime.strptime(check_in_day, '%Y-%m-%d').date()
        check_out_date = check_in_date + timedelta(days=number_of_nights)

        # 🛑 Check for booking conflicts
        conflict = BookingHomestay.objects.filter(
            room=room,
            check_in__lt=check_out_date,
            check_out__gt=check_in_date,
        ).exists()

        if conflict:
            from django.contrib import messages
            messages.error(request, "This room is already booked for the selected dates.")
            return render(request, 'core/homestay_booking.html', {'room': room})

        total_rent = room.night_rate * number_of_nights

        # ✅ Save to session
        request.session['booking_details'] = {
            'room_id': room.id,
            'room_type': room.room_type,
            'rent_per_night': float(room.night_rate),
            'check_in_day': check_in_day,
            'check_out_day': str(check_out_date),
            'total_rent': float(total_rent),
            'number_of_nights': number_of_nights,
        }

        return redirect('homestay_booking_confirmation')

    return render(request, 'core/homestay_booking.html', {'room': room})

@login_required
def homestay_booking_confirmation(request):
    booking_details = request.session.get('booking_details')
    if not booking_details:
        return redirect('homestay_list')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'cancel':
            del request.session['booking_details']
            messages.info(request, "Booking was cancelled.")
            return redirect('homestay_list')

        elif action == 'confirm':
            return redirect('homestay_payment')  # ✅ Just redirect to payment

    return render(request, 'core/homestay_booking_confirmation.html', {
        'booking': booking_details
    })

@login_required
def homestay_payment(request):
    booking_details = request.session.get('booking_details')

    if not booking_details:
        return redirect('homestay_list')

    if request.method == 'POST':
        card_number = request.POST.get('card_number')
        expiry_date = request.POST.get('expiry_date')
        cvv = request.POST.get('cvv')

        if not card_number or not expiry_date or not cvv:
            return render(request, 'core/payment.html', {
                'homestay_name': Room.objects.get(id=booking_details['room_id']).homestay.name,
                'room_type': booking_details['room_type'],
                'check_in': booking_details['check_in_day'],
                'check_out': booking_details['check_out_day'],
                'total_rent': booking_details['total_rent'],
                'error': 'Please fill in all fields.'
            })

        # ✅ Booking is created *after* successful payment
        room = get_object_or_404(Room, id=booking_details['room_id'])
        BookingHomestay.objects.create(
            user=request.user,
            room=room,
            check_in=booking_details['check_in_day'],
            check_out=booking_details['check_out_day'],
            rent_amount=booking_details['total_rent'],
            status='Completed'
        )

        del request.session['booking_details']
        return redirect(reverse('booking_success') + '?type=homestay')

    return render(request, 'core/payment.html', {
        'homestay_name': Room.objects.get(id=booking_details['room_id']).homestay.name,
        'room_type': booking_details['room_type'],
        'check_in': booking_details['check_in_day'],
        'check_out': booking_details['check_out_day'],
        'total_rent': booking_details['total_rent'],
    })

@login_required
def booking_success(request):
    booking_type = request.GET.get('type', 'homestay')  # could be 'homestay', 'bike', 'car', or empty
    return render(request, 'core/booking_success.html', {'booking_type': booking_type})

# 1. Bike Station List View
@login_required
def bike_station_list(request):
    stations = BikeStation.objects.all()
    return render(request, 'core/bike_station_list.html', {'bike_stations': stations})

# 2. Bike List View
@login_required
def bike_list(request, station_id):
    station = get_object_or_404(BikeStation, id=station_id)
    bikes = Bike.objects.filter(station=station)

    # ✅ Bikes from the same location but other stations
    recommended_bikes = Bike.objects.filter(
        station__location=station.location
    ).exclude(station=station)

    # ✅ Fallback to 3 random bikes if none from the same location
    if not recommended_bikes.exists():
        recommended_bikes = Bike.objects.exclude(station=station).order_by('?')[:3]

    return render(request, 'core/bike_list.html', {
        'bikes': bikes,
        'station': station,
        'recommended_bikes': recommended_bikes,
    })

def is_bike_available(bike, rent_date, return_date):
    conflicts = BookingBike.objects.filter(
        bike=bike,
        status="Completed",
        rent_date__lte=return_date,
        return_date__gte=rent_date,
    )
    return not conflicts.exists()

# 1. Bike Rent View (Step 1: Select Dates)
@login_required
def rent_bike(request, station_id, bike_id):
    station = get_object_or_404(BikeStation, id=station_id)
    bike = get_object_or_404(Bike, id=bike_id, station=station)
    BikeClick.objects.update_or_create(
    user=request.user,
    bike_id=bike_id,
    defaults={'timestamp': timezone.now()}
    )

    if request.method == "POST":
        rent_date = request.POST.get("rent_date")
        return_date = request.POST.get("return_date")

        if rent_date and return_date:
            try:
                rd = datetime.strptime(rent_date, "%Y-%m-%d").date()
                rt = datetime.strptime(return_date, "%Y-%m-%d").date()
            except ValueError:
                messages.error(request, "Invalid date format.")
                return render(request, 'core/rent_bike.html', {'bike': bike})

            if rt < rd:
                messages.error(request, "Return date cannot be before rent date.")
                return render(request, 'core/rent_bike.html', {'bike': bike})

            if not is_bike_available(bike, rd, rt):
                messages.error(request, "This bike is already booked for the selected dates.")
                return render(request, 'core/rent_bike.html', {'bike': bike})

            days = (rt - rd).days + 1
            total = days * bike.daily_rent_price

            request.session['bike_booking_details'] = {
                'bike_id': bike.id,
                'station_id': station.id,
                'rent_date': rent_date,
                'return_date': return_date,
                'rent_amount': float(total)
            }

            return redirect('bike_booking_confirmation')

    return render(request, 'core/rent_bike.html', {'bike': bike})

# 2. Confirmation View
@login_required
def bike_booking_confirmation(request):
    booking_details = request.session.get('bike_booking_details')
    if not booking_details:
        return redirect('bike_station_list')

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "confirm":
            return redirect('bike_payment_form')
        elif action == "cancel":
            request.session.pop('bike_booking_details', None)
            messages.info(request, "Bike booking cancelled.")
            return redirect('bike_station_list')

    bike_id = booking_details.get('bike_id')
    station_id = booking_details.get('station_id')  # update key to match your session data

    if not bike_id or not station_id:
        messages.error(request, "Incomplete booking data.")
        return redirect('bike_station_list')

    try:
        bike = Bike.objects.get(id=bike_id)
        station = BikeStation.objects.get(id=station_id)
    except (Bike.DoesNotExist, BikeStation.DoesNotExist):
        messages.error(request, "Invalid booking data.")
        return redirect('bike_station_list')

    booking = {
        'bike': bike,
        'bike_station': station,
        'rent_date': booking_details['rent_date'],
        'return_date': booking_details['return_date'],
        'rent_amount': booking_details['rent_amount'],
    }

    return render(request, 'core/bike_booking_confirmation.html', {'booking': booking})

# 3. Payment View
@login_required
def bike_payment(request):
    booking_details = request.session.get('bike_booking_details')
    if not booking_details:
        return redirect('bike_station_list')

    booking_date = timezone.now().date()

    if request.method == "POST":
        card_number = request.POST.get("card_number")
        expiry_date = request.POST.get("expiry_date")
        cvv = request.POST.get("cvv")

        if card_number and expiry_date and cvv:
            # Finalize the booking
            bike = get_object_or_404(Bike, id=booking_details['bike_id'])
            station = get_object_or_404(BikeStation, id=booking_details['station_id'])

            booking = BookingBike.objects.create(
                user=request.user,
                bike=bike,
                bike_station=station,
                rent_date=booking_details['rent_date'],
                return_date=booking_details['return_date'],
                rent_amount=booking_details['rent_amount'],
                status='Completed'
            )

            request.session.pop('bike_booking_details', None)
            return redirect(reverse('booking_success') + '?type=bike')

        else:
            error = "Please enter all payment details."
            return render(request, 'core/payment.html', {
                'bike_station': booking_details['station_id'],
                'bike_name': booking_details['bike_id'],
                'rent_date': booking_details['rent_date'],
                'return_date': booking_details['return_date'],
                'booking_date': booking_date,
                'error': error
            })

    return render(request, 'core/payment.html', {
        'bike_station': booking_details['station_id'],
        'bike_name': booking_details['bike_id'],
        'rent_date': booking_details['rent_date'],
        'return_date': booking_details['return_date'],
        'booking_date': booking_date
    })

# 1. Car Station List View
@login_required
def car_station_list(request):
    stations = CarStation.objects.all()
    return render(request, 'core/car_station_list.html', {'car_stations': stations})

# 2. Car List View
@login_required
def car_list(request, station_id):
    station = get_object_or_404(CarStation, id=station_id)
    cars = Car.objects.filter(station=station)

    # ✅ Cars from same location but other stations
    recommended_cars = Car.objects.filter(
        station__location=station.location
    ).exclude(station=station)

    # ✅ Fallback to 3 random cars (excluding current station)
    if not recommended_cars.exists():
        recommended_cars = Car.objects.exclude(station=station).order_by('?')[:3]

    return render(request, 'core/car_list.html', {
        'cars': cars,
        'station': station,
        'recommended_cars': recommended_cars,
    })

# 3. Car Rent View (Date Selection)
@login_required
def rent_car(request, station_id, car_id):
    station = get_object_or_404(CarStation, id=station_id)
    car = get_object_or_404(Car, id=car_id, station=station)
    CarClick.objects.update_or_create(
    user=request.user,
    car_id=car_id,
    defaults={'timestamp': timezone.now()}
    )

    if request.method == "POST":
        rent_date = request.POST.get("rent_date")
        return_date = request.POST.get("return_date")

        if rent_date and return_date:
            try:
                rd = datetime.strptime(rent_date, "%Y-%m-%d").date()
                rt = datetime.strptime(return_date, "%Y-%m-%d").date()
            except ValueError:
                messages.error(request, "Invalid date format.")
                return render(request, 'core/rent_car.html', {'car': car})

            if rt < rd:
                messages.error(request, "Return date cannot be before rent date.")
                return render(request, 'core/rent_car.html', {'car': car})

            # ❌ Check conflicts only with 'Completed' bookings
            if not is_car_available(car, rd, rt):
                messages.error(request, "This car is already booked for the selected dates.")
                return render(request, 'core/rent_car.html', {'car': car})

            # ✅ No booking created yet – just store in session
            days = (rt - rd).days + 1
            total = days * car.daily_rent_price

            request.session['car_booking_details'] = {
                'car_id': car.id,
                'station_id': station.id,
                'rent_date': rent_date,
                'return_date': return_date,
                'rent_amount': float(total)
            }

            return redirect('car_booking_confirmation')

    return render(request, 'core/rent_car.html', {'car': car})

def is_car_available(car, rent_date, return_date):
    conflicts = BookingCar.objects.filter(
        car=car,
        status="Completed",
        rent_date__lte=return_date,
        return_date__gte=rent_date,
    )
    return not conflicts.exists()

# 4. Booking Confirmation View
@login_required
def car_booking_confirmation(request):
    booking_details = request.session.get('car_booking_details')
    if not booking_details:
        return redirect('car_station_list')

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "confirm":
            return redirect('car_payment_form')
        elif action == "cancel":
            request.session.pop('car_booking_details', None)
            messages.info(request, "Booking cancelled.")
            return redirect('car_station_list')

    car_id = booking_details.get('car_id')
    station_id = booking_details.get('station_id')  # update to match your session key

    if not car_id or not station_id:
        messages.error(request, "Incomplete booking data.")
        return redirect('car_station_list')

    try:
        car = Car.objects.get(id=car_id)
        station = CarStation.objects.get(id=station_id)
    except (Car.DoesNotExist, CarStation.DoesNotExist):
        messages.error(request, "Invalid booking data.")
        return redirect('car_station_list')

    booking = {
        'car': car,
        'car_station': station,
        'rent_date': booking_details['rent_date'],
        'return_date': booking_details['return_date'],
        'rent_amount': booking_details['rent_amount'],
    }

    return render(request, 'core/car_booking_confirmation.html', {'booking': booking})

# 6. Payment Form View
@login_required
def car_payment_form(request):
    booking_details = request.session.get('car_booking_details')
    if not booking_details:
        return redirect('car_station_list')

    if request.method == "POST":
        card_number = request.POST.get("card_number")
        expiry_date = request.POST.get("expiry_date")
        cvv = request.POST.get("cvv")

        if card_number and expiry_date and cvv:
            # Create booking
            car = get_object_or_404(Car, id=booking_details['car_id'])
            station = get_object_or_404(CarStation, id=booking_details['station_id'])

            booking = BookingCar.objects.create(
                user=request.user,
                car=car,
                car_station=station,
                rent_date=booking_details['rent_date'],
                return_date=booking_details['return_date'],
                rent_amount=booking_details['rent_amount'],
                status='Completed'
            )

            # Clear session
            request.session.pop('car_booking_details', None)

            return redirect(reverse('booking_success') + '?type=car')
        else:
            return render(request, 'core/payment.html', {
                'car_name': booking_details.get('car_name', 'Car'),
                'rent_date': booking_details['rent_date'],
                'return_date': booking_details['return_date'],
                'error': 'Please enter all payment details.'
            })

    return render(request, 'core/payment.html', {
        'car_name': booking_details.get('car_name', 'Car'),
        'rent_date': booking_details['rent_date'],
        'return_date': booking_details['return_date'],
    })

@login_required
def booking_success(request):
    booking_type = request.GET.get('type', 'car')  # 'bike', 'car', or 'homestay'
    return render(request, 'core/booking_success.html', {'booking_type': booking_type})

@login_required
def booking_history(request):
    user = request.user
    bike_bookings = BookingBike.objects.filter(user=user)
    car_bookings = BookingCar.objects.filter(user=user)
    homestay_bookings = BookingHomestay.objects.filter(user=user)

    return render(request, 'core/booking_history.html', {
        'bike_bookings': bike_bookings,
        'car_bookings': car_bookings,
        'homestay_bookings': homestay_bookings,
    })

@login_required
def feedback(request):
    if request.method == 'POST':
        booking_type = request.POST.get('booking_type')
        booking_id = request.POST.get('booking_id')
        message = request.POST.get('message')

        feedback_data = {
            'user': request.user,
            'feedback': message
        }

        try:
            if booking_type == 'bike':
                booking = BookingBike.objects.get(id=booking_id, user=request.user)
                feedback_data['bike_station'] = booking.bike_station

            elif booking_type == 'car':
                booking = BookingCar.objects.get(id=booking_id, user=request.user)
                feedback_data['car_station'] = booking.car_station

            elif booking_type == 'homestay':
                booking = BookingHomestay.objects.get(id=booking_id, user=request.user)
                feedback_data['homestay'] = booking.room.homestay

            UserFeedback.objects.create(**feedback_data)
            messages.success(request, "Thank you for your feedback!", extra_tags='feedback')

        except Exception as e:
            messages.error(request, f"Error submitting feedback: {str(e)}", extra_tags='feedback')

        return redirect('feedback')

    completed_bike_bookings = BookingBike.objects.filter(user=request.user, status='Completed')
    completed_car_bookings = BookingCar.objects.filter(user=request.user, status='Completed')
    completed_homestay_bookings = BookingHomestay.objects.filter(user=request.user, status='Completed')

    context = {
        'completed_bike_bookings': completed_bike_bookings,
        'completed_car_bookings': completed_car_bookings,
        'completed_homestay_bookings': completed_homestay_bookings,
    }

    return render(request, 'core/feedback.html', context)

def service_provider_register(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        business_name = request.POST['business_name']
        contact_number = request.POST['contact_number']

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect('service_provider_register')

        user = User.objects.create_user(username=username, password=password)
        ServiceProvider.objects.create(
            user=user,
            business_name=business_name,
            contact_number=contact_number
        )
        messages.success(request, "Registration submitted. Await admin approval.")
        return redirect('login')

    return render(request, 'core/service_provider_register.html')

def choose_registration(request):
    return render(request, 'core/choose_registration.html')

@staff_member_required  # Only admins (is_staff=True) can access
def pending_providers(request):
    pending = ServiceProvider.objects.filter(approved=False, rejected=False)
    return render(request, 'core/pending_providers.html', {'pending': pending})

@login_required
def post_login_redirect(request):
    user = request.user

    print("User:", user.username)
    print("Is service provider:", hasattr(user, 'serviceprovider'))

    if hasattr(user, 'serviceprovider'):
        if not user.serviceprovider.approved:
            print("Provider not approved")
            return redirect('waiting_for_approval')

        print("Provider approved")
        return redirect('provider_dashboard')

    print("Not a service provider — redirecting to customer")
    return redirect('customer_dashboard')

@login_required
def waiting_for_approval(request):
    return render(request, 'core/waiting_for_approval.html')

@login_required
def provider_dashboard(request):
    return render(request, 'core/provider_dashboard.html')

@login_required
@user_passes_test(lambda u: u.is_superuser)
def approve_provider(request, provider_id):
    provider = get_object_or_404(ServiceProvider, id=provider_id)
    provider.approved = True
    provider.save()
    return redirect('pending_providers')

@login_required
@user_passes_test(lambda u: u.is_superuser)
def reject_provider(request, provider_id):
    provider = get_object_or_404(ServiceProvider, id=provider_id)
    provider.rejected = True
    provider.save()
    return redirect('pending_providers')

@login_required
def provider_add_bike(request):
    if not hasattr(request.user, 'serviceprovider') or not request.user.serviceprovider.approved:
        return redirect('login')  # Safety check

    provider = request.user.serviceprovider

    if request.method == 'POST':
        form = BikeForm(request.POST, request.FILES)
        if form.is_valid():
            bike = form.save(commit=False)
            bike.service_provider = provider  # Link to provider
            bike.save()
            messages.success(request, "Bike added successfully.")  # ✅ Success message
            return redirect('provider_add_bike')  # Or wherever you prefer
    else:
        form = BikeForm()

    return render(request, 'core/provider_add_bike.html', {'form': form})

@login_required
def provider_add_bike_station(request):
    if not hasattr(request.user, 'serviceprovider'):
        return redirect('login')

    if request.method == 'POST':
        form = BikeStationForm(request.POST, request.FILES)
        if form.is_valid():
            bike_station = form.save(commit=False)
            bike_station.service_provider = request.user.serviceprovider
            bike_station.save()
            messages.success(request, "Bike station added successfully.")  # ✅ success message
            return redirect('provider_add_bike_station')
    else:
        form = BikeStationForm()

    return render(request, 'core/provider_add_bike_station.html', {'form': form})

@login_required
def provider_add_car(request):
    if not hasattr(request.user, 'serviceprovider'):
        return redirect('login')

    if request.method == 'POST':
        form = CarForm(request.POST, request.FILES)
        if form.is_valid():
            car = form.save(commit=False)
            car.service_provider = request.user.serviceprovider
            car.save()
            messages.success(request, "Car added successfully.")  # ✅ Add success message
            return redirect('provider_add_car')  # Or another page like 'provider_manage_cars'
    else:
        form = CarForm()

    return render(request, 'core/provider_add_car.html', {'form': form})

@login_required
def provider_add_car_station(request):
    if not hasattr(request.user, 'serviceprovider'):
        return redirect('login')

    if request.method == 'POST':
        form = CarStationForm(request.POST, request.FILES)
        if form.is_valid():
            car_station = form.save(commit=False)
            car_station.service_provider = request.user.serviceprovider  # Link to provider
            car_station.save()
            messages.success(request, "Car station added successfully.")  # ✅ Success message
            return redirect('provider_add_car_station')
    else:
        form = CarStationForm()

    return render(request, 'core/provider_add_car_station.html', {'form': form})

@login_required
def provider_add_room(request):
    if not hasattr(request.user, 'serviceprovider'):
        return redirect('login')

    # Limit homestays to only those owned by the provider
    provider_homestays = request.user.serviceprovider.homestay_set.all()

    if request.method == 'POST':
        form = RoomForm(request.POST, request.FILES)
        form.fields['homestay'].queryset = provider_homestays  # Restrict homestay choices
        if form.is_valid():
            room = form.save()
            messages.success(request, "Room added successfully.")  # ✅ Success message
            return redirect('provider_add_room')
    else:
        form = RoomForm()
        form.fields['homestay'].queryset = provider_homestays

    return render(request, 'core/provider_add_room.html', {'form': form})

@login_required
def provider_add_homestay(request):
    if not hasattr(request.user, 'serviceprovider'):
        return redirect('login')

    if request.method == 'POST':
        form = HomestayForm(request.POST, request.FILES)
        if form.is_valid():
            homestay = form.save(commit=False)
            homestay.service_provider = request.user.serviceprovider
            homestay.save()
            messages.success(request, "Homestay added successfully.")  # ✅ Success message
            return redirect('provider_add_homestay')
    else:
        form = HomestayForm()

    return render(request, 'core/provider_add_homestay.html', {'form': form})

@login_required
def provider_manage_resource(request):
    provider = request.user.serviceprovider  # assuming you have a OneToOneField from User to ServiceProvider

    context = {
        'bikes': Bike.objects.filter(station__service_provider=provider),
        'bike_stations': BikeStation.objects.filter(service_provider=provider),
        'cars': Car.objects.filter(station__service_provider=provider),
        'car_stations': CarStation.objects.filter(service_provider=provider),
        'rooms': Room.objects.filter(homestay__service_provider=provider),
        'homestays': Homestay.objects.filter(service_provider=provider)
    }

    return render(request, 'core/provider_manage_resource.html', context)

@login_required
def provider_manage_booking(request):
    service_provider = request.user.serviceprovider  # FIXED

    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    date_filter = {}
    if start_date:
        date_filter['rent_date__gte'] = start_date
    if end_date:
        date_filter['return_date__lte'] = end_date

    homestay_date_filter = {}
    if start_date:
        homestay_date_filter['check_in__gte'] = start_date
    if end_date:
        homestay_date_filter['check_out__lte'] = end_date

    bike_bookings = BookingBike.objects.filter(
        bike__station__service_provider=service_provider,
        status='Completed',
        **date_filter
    )

    car_bookings = BookingCar.objects.filter(
        car__station__service_provider=service_provider,
        status='Completed',
        **date_filter
    )

    homestay_bookings = BookingHomestay.objects.filter(
        room__homestay__service_provider=service_provider,
        status='Completed',
        **homestay_date_filter
    )

    context = {
        'bike_bookings': bike_bookings,
        'car_bookings': car_bookings,
        'homestay_bookings': homestay_bookings,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'core/provider_manage_booking.html', context)

@login_required
def provider_feedback(request):
    provider = request.user.serviceprovider  # Get current provider

    # Get feedbacks linked to this provider's resources
    bike_feedbacks = UserFeedback.objects.filter(bike_station__service_provider=provider)
    car_feedbacks = UserFeedback.objects.filter(car_station__service_provider=provider)
    homestay_feedbacks = UserFeedback.objects.filter(homestay__service_provider=provider)

    # Combine all feedbacks into one list
    feedback_list = list(bike_feedbacks) + list(car_feedbacks) + list(homestay_feedbacks)

    return render(request, 'core/provider_feedback.html', {
        'feedback_list': feedback_list
    })

# ----------- BIKE ----------
@login_required
def provider_edit_bike(request, bike_id):
    bike = get_object_or_404(Bike, id=bike_id, service_provider=request.user)
    if request.method == 'POST':
        bike.name = request.POST.get('name')
        bike.type = request.POST.get('type')
        bike.daily_rent_price = request.POST.get('daily_rent_price')
        if 'image' in request.FILES:
            bike.image = request.FILES['image']
        bike.save()
        messages.success(request, 'Bike updated successfully.')
    return redirect('provider_manage_resource')

@login_required
def provider_delete_bike(request, bike_id):
    bike = get_object_or_404(Bike, id=bike_id, service_provider=request.user)
    bike.delete()
    messages.success(request, 'Bike deleted successfully.')
    return redirect('provider_manage_resource')

# ----------- BIKE STATION ----------
@login_required
def provider_edit_bike_station(request, station_id):
    station = get_object_or_404(BikeStation, id=station_id, service_provider=request.user)
    if request.method == 'POST':
        station.name = request.POST.get('name')
        station.longitude = request.POST.get('longitude')
        station.latitude = request.POST.get('latitude')
        station.location = request.POST.get('location')
        if 'image' in request.FILES:
            station.image = request.FILES['image']
        station.save()
        messages.success(request, 'Bike station updated successfully.')
    return redirect('provider_manage_resource')

@login_required
def provider_delete_bike_station(request, station_id):
    station = get_object_or_404(BikeStation, id=station_id, service_provider=request.user)
    station.delete()
    messages.success(request, 'Bike station deleted successfully.')
    return redirect('provider_manage_resource')

# ----------- CAR ----------
@login_required
def provider_edit_car(request, car_id):
    car = get_object_or_404(Car, id=car_id, service_provider=request.user)
    if request.method == 'POST':
        car.name = request.POST.get('name')
        car.type = request.POST.get('type')
        car.daily_rent_price = request.POST.get('daily_rent_price')
        if 'image' in request.FILES:
            car.image = request.FILES['image']
        car.save()
        messages.success(request, 'Car updated successfully.')
    return redirect('provider_manage_resource')

@login_required
def provider_delete_car(request, car_id):
    car = get_object_or_404(Car, id=car_id, service_provider=request.user)
    car.delete()
    messages.success(request, 'Car deleted successfully.')
    return redirect('provider_manage_resource')

# ----------- CAR STATION ----------
@login_required
def provider_edit_car_station(request, station_id):
    station = get_object_or_404(CarStation, id=station_id, service_provider=request.user)
    if request.method == 'POST':
        station.name = request.POST.get('name')
        station.longitude = request.POST.get('longitude')
        station.latitude = request.POST.get('latitude')
        station.location = request.POST.get('location')
        if 'image' in request.FILES:
            station.image = request.FILES['image']
        station.save()
        messages.success(request, 'Car station updated successfully.')
    return redirect('provider_manage_resource')

@login_required
def provider_delete_car_station(request, station_id):
    station = get_object_or_404(CarStation, id=station_id, service_provider=request.user)
    station.delete()
    messages.success(request, 'Car station deleted successfully.')
    return redirect('provider_manage_resource')

# ----------- ROOM ----------
@login_required
def provider_edit_room(request, room_id):
    room = get_object_or_404(Room, id=room_id, service_provider=request.user)
    if request.method == 'POST':
        room.name = request.POST.get('name')
        room.type = request.POST.get('type')
        room.night_rate = request.POST.get('night_rate')
        room.description = request.POST.get('description')
        if 'image' in request.FILES:
            room.image = request.FILES['image']
        room.save()
        messages.success(request, 'Room updated successfully.')
    return redirect('provider_manage_resource')

@login_required
def provider_delete_room(request, room_id):
    room = get_object_or_404(Room, id=room_id, service_provider=request.user)
    room.delete()
    messages.success(request, 'Room deleted successfully.')
    return redirect('provider_manage_resource')

# ----------- HOMESTAY ----------
@login_required
def provider_edit_homestay(request, homestay_id):
    homestay = get_object_or_404(Homestay, id=homestay_id, service_provider=request.user)
    if request.method == 'POST':
        homestay.name = request.POST.get('name')
        homestay.property_type = request.POST.get('type')
        homestay.location = request.POST.get('location')
        homestay.phone_number = request.POST.get('phone_number')
        if 'image' in request.FILES:
            homestay.image = request.FILES['image']
        homestay.save()
        messages.success(request, 'Homestay updated successfully.')
    return redirect('provider_manage_resource')

@login_required
def provider_delete_homestay(request, homestay_id):
    homestay = get_object_or_404(Homestay, id=homestay_id, service_provider=request.user)
    homestay.delete()
    messages.success(request, 'Homestay deleted successfully.')
    return redirect('provider_manage_resource')

@login_required
def edit_service_provider_profile(request):
    if not hasattr(request.user, 'serviceprovider'):
        return redirect('login')

    if request.method == 'POST':
        provider_form = ServiceProviderUpdateForm(request.POST, instance=request.user.serviceprovider)

        if provider_form.is_valid():
            provider_form.save()
            messages.success(request, "Your profile has been updated successfully!")  # 👈 message here
            return redirect('edit_service_provider_profile')  # 👈 stay on the same page to see message
    else:
        provider_form = ServiceProviderUpdateForm(instance=request.user.serviceprovider)

    return render(request, 'core/edit_service_provider_profile.html', {
        'provider_form': provider_form,
    })

@login_required
def edit_customer_profile(request):
    user = request.user
    try:
        profile = user.profile
    except Profile.DoesNotExist:
        profile = Profile.objects.create(user=user)

    if request.method == 'POST':
        form = CustomerUpdateForm(request.POST, instance=user, profile_instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated successfully!")
            return redirect('edit_customer_profile')
    else:
        form = CustomerUpdateForm(instance=user, profile_instance=profile)

    return render(request, 'core/edit_customer_profile.html', {
        'form': form,
    })

@login_required
def admin_reports(request):
    # Count completed bookings
    total_bike_bookings = BookingBike.objects.filter(status='Completed').count()
    total_car_bookings = BookingCar.objects.filter(status='Completed').count()
    total_homestay_bookings = BookingHomestay.objects.filter(status='Completed').count()

    total_bookings = total_bike_bookings + total_car_bookings + total_homestay_bookings

    # Get revenue from each type (fallback to Decimal('0') if None)
    bike_total = BookingBike.objects.filter(status='Completed').aggregate(Sum('rent_amount'))['rent_amount__sum'] or Decimal('0')
    car_total = BookingCar.objects.filter(status='Completed').aggregate(Sum('rent_amount'))['rent_amount__sum'] or Decimal('0')
    homestay_total = BookingHomestay.objects.filter(status='Completed').aggregate(Sum('rent_amount'))['rent_amount__sum'] or Decimal('0')

    total_revenue = bike_total + car_total + homestay_total
    platform_fees = total_revenue * Decimal('0.10')  # 10%

    feedback_count = UserFeedback.objects.count()

    context = {
        'total_bike_bookings': total_bike_bookings,
        'total_car_bookings': total_car_bookings,
        'total_homestay_bookings': total_homestay_bookings,
        'total_bookings': total_bookings,
        'total_revenue': total_revenue,
        'platform_fees': platform_fees,
        'feedback_count': feedback_count,
    }

    return render(request, 'core/admin_reports.html', context)