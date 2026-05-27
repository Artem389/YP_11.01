from django.urls import path
from hotel_booking import views

urlpatterns = [
    path('', views.index, name='index'),
    path('hotels/', views.hotel_list, name='hotel_list'),
    path('hotels/<int:hotel_id>/rooms/', views.room_list, name='room_list'),
]