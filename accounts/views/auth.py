from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from accounts.serializers.auth import (
    LoginSerializer, RegisterSerializer, RequestOtpSerializer,
    SetPasswordSerializer, VerifyOtpSerializer,
)
from accounts.services.otp import OtpError, OtpRateLimitError, request_otp, verify_otp


class RegisterView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth-register"

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "حساب ساخته شد"}, status=status.HTTP_201_CREATED)


class RequestOtpView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth-request-otp"

    def post(self, request):
        serializer = RequestOtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ip = request.META.get("REMOTE_ADDR")
        try:
            request_otp(serializer.validated_data["phone_number"], ip_address=ip)
        except OtpRateLimitError as e:
            return Response({"detail": str(e), "code": "rate_limited"}, status=429)
        except OtpError as e:
            return Response(
                {"detail": str(e), "code": "sms_unavailable"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Response({"detail": "کد ارسال شد"})


class VerifyOtpView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth-verify"

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
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth-login"


class SetPasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SetPasswordSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["password"])
        request.user.save(update_fields=["password"])
        return Response({"detail": "Password set successfully."})


class RefreshView(TokenRefreshView):
    pass