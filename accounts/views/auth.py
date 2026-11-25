from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from accounts.serializers.auth import (
    LoginSerializer, RegisterSerializer, RequestOtpSerializer, VerifyOtpSerializer,
)
from accounts.services.otp import OtpError, OtpRateLimitError, request_otp, verify_otp


class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "حساب ساخته شد"}, status=status.HTTP_201_CREATED)


class RequestOtpView(APIView):
    def post(self, request):
        serializer = RequestOtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ip = request.META.get("REMOTE_ADDR")
        try:
            request_otp(serializer.validated_data["phone_number"], ip_address=ip)
        except OtpRateLimitError as e:
            return Response({"detail": str(e), "code": "rate_limited"}, status=429)
        return Response({"detail": "کد ارسال شد"})


class VerifyOtpView(APIView):
    def post(self, request):
        serializer = VerifyOtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = verify_otp(
                serializer.validated_data["phone_number"],
                serializer.validated_data["code"],
            )
        except OtpError as e:
            return Response({"detail": str(e), "code": "otp_invalid"}, status=400)
        refresh = RefreshToken.for_user(user)
        return Response({"refresh": str(refresh), "access": str(refresh.access_token)})


class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer


class RefreshView(TokenRefreshView):
    pass