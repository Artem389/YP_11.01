from django.shortcuts import render
from .models import Hotel, Room

def index(request):
    return render(request, 'hotel_booking/index.html')

def hotel_list(request):
    hotels = Hotel.objects.all()
    return render(request, 'hotel_booking/hotel_list.html', {'hotels': hotels})

def room_list(request, hotel_id):
    hotel = Hotel.objects.get(id=hotel_id)
    rooms = Room.objects.filter(hotel=hotel, is_available=True)
    return render(request, 'hotel_booking/room_list.html', {'hotel': hotel, 'rooms': rooms})