from django.contrib import admin
from django.urls import path

from appointments.views.appointments import CreateBookingView
from scheduling.views.free_slots import FreeSlotsView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/free-slots/", FreeSlotsView.as_view(), name="free-slots"),
    path("api/v1/bookings/", CreateBookingView.as_view(), name="create-booking"),
]
