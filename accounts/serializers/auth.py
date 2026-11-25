from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import User
from accounts.services.phone import normalize_phone


class RegisterSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField()

    class Meta:
        model = User
        fields = ["phone_number", "first_name", "last_name"]

    def to_internal_value(self, data):
        if "password" in data:
            raise serializers.ValidationError(
                {"password": "Password cannot be set during registration."}
            )
        return super().to_internal_value(data)

    def validate_phone_number(self, value):
        phone_number = normalize_phone(value)
        if User.objects.filter(phone_number=phone_number).exists():
            raise serializers.ValidationError("این شماره تلفن قبلا ثبت شده است")
        return phone_number

    def create(self, validated_data):
        user = User(**validated_data)
        user.set_unusable_password()
        user.save()
        return user


class RequestOtpSerializer(serializers.Serializer):
    phone_number = serializers.CharField()

    def validate_phone_number(self, value):
        return normalize_phone(value)


class VerifyOtpSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    code = serializers.CharField(max_length=6, min_length=6)

    def validate_phone_number(self, value):
        return normalize_phone(value)


class SetPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    password_confirm = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password_confirm": "Passwords do not match."}
            )
        try:
            validate_password(
                attrs["password"], user=self.context["request"].user
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(
                {"password": list(exc.messages)}
            ) from exc
        return attrs


class LoginSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        user = authenticate(
            request=self.context.get("request"),
            **{
                self.username_field: attrs[self.username_field],
                "password": attrs["password"],
            },
        )
        if user is None:
            raise AuthenticationFailed(
                self.error_messages["no_active_account"],
                code="no_active_account",
            )
        if user.account_state != User.AccountState.VERIFIED:
            raise AuthenticationFailed(
                self.error_messages["no_active_account"],
                code="no_active_account",
            )

        refresh = RefreshToken.for_user(user)
        return {"refresh": str(refresh), "access": str(refresh.access_token)}