from django.urls import path, include
from .views import (
    PaymentList,
    PaymentDetail,
    create_stripe_session,
    payment_success,
    payment_cancel,
)

urlpatterns = [
    path("", PaymentList.as_view(), name="payment_list"),
    path("<int:pk>/", PaymentDetail.as_view(), name="payment_detail"),
    path(
        "<int:pk>/create-stripe-session/",
        create_stripe_session,
        name="create_stripe_session",
    ),
    path("success/", payment_success, name="payment_success"),
    path("cancel/", payment_cancel, name="payment_cancel"),
]

app_name = "payments"
