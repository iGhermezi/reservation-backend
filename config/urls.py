from django.contrib import admin
from django.urls import path

from appointments.views.cancel import CancelBookingView
from appointments.views.reschedule import RescheduleBookingView
from appointments.views.appointments import CreateBookingView
from appointments.views.timeline import AppointmentTimelineView
from scheduling.views.free_slots import FreeSlotsView
from accounts.views.auth import (
    LoginView, RefreshView, RegisterView, RequestOtpView, SetPasswordView,
    VerifyOtpView,
)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/free-slots/", FreeSlotsView.as_view(), name="free-slots"),
    path("api/v1/bookings/", CreateBookingView.as_view(), name="create-booking"),
    path("api/v1/auth/register/", RegisterView.as_view(), name="register"),
    path("api/v1/auth/login/", LoginView.as_view(), name="login"),
    path("api/v1/auth/request-otp/", RequestOtpView.as_view(), name="request-otp"),
    path("api/v1/auth/verify-otp/", VerifyOtpView.as_view(), name="verify-otp"),
    path("api/v1/auth/set-password/", SetPasswordView.as_view(), name="set-password"),
    path("api/v1/auth/refresh/", RefreshView.as_view(), name="token-refresh"),
    path("api/v1/bookings/<uuid:public_id>/cancel/",CancelBookingView.as_view(),name="cancel-booking",),
    path("api/v1/bookings/<uuid:public_id>/reschedule/",RescheduleBookingView.as_view(),name="reschedule-booking",),
    path(
        "api/v1/bookings/<uuid:public_id>/timeline/",
        AppointmentTimelineView.as_view(),
        name="appointment-timeline",
    ),
]
